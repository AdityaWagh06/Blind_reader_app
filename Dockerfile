FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
# CPU-only torch keeps the image around 2 GB smaller; drop the index URL for a CUDA base image
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

# Run as an unprivileged user; models download from Hugging Face on first start into /models,
# so mount a volume there to keep them between runs
RUN useradd --create-home --uid 1000 app && mkdir /models && chown app /models
COPY --chown=app . .
USER app
ENV HF_HOME=/models \
    BLIND_READER_HOST=0.0.0.0

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/status', timeout=4)"
CMD ["python", "app.py"]
