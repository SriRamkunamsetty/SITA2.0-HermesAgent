# SITA Project Structure Analysis 📂

This document categorizes the files in the SITA (Smart Intelligent Traffic Analyzer) project to help you identify which files are essential for operation and which are auxiliary or development-related.

## 🚀 Core Essential Files (Critical)
These files form the "Brain" and "Body" of SITA. If you are importing the project to improve it, **these are mandatory**.

### Backend & AI Logic
- **[app.py](file:///d:/SITA/SITA/app.py)**: The main entry point for the Flask server. Handles API routing, job management, and authentication hooks.
- **[processor.py](file:///d:/SITA/SITA/processor.py)**: The AI Vision Pipeline. Contains the `SITAProcessor` class which handles YOLO detection, EasyOCR, and tracking logic. **Crucial for accuracy improvements.**
- **[database.py](file:///d:/SITA/SITA/database.py)**: Manages SQLite interactions, user roles (RBAC), organization silos, and job persistence.
- **[firebase_utils.py](file:///d:/SITA/SITA/firebase_utils.py)**: Cloud synchronization logic for logs and user data.
- **[yolov8s.pt](file:///d:/SITA/SITA/yolov8s.pt)**: The pre-trained neural network weights used by YOLO for vehicle detection.

### Frontend (User Interface)
- **[sita-web/src/](file:///d:/SITA/SITA/sita-web/src/)**: Contains all React components, pages, and styles.
- **[sita-web/package.json](file:///d:/SITA/SITA/sita-web/package.json)**: Defines frontend dependencies.
- **[sita-web/vite.config.js](file:///d:/SITA/SITA/sita-web/vite.config.js)**: Configuration for the Vite build tool.

### Environment & Meta
- **[.env](file:///d:/SITA/SITA/.env)**: Contains sensitive credentials (API keys, Email passwords). **Must be kept secure.**
- **[requirements.txt](file:///d:/SITA/SITA/requirements.txt)**: Lists all Python libraries needed for the backend.

---

## 🛠 Auxiliary & Development Files (Optional)
These files are useful for testing, verification, or deployment but aren't strictly required for the core app to function.

### Test & Verification Scripts
- `day1_*` to `day6_*`: Development-stage scripts and tutorials.
- `verify_*`: Scripts used to check if specific components (Firebase, database, OCR) are working correctly.
- `test_*`: Unit tests for OTP, codecs, and OCR.
- `reproduce_*`: Scripts to recreate specific issues for debugging.

### Logs & Temporary Data
- `*.log`: System logs (server.log, debug_viva.log).
- `*.csv`: Processed results from past runs.
- `uploads/` & `downloads/`: Temporary storage for videos and reports.
- `sita.db`: The local SQLite database file (contains your specific user/job data).

### Deployment Configuration
- `Procfile`, `render.yaml`, `netlify.toml`, `vercel.json`: Configuration for various cloud hosting platforms.

---

## 📈 Roadmap for Improvement

### To Improve Accuracy:
1.  **Modify [processor.py](file:///d:/SITA/SITA/processor.py)**:
    - Tune the `detect_color` HSV ranges for better color recognition under different lighting.
    - Enhance the `detect_plate` image preprocessing (sharpening, thresholding) to help EasyOCR.
    - Increase `imgsz` in the `model.track` call for higher resolution detection.
2.  **Upgrade the Model**:
    - Replace `yolov8s.pt` with a larger model like `yolov8x.pt` or the newer `yolov11` series for better detection of small or distant vehicles.

### To Add Features:
1.  **Expand [database.py](file:///d:/SITA/SITA/database.py)**: Update the schema to track new metrics (e.g., vehicle speed, lane violations).
2.  **Update [app.py](file:///d:/SITA/SITA/app.py)**: Add new REST API endpoints to serve the new data to the frontend.
3.  **Enhance [sita-web/src/](file:///d:/SITA/SITA/sita-web/src/)**: Build new dashboard widgets or data visualization pages using the new API data.
