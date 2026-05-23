ARG BASE_IMAGE=python:3.10-slim
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_REQUIRE_HASHES=0
ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org pypi.python.org download.pytorch.org download-r2.pytorch.org"

RUN apt-get update && apt-get install -y \
    python3-dev \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    gstreamer1.0-tools \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir \
    --trusted-host download.pytorch.org \
    --trusted-host download-r2.pytorch.org \
    "https://download.pytorch.org/whl/cpu/torch-2.5.1%2Bcpu-cp310-cp310-linux_x86_64.whl" \
    "https://download.pytorch.org/whl/cpu/torchvision-0.20.1%2Bcpu-cp310-cp310-linux_x86_64.whl" \
    && pip install --no-cache-dir \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    -r requirements.txt

ENV EASYOCR_MODULE_PATH=/opt/easyocr
RUN mkdir -p /opt/easyocr/model \
    && curl -Lk "https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip" -o /tmp/craft_mlt_25k.zip \
    && curl -Lk "https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip" -o /tmp/english_g2.zip \
    && python -c "from zipfile import ZipFile; pairs=[('/tmp/craft_mlt_25k.zip','craft_mlt_25k.pth'),('/tmp/english_g2.zip','english_g2.pth')]; [ZipFile(src).extract(name, '/opt/easyocr/model') for src, name in pairs]" \
    && rm -f /tmp/craft_mlt_25k.zip /tmp/english_g2.zip

COPY . .

EXPOSE 8002

CMD ["python", "src/main.py"]
