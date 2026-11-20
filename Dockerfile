FROM python:3.11-slim

WORKDIR /app
# CPU-only torch keeps the image around 2 GB smaller; drop the index URL for a CUDA base image
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Models download from Hugging Face on first start; mount a volume here to keep them between runs
ENV HF_HOME=/models \
    BLIND_READER_HOST=0.0.0.0
EXPOSE 8000
CMD ["python", "app.py"]
