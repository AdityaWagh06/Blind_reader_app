# Changelog

## 2.2.0

- Requests wait at most 120 s for the models (configurable), then get a 503 instead of piling up.
- A model failure returns a clean 500 and is logged with its traceback. Each photo is logged with size, timings and outcome only.
- Security headers on every page: a strict Content-Security-Policy, nosniff, no-referrer and a camera-only Permissions-Policy.
- The Docker image runs as a non-root user and has a health check.
- Ruff linting, a `pyproject.toml`, and CI on Python 3.10 and 3.13 with a Docker build check.
- Simplified the BLIP wrapper.
- Rewrote the README.

## 2.1.0

- Phone photos are turned upright using their EXIF orientation, and large photos are shrunk in the browser before upload, so they are no longer rejected by the 10 MB limit.
- Images that would decode to an extreme number of pixels are rejected with a clear message.
- Invalid settings, such as a threshold outside 0–1, stop the app at startup.
- Test suite (pytest) and GitHub Actions CI.
- Dockerfile.
- MIT licence and a project guide (`docs/PROJECT_GUIDE.md`).

## 2.0.0

- New FastAPI website, replacing Streamlit, with Describe, Evaluation and How it works pages.
- BLIP fine-tuned on VizWiz-Captions and published as `adityawagh07/blip-vizwiz`.
- Florence-2 for detailed descriptions and text reading.
- Held-out evaluation (BLEU, ROUGE-L, CIDEr, loss, precision and recall) and a calibrated blurry-photo threshold (0.40).
- Speech in the browser (Web Speech API), replacing server-side text-to-speech.

## 1.0.0

- First Streamlit version: BLIP captions, text explanation and speech.
