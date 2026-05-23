import json
import logging
import os
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

import cv2
import numpy as np
import redis
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, generate_latest
from ultralytics import YOLO

try:
    import easyocr
except Exception:  # pragma: no cover - optional dependency may be unavailable during bootstrap
    easyocr = None

try:
    import torch
except Exception:  # pragma: no cover - optional dependency may be unavailable during bootstrap
    torch = None


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sentinelos.perception")

tracer_provider = TracerProvider()
trace.set_tracer_provider(tracer_provider)
ot_tracer = trace.get_tracer("sentinelos.perception")
propagator = TraceContextTextMapPropagator()

registry = CollectorRegistry()
gpu_vram_used = Gauge("sita_gpu_vram_used_bytes", "Total VRAM used by GPU", registry=registry)
gpu_temp = Gauge("sita_gpu_temperature_celsius", "GPU core temperature", registry=registry)
gpu_saturation = Gauge("sita_gpu_saturation_percent", "GPU core utilization percentage", registry=registry)
gpu_metrics_available = Gauge("sita_gpu_metrics_available", "1 if GPU telemetry is available", registry=registry)
inference_latency = Gauge("sita_inference_latency_ms", "Model inference latency", ["backend"], registry=registry)
ocr_latency = Gauge("sita_ocr_latency_ms", "OCR latency", registry=registry)
active_streams = Gauge("sita_active_streams", "Active perception streams", registry=registry)
processed_frames = Counter("sita_processed_frames_total", "Frames processed by perception runtime", registry=registry)
emitted_events = Counter("sita_emitted_events_total", "Detection events emitted to Redis", registry=registry)
successful_ocr_reads = Counter("sita_ocr_success_total", "Successful OCR stabilizations", registry=registry)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
STREAM_NAME = os.getenv("DETECTIONS_STREAM", "sita:stream:detections")
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8s.pt")
YOLO_IMAGE_SIZE = int(os.getenv("YOLO_IMAGE_SIZE", 960))
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", 0.35))
YOLO_IOU = float(os.getenv("YOLO_IOU", 0.45))
TRACK_CLASSES = [2, 3, 5, 7]
OCR_ENABLED = os.getenv("OCR_ENABLED", "1") == "1"
FRAME_SKIP_CPU = max(1, int(os.getenv("FRAME_SKIP_CPU", 3)))
FRAME_SKIP_GPU = max(1, int(os.getenv("FRAME_SKIP_GPU", 1)))
EMIT_EVERY_N_FRAMES = max(1, int(os.getenv("EMIT_EVERY_N_FRAMES", 8)))
OCR_EVERY_N_FRAMES = max(1, int(os.getenv("OCR_EVERY_N_FRAMES", 4)))
COLOR_REFRESH_EVERY_N_FRAMES = max(1, int(os.getenv("COLOR_REFRESH_EVERY_N_FRAMES", 6)))
PLATE_CONFIDENCE_THRESHOLD = float(os.getenv("PLATE_CONFIDENCE_THRESHOLD", 0.35))
SPEED_SMOOTHING = float(os.getenv("SPEED_SMOOTHING", 0.7))
OCR_VOTE_WINDOW = max(3, int(os.getenv("OCR_VOTE_WINDOW", 6)))
COLOR_VOTE_WINDOW = max(3, int(os.getenv("COLOR_VOTE_WINDOW", 8)))
MAX_CPU_THREADS = max(1, int(os.getenv("MAX_CPU_THREADS", 4)))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=3.0)
app = FastAPI(title="SentinelOS Real Perception Service")


def choose_device() -> str:
    if torch and torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def normalize_text(text: str) -> str:
    return "".join(ch for ch in text.upper() if ch.isalnum())


def compute_iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    intersection = inter_w * inter_h
    if intersection <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - intersection
    return float(intersection / union) if union > 0 else 0.0


def vehicle_type_from_class(class_id: int) -> str:
    return {
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
    }.get(class_id, "unknown")


def compute_centroid(box: np.ndarray) -> Tuple[float, float]:
    x1, y1, x2, y2 = box
    return float((x1 + x2) / 2.0), float((y1 + y2) / 2.0)


class OCRProcessor:
    def __init__(self, enabled: bool):
        self.enabled = enabled and easyocr is not None
        self.reader = None
        if self.enabled:
            use_gpu = bool(torch and torch.cuda.is_available())
            logger.info("Initializing EasyOCR. gpu=%s", use_gpu)
            self.reader = easyocr.Reader(["en"], gpu=use_gpu)
        elif enabled:
            logger.warning("OCR requested but EasyOCR is unavailable; OCR disabled.")

    def detect_plate(self, vehicle_crop: np.ndarray, frame_width: int) -> Tuple[str, float]:
        if not self.reader or vehicle_crop.size == 0:
            return "", 0.0

        started = time.time()
        h, w, _ = vehicle_crop.shape
        if w < max(36, frame_width * 0.045):
            return "", 0.0

        y1, y2 = int(h * 0.38), int(h * 0.86)
        x1, x2 = int(w * 0.05), int(w * 0.95)
        plate_crop = vehicle_crop[y1:y2, x1:x2]
        if plate_crop.size == 0:
            return "", 0.0

        pad = max(4, int(frame_width * 0.006))
        plate_crop = cv2.copyMakeBorder(plate_crop, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 50, 50)

        sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(gray, -1, sharpen_kernel)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharpened)
        upscaled = cv2.resize(enhanced, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        _, otsu = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(
            upscaled,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        morph = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)

        candidates = [upscaled, otsu, adaptive, morph]
        rectified = self._rectify_candidate(plate_crop)
        if rectified is not None:
            rectified_gray = cv2.cvtColor(rectified, cv2.COLOR_BGR2GRAY)
            rectified_gray = clahe.apply(rectified_gray)
            rectified_gray = cv2.resize(rectified_gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            candidates.append(rectified_gray)
        best_text, best_score = "", 0.0
        allowlist = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for candidate in candidates:
            try:
                results = self.reader.readtext(candidate, allowlist=allowlist, detail=1)
            except Exception as exc:
                logger.debug("OCR candidate failed: %s", exc)
                continue

            for _, text, score in results:
                clean = normalize_text(text)
                if len(clean) < 4:
                    continue
                if score > best_score:
                    best_text = clean
                    best_score = float(score)

        ocr_latency.set((time.time() - started) * 1000.0)
        return best_text, best_score

    def _rectify_candidate(self, plate_crop: np.ndarray) -> Optional[np.ndarray]:
        try:
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(gray, 80, 200)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
            for contour in contours:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
                if len(approx) != 4:
                    continue
                points = approx.reshape(4, 2).astype(np.float32)
                ordered = self._order_points(points)
                width = int(max(np.linalg.norm(ordered[0] - ordered[1]), np.linalg.norm(ordered[2] - ordered[3])))
                height = int(max(np.linalg.norm(ordered[0] - ordered[3]), np.linalg.norm(ordered[1] - ordered[2])))
                if width < 40 or height < 12:
                    continue
                destination = np.array(
                    [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
                    dtype=np.float32,
                )
                matrix = cv2.getPerspectiveTransform(ordered, destination)
                return cv2.warpPerspective(plate_crop, matrix, (width, height))
        except Exception as exc:
            logger.debug("Plate rectification failed: %s", exc)
        return None

    @staticmethod
    def _order_points(points: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype=np.float32)
        sums = points.sum(axis=1)
        rect[0] = points[np.argmin(sums)]
        rect[2] = points[np.argmax(sums)]
        diffs = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diffs)]
        rect[3] = points[np.argmax(diffs)]
        return rect


class ColorAnalyzer:
    COLOR_RANGES = {
        "black": [((0, 0, 0), (180, 255, 55))],
        "white": [((0, 0, 185), (180, 55, 255))],
        "gray": [((0, 0, 56), (180, 45, 184))],
        "silver": [((0, 0, 120), (180, 35, 215))],
        "red": [((0, 70, 50), (10, 255, 255)), ((170, 70, 50), (180, 255, 255))],
        "blue": [((95, 70, 40), (135, 255, 255))],
        "green": [((36, 45, 35), (89, 255, 255))],
        "yellow": [((18, 60, 90), (36, 255, 255))],
        "orange": [((9, 80, 80), (22, 255, 255))],
        "brown": [((5, 55, 20), (22, 255, 150))],
    }

    def detect(self, crop: np.ndarray) -> Tuple[str, float]:
        if crop.size == 0:
            return "unknown", 0.0

        h, w, _ = crop.shape
        regions = [
            crop[int(h * 0.15):int(h * 0.55), int(w * 0.15):int(w * 0.85)],
            crop[int(h * 0.25):int(h * 0.75), int(w * 0.20):int(w * 0.80)],
            crop[int(h * 0.10):int(h * 0.45), int(w * 0.25):int(w * 0.75)],
        ]

        scores = {name: 0.0 for name in self.COLOR_RANGES}
        total_weight = 0.0

        for idx, region in enumerate(regions):
            if region.size == 0:
                continue
            weight = 1.0 if idx == 0 else 0.7
            total_weight += weight

            lab = cv2.cvtColor(region, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l_norm = cv2.normalize(l, None, 40, 220, cv2.NORM_MINMAX)
            normalized = cv2.merge((l_norm, a, b))
            region_bgr = cv2.cvtColor(normalized, cv2.COLOR_LAB2BGR)
            blurred = cv2.GaussianBlur(region_bgr, (5, 5), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            pixels = hsv.shape[0] * hsv.shape[1]
            if pixels <= 0:
                continue

            for color_name, ranges in self.COLOR_RANGES.items():
                coverage = 0
                for low, high in ranges:
                    mask = cv2.inRange(hsv, np.array(low), np.array(high))
                    coverage += cv2.countNonZero(mask)
                scores[color_name] += weight * (coverage / pixels)

        if total_weight == 0:
            return "unknown", 0.0

        best_color, best_score = max(scores.items(), key=lambda item: item[1])
        confidence = min(1.0, best_score / max(total_weight, 1e-6))

        if confidence < 0.18:
            return "unknown", confidence
        if best_color == "gray" and scores["silver"] > scores["gray"] * 0.9:
            best_color = "silver"
            confidence = min(1.0, scores["silver"] / total_weight)

        return best_color, confidence


@dataclass
class TrackState:
    track_id: int
    class_id: int
    frames_seen: int = 0
    last_seen_frame: int = 0
    last_bbox: Optional[np.ndarray] = None
    last_centroid: Optional[Tuple[float, float]] = None
    speed_px_s: float = 0.0
    vehicle_color: str = "unknown"
    color_confidence: float = 0.0
    plate_text: str = ""
    plate_confidence: float = 0.0
    detection_confidence: float = 0.0
    last_emitted_frame: int = 0
    stable_frames: int = 0
    last_event_hash: str = ""
    plate_history: Deque[Tuple[str, float]] = field(default_factory=lambda: deque(maxlen=OCR_VOTE_WINDOW))
    color_history: Deque[Tuple[str, float]] = field(default_factory=lambda: deque(maxlen=COLOR_VOTE_WINDOW))
    metadata: Dict[str, str] = field(default_factory=dict)


class VisionPipeline:
    def __init__(self):
        self.device = choose_device()
        if torch and self.device == "cpu":
            try:
                torch.set_num_threads(MAX_CPU_THREADS)
                torch.set_num_interop_threads(1)
            except Exception as exc:
                logger.debug("Unable to tune torch CPU threads: %s", exc)
        self.model = YOLO(YOLO_MODEL_PATH)
        self.color_analyzer = ColorAnalyzer()
        self.ocr = OCRProcessor(OCR_ENABLED)
        self.frame_skip = FRAME_SKIP_GPU if self.device.startswith("cuda") else FRAME_SKIP_CPU
        logger.info(
            "Perception pipeline ready. device=%s model=%s frame_skip=%s",
            self.device,
            YOLO_MODEL_PATH,
            self.frame_skip,
        )

    def infer(self, frame: np.ndarray) -> List[dict]:
        start_time = time.time()
        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            classes=TRACK_CLASSES,
            conf=YOLO_CONFIDENCE,
            iou=YOLO_IOU,
            imgsz=YOLO_IMAGE_SIZE,
            verbose=False,
            device=self.device,
        )
        inference_latency.labels(backend=f"ultralytics_{self.device}").set((time.time() - start_time) * 1000.0)

        detections: List[dict] = []
        for result in results:
            if result.boxes is None or result.boxes.id is None:
                continue

            boxes = result.boxes.xyxy.cpu().numpy()
            track_ids = result.boxes.id.int().cpu().tolist()
            class_ids = result.boxes.cls.int().cpu().tolist()
            confidences = result.boxes.conf.cpu().tolist()

            for bbox, track_id, class_id, confidence in zip(boxes, track_ids, class_ids, confidences):
                detections.append(
                    {
                        "bbox": bbox.astype(float),
                        "track_id": int(track_id),
                        "class_id": int(class_id),
                        "confidence": float(confidence),
                    }
                )

        return detections


pipeline = VisionPipeline()


class StreamProcessorThread(threading.Thread):
    def __init__(self, camera_id: str, stream_source: str):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.stream_source = stream_source
        self.running = False
        self.track_states: Dict[int, TrackState] = {}

    def run(self):
        self.running = True
        cap = self._open_capture()
        frame_idx = 0
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if fps and fps > 0 else 25.0
        active_streams.inc()

        while self.running:
            if not cap.isOpened():
                time.sleep(2.0)
                cap = self._open_capture()
                continue

            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(1.0)
                cap.release()
                cap = self._open_capture()
                continue

            frame_idx += 1
            processed_frames.inc()

            if frame_idx % pipeline.frame_skip != 0:
                self._update_gpu_metrics()
                continue

            try:
                with ot_tracer.start_as_current_span("process_frame") as span:
                    span.set_attribute("camera_id", self.camera_id)
                    span.set_attribute("frame_index", frame_idx)
                    detections = pipeline.infer(frame)
                    carrier = {}
                    propagator.inject(carrier)
                    self._update_tracks_and_publish(frame, frame_idx, fps, detections, carrier.get("traceparent", ""))
            except Exception as exc:
                logger.exception("Frame processing failed for camera=%s frame=%s: %s", self.camera_id, frame_idx, exc)

            self._expire_stale_tracks(frame_idx)
            self._update_gpu_metrics()

        active_streams.dec()
        cap.release()

    def _open_capture(self) -> cv2.VideoCapture:
        if self.stream_source.startswith("gst:"):
            return cv2.VideoCapture(self.stream_source[4:], cv2.CAP_GSTREAMER)
        if self.stream_source.startswith(("rtsp://", "http://", "https://")):
            os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp|max_delay;500000")
            return cv2.VideoCapture(self.stream_source, cv2.CAP_FFMPEG)
        return cv2.VideoCapture(self.stream_source)

    def _update_tracks_and_publish(
        self,
        frame: np.ndarray,
        frame_idx: int,
        fps: float,
        detections: List[dict],
        traceparent: str,
    ) -> None:
        seen_ids = set()
        frame_height, frame_width = frame.shape[:2]

        for det in detections:
            track_id = det["track_id"]
            class_id = det["class_id"]
            bbox = det["bbox"]
            confidence = det["confidence"]
            seen_ids.add(track_id)

            state = self.track_states.get(track_id)
            if state is None:
                state = TrackState(track_id=track_id, class_id=class_id)
                self.track_states[track_id] = state

            state.frames_seen += 1
            state.last_seen_frame = frame_idx
            state.detection_confidence = confidence

            centroid = compute_centroid(bbox)
            if state.last_bbox is not None and compute_iou(state.last_bbox, bbox) > 0.4:
                state.stable_frames += 1
            else:
                state.stable_frames = 1

            if state.last_centroid is not None:
                pixel_distance = float(np.linalg.norm(np.array(centroid) - np.array(state.last_centroid)))
                instant_speed = pixel_distance * fps / max(pipeline.frame_skip, 1)
                state.speed_px_s = (SPEED_SMOOTHING * state.speed_px_s) + ((1.0 - SPEED_SMOOTHING) * instant_speed)

            state.last_centroid = centroid
            state.last_bbox = bbox

            x1, y1, x2, y2 = bbox.astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame_width, x2), min(frame_height, y2)
            crop = frame[y1:y2, x1:x2]

            if crop.size > 0 and (state.frames_seen == 1 or frame_idx % COLOR_REFRESH_EVERY_N_FRAMES == 0):
                color, color_conf = pipeline.color_analyzer.detect(crop)
                if color != "unknown":
                    state.color_history.append((color, color_conf))
                    stable_color, stable_conf = self._stabilize_color(state)
                    if stable_conf >= state.color_confidence or state.vehicle_color == "unknown":
                        state.vehicle_color = stable_color
                        state.color_confidence = stable_conf

            if crop.size > 0 and OCR_ENABLED and frame_idx % OCR_EVERY_N_FRAMES == 0 and state.stable_frames >= 2:
                plate_text, plate_conf = pipeline.ocr.detect_plate(crop, frame_width)
                if plate_text and plate_conf >= PLATE_CONFIDENCE_THRESHOLD:
                    state.plate_history.append((plate_text, plate_conf))
                    stable_plate, stable_conf = self._stabilize_plate(state)
                    if stable_conf >= state.plate_confidence:
                        if stable_plate != state.plate_text:
                            successful_ocr_reads.inc()
                        state.plate_text = stable_plate
                        state.plate_confidence = stable_conf

            self._emit_detection_event(state, frame_idx, traceparent)

        for track_id, state in list(self.track_states.items()):
            if track_id not in seen_ids:
                continue

    def _emit_detection_event(self, state: TrackState, frame_idx: int, traceparent: str) -> None:
        should_emit = (
            state.frames_seen == 1
            or frame_idx - state.last_emitted_frame >= EMIT_EVERY_N_FRAMES
            or (state.plate_text and state.last_event_hash != state.plate_text)
        )
        if not should_emit or state.last_bbox is None:
            return

        bbox = [round(float(value), 2) for value in state.last_bbox.tolist()]
        event_payload = {
            "camera_id": self.camera_id,
            "frame_index": str(frame_idx),
            "timestamp": f"{time.time():.6f}",
            "class_id": str(state.class_id),
            "vehicle_type": vehicle_type_from_class(state.class_id),
            "confidence": f"{state.detection_confidence:.4f}",
            "bbox": json.dumps(bbox),
            "track_id": str(state.track_id),
            "traceparent": traceparent,
            "color": state.vehicle_color,
            "color_confidence": f"{state.color_confidence:.4f}",
            "license_plate": state.plate_text,
            "ocr_confidence": f"{state.plate_confidence:.4f}",
            "speed_px_per_sec": f"{state.speed_px_s:.4f}",
        }

        try:
            redis_client.xadd(STREAM_NAME, event_payload, maxlen=100000, approximate=True)
            state.last_emitted_frame = frame_idx
            state.last_event_hash = state.plate_text or f"{state.track_id}:{frame_idx}"
            emitted_events.inc()
        except Exception as exc:
            logger.error("Failed to publish detection event for track=%s: %s", state.track_id, exc)

    def _expire_stale_tracks(self, frame_idx: int) -> None:
        for track_id, state in list(self.track_states.items()):
            if frame_idx - state.last_seen_frame > 120:
                self.track_states.pop(track_id, None)

    def _stabilize_plate(self, state: TrackState) -> Tuple[str, float]:
        vote_weights: Dict[str, float] = {}
        best_confidence: Dict[str, float] = {}
        for text, confidence in state.plate_history:
            vote_weights[text] = vote_weights.get(text, 0.0) + confidence
            best_confidence[text] = max(best_confidence.get(text, 0.0), confidence)

        if not vote_weights:
            return "", 0.0

        best_text = max(vote_weights.items(), key=lambda item: (item[1], best_confidence.get(item[0], 0.0), len(item[0])))[0]
        aggregated_conf = min(1.0, (vote_weights[best_text] / max(1, len(state.plate_history))) * 1.25)
        return best_text, max(best_confidence.get(best_text, 0.0), aggregated_conf)

    def _stabilize_color(self, state: TrackState) -> Tuple[str, float]:
        vote_weights: Dict[str, float] = {}
        best_confidence: Dict[str, float] = {}
        for color, confidence in state.color_history:
            vote_weights[color] = vote_weights.get(color, 0.0) + confidence
            best_confidence[color] = max(best_confidence.get(color, 0.0), confidence)

        if not vote_weights:
            return "unknown", 0.0

        best_color = max(vote_weights.items(), key=lambda item: (item[1], best_confidence.get(item[0], 0.0)))[0]
        aggregated_conf = min(1.0, vote_weights[best_color] / max(1, len(state.color_history)))
        return best_color, max(best_confidence.get(best_color, 0.0), aggregated_conf)

    def _update_gpu_metrics(self) -> None:
        if not pipeline.device.startswith("cuda"):
            gpu_metrics_available.set(0)
            return

        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,temperature.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
            sat, temp, vram = map(float, output.split(", "))
            gpu_saturation.set(sat)
            gpu_temp.set(temp)
            gpu_vram_used.set(vram * 1024 * 1024)
            gpu_metrics_available.set(1)
        except Exception as exc:
            logger.debug("GPU metrics unavailable: %s", exc)
            gpu_metrics_available.set(0)

    def stop(self):
        self.running = False


active_workers: Dict[str, StreamProcessorThread] = {}
workers_lock = threading.Lock()


@app.post("/streams/start")
def start_stream(camera_id: str, source: str):
    with workers_lock:
        if camera_id in active_workers:
            raise HTTPException(status_code=409, detail="Stream already active")

        worker = StreamProcessorThread(camera_id, source)
        active_workers[camera_id] = worker
        worker.start()
    return {"status": "success", "camera_id": camera_id, "source": source, "device": pipeline.device}


@app.post("/streams/stop")
def stop_stream(camera_id: str):
    with workers_lock:
        worker = active_workers.pop(camera_id, None)
    if worker is None:
        raise HTTPException(status_code=404, detail="Stream not running")

    worker.stop()
    worker.join(timeout=5.0)
    return {"status": "success", "camera_id": camera_id}


@app.get("/metrics")
def get_metrics():
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    with workers_lock:
        workers = list(active_workers.keys())
    return {
        "status": "healthy",
        "device": pipeline.device,
        "ocr_enabled": pipeline.ocr.reader is not None,
        "active_workers": workers,
        "frame_skip": pipeline.frame_skip,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
