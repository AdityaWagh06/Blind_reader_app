# 👁️ Blind Reader Assistant

**Take a photo, hear what's in it.** A private, offline web app that describes photos in detail for blind and visually impaired people. It reads any text out word for word and warns when a photo is too blurry to trust. It uses a BLIP model that we fine-tuned on 7,362 real photos taken by blind people.

[![tests](https://github.com/AdityaWagh06/Blind_reader_app/actions/workflows/tests.yml/badge.svg)](https://github.com/AdityaWagh06/Blind_reader_app/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
[![Model on Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20model-blip--vizwiz-yellow)](https://huggingface.co/adityawagh07/blip-vizwiz)

![Blind Reader Assistant screenshot](assets/screenshot.png)

## Highlights

- **Fine-tuned model, measured on photos it never saw:** held-out loss fell by **49%** and CIDEr rose **3.4×** (0.49 → 1.68) compared with the original BLIP.
- **Calibrated "too blurry" warning:** false alarms fell from 67 to 5 on 194 test photos, and F1 rose from 47.8% to 62.1%.
- **Detailed descriptions:** it notices small things. For a photo of cats on a couch it adds *"There are two white remote controls resting on the couch next to them."*
- **Private by design:** everything runs locally with free, open models. There is no paid API, no account, and photos are never uploaded anywhere.

## Contents

[Features](#features) · [Quick start](#quick-start) · [How it works](#how-it-works) · [Fine-tuning](#the-fine-tuned-model) · [Evaluation](#evaluation) · [Engineering](#engineering) · [API](#api) · [Configuration](#configuration) · [Development](#development) · [Limitations](#limitations-and-roadmap)

## Features

- **Describes everything in the photo:** objects, people, colours, positions and small details (Microsoft Florence-2).
- **Reads text:** labels, medicine boxes, signs, screens and documents, line by line.
- **Knows when it can't see:** flags blurry or dark photos and explains how to retake them. It never reads text from such photos, because a wrongly read medicine dose is worse than none.
- **Speaks automatically** using the device's own voices, with pause, stop and speed controls.
- **Accessible web interface:**
  - upload, camera, drag-and-drop or paste;
  - large text, light and dark themes;
  - works with a keyboard and screen readers.
- **Phone-friendly:** large photos are shrunk and turned upright in the browser before upload.
- **Transparent:** an Evaluation page shows every metric with plain-language explanations.

## Quick start

**Windows:** double-click `run.bat`, then open **http://127.0.0.1:8000**.

**macOS / Linux / Windows (manual):**

```bash
git clone https://github.com/AdityaWagh06/Blind_reader_app.git
cd Blind_reader_app
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py                   # then open http://127.0.0.1:8000
```

**Docker:**

```bash
docker build -t blind-reader .
docker run -p 8000:8000 -v blind-reader-models:/models blind-reader
```

The first start downloads the two models (about 1.4 GB) from Hugging Face. After that, the app works offline. You need Python 3.9+ and about 4 GB of free RAM. A GPU is optional: on a CPU, each photo takes 10–25 seconds.

## How it works

```
                 ┌─► fine-tuned BLIP ──► one-line summary + P(photo is unreadable)
photo ─► server ─┤
 (browser shrinks│                                   P ≥ 0.40 → "too blurry" warning, skip text reading
  and rotates)   └─► Florence-2 ───────► detailed paragraph
                              └─(text mentioned and photo clear)─► OCR: every line of text
                                                       │
                      browser speaks the result ◄──────┘   (Web Speech API)
```

| Step | Model | Size | Why this model |
|---|---|---|---|
| Summary and blurry check | [`adityawagh07/blip-vizwiz`](https://huggingface.co/adityawagh07/blip-vizwiz), our fine-tune of [`Salesforce/blip-image-captioning-base`](https://huggingface.co/Salesforce/blip-image-captioning-base) | 0.25B | Trained on photos taken by blind people, so it learnt when a photo is unusable |
| Detailed description and text reading | [`florence-community/Florence-2-base`](https://huggingface.co/florence-community/Florence-2-base) (Microsoft, MIT) | 0.23B | Rich detail and OCR in one small model |
| Speech | Browser Web Speech API | built in | Instant, offline, with pause and speed |

Both models are small enough to run on a normal laptop CPU.

## The fine-tuned model

BLIP was fine-tuned on [VizWiz-Captions](https://huggingface.co/datasets/lmms-lab/VizWiz-Caps): real photos taken by blind people, each with a caption written by a person. Training ran on a free Google Colab T4 GPU.

| | |
|---|---|
| Data | 7,750 captioned photos, split with seed 42 into **7,362 for training** and **388 held out** |
| Training | 3 epochs (1,383 steps of 16 photos), learning rate 5e-5, fp16, 27.5 minutes |
| Held-out loss per epoch | 2.326 → **2.291** → 2.338. The best epoch (2) was kept automatically, before overfitting set in |
| Published | [huggingface.co/adityawagh07/blip-vizwiz](https://huggingface.co/adityawagh07/blip-vizwiz) |

To train your own: open [`training/finetune_blip_colab.ipynb`](training/finetune_blip_colab.ipynb) in Colab, choose a T4 GPU, and add a Hugging Face write token as the Colab secret `HF_TOKEN`. Then run the cells. The notebook shows live TensorBoard charts, before-and-after captions, publishes the model, and runs the evaluation. To use your model in the app, set `BLIP_MODEL`.

## Evaluation

All numbers come from the **388 held-out photos** (never used in training), produced by [`training/evaluate.py`](training/evaluate.py) on a Colab T4. Every caption from every model is in [`eval/predictions.csv`](eval/predictions.csv).

### Caption quality

| Model | Held-out loss ↓ | Perplexity ↓ | BLEU-1 | BLEU-4 | ROUGE-L | CIDEr |
|---|---|---|---|---|---|---|
| Original BLIP | 4.298 | 73.6 | 0.254 | 0.049 | 0.253 | 0.491 |
| **Fine-tuned BLIP (ours)** | **2.212** | **9.1** | 0.283 | **0.159** | **0.292** | **1.684** |
| Florence-2 (short caption mode) | – | – | **0.305** | 0.077 | 0.276 | 0.756 |

### "Too blurry" detection

Humans labelled 50 of the 388 photos as unreadable. The 0.40 threshold was chosen on one half of the held-out photos and is reported on the other half (194 photos), so it is never scored on the photos it was tuned on.

| Rule | Caught | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Original BLIP | 0 | 0 | 50 | – | 0% | 0% |
| Fine-tuned, trusting its caption (all 388) | 45 | 142 | 5 | 24.1% | 90.0% | 38.0% |
| Fine-tuned, trusting its caption (194 report photos) | 32 | 67 | 3 | 32.3% | 91.4% | 47.8% |
| **Fine-tuned, probability ≥ 0.40 (used by the app, same 194)** | 18 | **5** | 17 | **78.3%** | 51.4% | **62.1%** |

### What the metrics mean

- **BLEU-1 / BLEU-4:** the share of the model's 1-word (BLEU-1) or up-to-4-word (BLEU-4) sequences that also appear in the human caption.
- **ROUGE-L:** the longest run of words that both captions share, in the same order.
- **CIDEr:** the main captioning metric. It compares word sequences, but rare, informative words ("Pepsi", "insulin") count far more than common ones ("a", "the").
- **Held-out loss / perplexity:** how surprised the model is by the real human caption (lower is better). Perplexity = e^loss.
- **Precision / recall / F1:** for the yes/no "too blurry?" decision.
  - Precision: how often a warning is right.
  - Recall: how many blurry photos are caught.
  - F1: the balance of the two.

The [project guide](docs/PROJECT_GUIDE.md) and the website's Evaluation page explain each metric with formulas and worked examples.

## Engineering

| Area | What is in place |
|---|---|
| Testing | 15 fast pytest tests with stand-in models: upload validation, the clear and blurry paths, OCR gating, EXIF rotation, busy and crash handling, security headers. Plus `test_installation.py` for an end-to-end check with the real models |
| CI | GitHub Actions on every push: ruff lint, tests on Python 3.9 and 3.12, and a Docker build-and-start check |
| Input safety | 10 MB upload limit, real image decoding (not trusting the file extension), decompression-bomb protection, EXIF orientation |
| Reliability | Models load in the background so the site is up instantly. Requests are queued with a timeout (503 when busy). Model failures return a clean 500 without internals, and are logged with a traceback |
| Security | Strict Content-Security-Policy (no third-party scripts), nosniff, no-referrer, camera-only Permissions-Policy. Binds to 127.0.0.1 by default. The Docker image runs as a non-root user and has a health check |
| Privacy | Photos are processed in memory and never stored. Logs record only image size, timings and outcome |
| Configuration | Every setting can be overridden with an environment variable and is validated at startup |

## API

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/status` | Whether the models are loaded, and any loading error |
| `POST` | `/api/describe` (multipart field `image`) | `summary`, `description`, `text_lines`, `unclear`, `unreadable_probability`, `retake_tip`, `speech`, `seconds` |
| `GET` | `/api/eval` | Evaluation results (local `eval/results.json`, or the copy on the model's Hub page) |

`/api/describe` errors:

| Code | Meaning |
|---|---|
| 413 | File too large, or too many pixels |
| 415 | Not a readable image |
| 503 | Models still loading, or the server is busy |
| 500 | A model failed |

Interactive API docs are at http://127.0.0.1:8000/docs.

```bash
curl -F image=@photo.jpg http://127.0.0.1:8000/api/describe
```

## Configuration

Settings live in [`config.py`](config.py). You can override any of them with an environment variable prefixed `BLIND_READER_`, for example `BLIND_READER_PORT=9000`.

| Setting | Default | Meaning |
|---|---|---|
| `BLIP_MODEL` | `adityawagh07/blip-vizwiz` | Summary and blurry-photo model |
| `FLORENCE_MODEL` | `florence-community/Florence-2-base` | Detailed description and OCR. `-large` is more accurate but needs a GPU |
| `UNREADABLE_THRESHOLD` | `0.4` | Probability above which a photo is called too blurry (calibrated) |
| `MAX_FILE_SIZE_MB` | `10` | Upload limit |
| `QUEUE_TIMEOUT_S` | `120` | How long a request waits while another photo is being described |
| `HOST`, `PORT` | `127.0.0.1`, `8000` | Where the website is served |

## Development

```bash
pip install -r requirements-dev.txt
pytest                 # 15 tests, a few seconds, no model downloads
ruff check .           # lint
python test_installation.py   # end-to-end check with the real models
```

Training and evaluation dependencies are in `requirements-train.txt`. To check the training code quickly on a CPU (16 photos, 2 steps):

```bash
python training/finetune_blip.py --limit 16 --max_steps 2 --batch_size 2
```

### Project structure

```
app.py                     FastAPI server: website, API, security headers
config.py                  settings, environment overrides and validation
static/                    website (index.html, styles.css, app.js); no build step
utils/image_captioning.py  BLIP: summary + unreadable probability
utils/scene_describer.py   Florence-2: detailed description + OCR
training/finetune_blip.py  fine-tuning script (Hugging Face Trainer)
training/finetune_blip_colab.ipynb  Colab notebook: train, publish, evaluate
training/evaluate.py       held-out evaluation and threshold calibration
eval/                      evaluation results and every prediction
tests/                     pytest suite
docs/PROJECT_GUIDE.md      the whole project explained, with every metric and common questions
Dockerfile                 container image
run.bat / run.sh / run.py  launchers
```

## Limitations and roadmap

Known limitations:

- Detailed descriptions can contain small mistakes, such as a wrong colour or count.
- Florence-2's text reader can invent text on blank or blurry images. The app therefore reads text only when the description mentions text and the photo is not flagged as blurry.
- At the chosen threshold, the blurry check misses about half of the truly unreadable photos. This is a deliberate trade for far fewer false alarms.
- Captions are scored against one human caption per photo, so absolute BLEU and CIDEr values are lower than in published benchmarks, which use five.
- One photo is processed at a time, and on a CPU each takes 10–25 seconds.

Next steps:

- Train on the full VizWiz training split (about 23,000 photos).
- Fine-tune Florence-2 as well.
- Quantise the models for faster CPU inference.
- Test the app with blind users.

## License

The code is MIT licensed (see [LICENSE](LICENSE)). The models and data keep their own licences:

- BLIP: BSD-3-Clause
- Florence-2: MIT
- VizWiz-Captions: CC BY 4.0

## Acknowledgments

Salesforce (BLIP), Microsoft (Florence-2), the VizWiz project and lmms-lab (dataset), Hugging Face (Transformers, Hub), FastAPI.
