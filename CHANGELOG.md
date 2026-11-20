# Changelog

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
