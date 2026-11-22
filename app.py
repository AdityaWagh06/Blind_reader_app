"""
Blind Reader Assistant web server.

    python app.py            ->  http://127.0.0.1:8000

Serves the website in static/ and a small JSON API:
    GET  /api/status     models loaded yet?
    POST /api/describe   image upload -> summary, detailed description, text found, readability warning
    GET  /api/eval       evaluation results produced by training/evaluate.py
"""
import io
import json
import logging
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError

from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("blind_reader")

ROOT = Path(__file__).parent
RETAKE_TIP = ("Try again holding the camera steady, about 30 centimetres away, with more light. "
              "Text is not read out from unclear photos, because it could be wrong.")

@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=load_models, daemon=True).start()
    yield


app = FastAPI(title=Config.APP_NAME, version=Config.APP_VERSION, lifespan=lifespan)

# The site loads nothing from other origins; inline style attributes are used by the result charts.
# /docs is excluded because FastAPI's Swagger page loads its scripts from a CDN.
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; "
                               "frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(self), microphone=(), geolocation=()",
}


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith(("/docs", "/redoc")):
        response.headers.update(SECURITY_HEADERS)
    return response


models = {}
model_error = None
model_lock = threading.Lock()  # one image at a time: the models are large and share the CPU/GPU


def load_models():
    global model_error
    try:
        # Imported here so the website comes up instantly while torch and the models load
        from utils.image_captioning import ImageCaptioner
        from utils.scene_describer import SceneDescriber
        models["captioner"] = ImageCaptioner(Config.BLIP_MODEL)
        models["describer"] = SceneDescriber(Config.FLORENCE_MODEL)
        logger.info("Models ready")
    except Exception as e:  # surfaced through /api/status instead of crashing the server
        logger.exception("Model loading failed")
        model_error = str(e)


@app.get("/api/status")
def status():
    return {"ready": len(models) == 2, "error": model_error,
            "models": {"summary": Config.BLIP_MODEL, "description": Config.FLORENCE_MODEL}}


def build_speech(summary_unclear, description, text_lines):
    parts = []
    if summary_unclear:
        parts.append("This photo looks blurry or unclear, so the description may not be accurate. " + RETAKE_TIP)
    parts.append(description)
    if text_lines:
        parts.append("The text in the image reads: " + ". ".join(text_lines) + ".")
    return " ".join(parts)


@app.post("/api/describe")
def describe(image: UploadFile = File(...)):
    data = image.file.read(Config.MAX_FILE_SIZE_MB * 1024 * 1024 + 1)
    if len(data) > Config.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"Image is larger than {Config.MAX_FILE_SIZE_MB} MB.")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        # Phone cameras store rotation in EXIF; without this a portrait label is read sideways
        img = ImageOps.exif_transpose(img).convert("RGB")
    except Image.DecompressionBombError:
        # a small file can still decode to billions of pixels and exhaust memory
        raise HTTPException(413, "This image has too many pixels. Please use a normal photo.")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(415, "That file is not an image we can read. Please use a JPG, PNG or WebP photo.")
    if model_error:
        raise HTTPException(500, f"The AI models failed to load: {model_error}")
    if len(models) < 2:
        raise HTTPException(503, "The AI models are still loading. Please try again in a moment.")

    # Requests queue for one photo at a time; give up rather than pile up threads behind a slow CPU
    if not model_lock.acquire(timeout=Config.QUEUE_TIMEOUT_S):
        raise HTTPException(503, "The app is busy with other photos. Please try again in a minute.")
    try:
        result = analyse(img)
    except Exception:
        logger.exception("Describing a photo failed")
        raise HTTPException(500, "Something went wrong while describing this photo. Please try another one.")
    finally:
        model_lock.release()
    logger.info("described %dx%d photo in %s, unclear=%s, %d text lines", *img.size,
                result["seconds"], result["unclear"], len(result["text_lines"]))
    return result


def analyse(img):
    timings = {}
    t = time.time()
    p_unreadable = models["captioner"].unreadable_probability(img)
    unclear = p_unreadable >= Config.UNREADABLE_THRESHOLD
    summary = models["captioner"].generate_caption(img, avoid_unreadable=not unclear)
    timings["summary"] = time.time() - t

    t = time.time()
    description = models["describer"].describe(img)
    timings["description"] = time.time() - t

    text_lines = []
    # OCR invents characters on blurry photos; reading a wrong dose or number aloud is worse than none
    if not unclear and models["describer"].mentions_text(description):
        t = time.time()
        text_lines = models["describer"].read_text(img)
        timings["text"] = time.time() - t

    return {
        "summary": "This photo looks blurry or unclear." if unclear else summary[0].upper() + summary[1:],
        "unclear": unclear,
        "unreadable_probability": round(p_unreadable, 3),
        "retake_tip": RETAKE_TIP if unclear else None,
        "description": description,
        "text_lines": text_lines,
        "speech": build_speech(unclear, description, text_lines),
        "seconds": {k: round(v, 1) for k, v in timings.items()},
    }


@app.get("/api/eval")
def eval_results():
    path = ROOT / "eval" / "results.json"
    if not path.exists():
        # evaluate.py --push_to stores the results next to the model on the Hugging Face Hub
        try:
            from huggingface_hub import hf_hub_download
            path = Path(hf_hub_download(Config.BLIP_MODEL, "eval/results.json"))
        except Exception:
            raise HTTPException(404, "No evaluation yet. Run: python training/evaluate.py")
    return json.loads(path.read_text(encoding="utf-8"))


app.mount("/", StaticFiles(directory=ROOT / "static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
