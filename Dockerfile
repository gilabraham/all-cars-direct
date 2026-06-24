# All Cars Direct — production container for Fly.io.
# Streamlit binds to 0.0.0.0:8080; SQLite + favicons + brand logos all live
# inside the image except the listings DB, which is on a mounted volume at
# /data so it survives restarts. Bundled headless Chromium (Playwright) so
# admin can trigger deep PDP scrapes from the live site to capture
# JavaScript-rendered lease/finance pricing.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    ACD_DATA_DIR=/data \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Build deps for lxml + everything Chromium needs at runtime (libgbm, libnss,
# libatk, audio, fonts, etc.) — the full list comes from Playwright's
# `install-deps` script. We keep the deps after install because Chromium
# needs them to run; we only strip the *build* toolchain (gcc/etc.).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Download Chromium (~150 MB) and install its OS-level shared libraries.
# --with-deps reinstalls apt so we re-run rm at the end.
RUN playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# Drop build toolchain to slim the final image.
RUN apt-get update \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8080

# Fly mounts the volume at /data before the container starts. Exec-form CMD
# so signals reach Streamlit cleanly.
CMD ["streamlit", "run", "streamlit_app.py"]
