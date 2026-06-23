# All Cars Direct — production container for Fly.io / Render / Railway.
# Streamlit binds to 0.0.0.0:8080; SQLite + favicons + brand logos all live
# inside the image except the listings DB, which is on a mounted volume at
# /data so it survives restarts.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    ACD_DATA_DIR=/data

WORKDIR /app

# Install build deps for lxml first, then drop them to keep the image lean.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8080

# Fly mounts the volume at /data before the container starts, so no mkdir
# needed. Use exec-form CMD so signals reach Streamlit cleanly.
CMD ["streamlit", "run", "streamlit_app.py"]
