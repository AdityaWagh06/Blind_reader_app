# 👁️ Blind Reader Assistant

A private, offline website that helps blind and visually impaired people understand photos. Take or upload a picture and hear a **detailed description of everything in it**: objects, people, colours, where things are, and any text, read out word for word. It also **warns you when a photo is too blurry or dark** to describe.

All AI runs on your own computer with free, open-source models from Hugging Face. There is no paid API, no account and no cloud upload.

![Blind Reader Assistant screenshot](assets/screenshot.png)

## Features

- **Detailed descriptions** by Microsoft Florence-2: small things count, e.g. *"There are two white remote controls resting on the couch next to them."*
- **Reads text**: labels, medicine boxes, signs, screens and documents, line by line
- **Knows when it can't see**: our own model, fine-tuned on 7,362 photos taken by blind people, flags unreadable photos and suggests how to retake them
- **Speaks automatically** with the computer's built-in voices, with pause, resume, stop and speed controls
- **Professional, accessible web UI**: upload, camera, drag-and-drop or paste; large text; light and dark themes; keyboard and screen-reader friendly
- **Measured accuracy**: an Evaluation page with BLEU, ROUGE-L, CIDEr, held-out loss and precision/recall, explained in plain language

## Quick start

**Windows:** double-click `run.bat`, then open **http://127.0.0.1:8000**.

**Any OS:**

```bash
git clone https://github.com/AdityaWagh06/Blind_reader_app.git
cd Blind_reader_app
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py                   # then open http://127.0.0.1:8000
```

The first start downloads the two models (about 1.4 GB) from Hugging Face. After that everything works offline. Check an installation end to end with `python test_installation.py`.

Requirements: Python 3.9+, about 4 GB of free RAM. A GPU is optional (CPU: 10–25 s per photo).

**Docker:**

```bash
docker build -t blind-reader .
docker run -p 8000:8000 -v blind-reader-models:/models blind-reader
```

## How it works

```
photo ──► fine-tuned BLIP ─────────► one-line summary + "is it too blurry?" (probability)
      └─► Florence-2 ──────────────► detailed paragraph description
                    └─(if text)────► OCR: every line of text
                                       │
           browser (Web Speech API) ◄──┘  reads it aloud
```

| Step | Model | Size | Why |
|---|---|---|---|
| Summary & blurry-photo check | [`adityawagh07/blip-vizwiz`](https://huggingface.co/adityawagh07/blip-vizwiz): our fine-tune of [`Salesforce/blip-image-captioning-base`](https://huggingface.co/Salesforce/blip-image-captioning-base) | 0.25B params | Specialised for photos taken by blind people |
| Detailed description & text reading | [`florence-community/Florence-2-base`](https://huggingface.co/florence-community/Florence-2-base) (Microsoft, MIT) | 0.23B params | Rich detail and OCR in one small model |
| Speech | Browser Web Speech API | built in | Instant, offline, with pause and speed |

The website itself explains everything in depth on its **How it works** and **Evaluation** pages.

## Our fine-tuned model

BLIP was fine-tuned on [VizWiz-Captions](https://huggingface.co/datasets/lmms-lab/VizWiz-Caps), real photos taken by blind people with human-written descriptions, on a free Google Colab T4 GPU:

- 7,750 captioned photos, split with seed 42 into **7,362 for training** and **388 held out for testing**
- 3 epochs (1,383 steps of 16 photos), learning rate 5e-5, fp16, 27.5 minutes
- Held-out loss after each epoch: 2.326 → **2.291** → 2.338. The best epoch (2) was kept automatically, before the model began to overfit.

### Evaluation results

Measured on the **388 held-out photos** (never seen in training) with `training/evaluate.py` on a Colab T4. Scores compare each model's caption with the one human caption per photo.

| Model | Held-out loss ↓ | Perplexity ↓ | BLEU-1 | BLEU-4 | ROUGE-L | CIDEr |
|---|---|---|---|---|---|---|
| Original BLIP | 4.298 | 73.6 | 0.254 | 0.049 | 0.253 | 0.491 |
| **Fine-tuned BLIP (ours)** | **2.212** | **9.1** | 0.283 | **0.159** | **0.292** | **1.684** |
| Florence-2 (short caption mode) | – | – | **0.305** | 0.077 | 0.276 | 0.756 |

Fine-tuning cut the held-out loss by **49%** and raised CIDEr **3.4×**.

**Detecting photos that are too blurry or dark to describe** (50 of the 388 were labelled so by humans):

| Rule | Caught | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Original BLIP | 0 | 0 | 50 | – | 0% | 0% |
| Fine-tuned, trusting its caption's first words (all 388) | 45 | 142 | 5 | 24.1% | 90.0% | 38.0% |
| Fine-tuned, trusting its caption (194 report photos) | 32 | 67 | 3 | 32.3% | 91.4% | 47.8% |
| **Fine-tuned, probability ≥ 0.4 (used by the app, same 194)** | 18 | **5** | 17 | **78.3%** | 51.4% | **62.1%** |

The 0.4 threshold was picked on the other 194 held-out photos, so it is not tuned on the photos it is reported on. Calibrating cut false alarms from 67 to 5, at the cost of missing more blurry photos. The app also never refuses: it warns, skips text reading (OCR invents characters on blurry photos), and still describes the scene.

Reproduce: run the last cell of [`training/finetune_blip_colab.ipynb`](training/finetune_blip_colab.ipynb) in Colab, or `python training/evaluate.py` on any machine with a GPU. Every caption from every model is in `eval/predictions.csv`.

### How the metrics work (short version)

- **BLEU-1 / BLEU-4**: share of 1-word / up-to-4-word sequences in the model's caption that also appear in the human caption
- **ROUGE-L**: longest run of words both captions share in the same order
- **CIDEr**: n-gram similarity where informative words ("Pepsi", "medicine") count far more than common ones ("a", "the"). This is the main captioning metric.
- **Held-out loss / perplexity**: how surprised the model is by the human's real caption on photos it never trained on (lower is better)
- **Precision / recall / F1**: for the yes/no "too blurry?" decision, how often an alarm is right / how many blurry photos are caught / the balance of both

Full explanations with formulas and worked examples are on the website's Evaluation page and in [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md).

## Train your own

1. Open [`training/finetune_blip_colab.ipynb`](training/finetune_blip_colab.ipynb) in Google Colab and choose a free **T4 GPU** runtime.
2. Add your Hugging Face **write** token as a Colab secret named `HF_TOKEN` (🔑 icon, enable notebook access).
3. Run the cells. You'll get live TensorBoard charts, before and after captions, and the model is published to `https://huggingface.co/<you>/blip-vizwiz`.
4. Put that name in `config.py` (`BLIP_MODEL`) or set `$env:BLIND_READER_BLIP_MODEL`.

Quick local check of the training code (16 photos, 2 steps): `python training/finetune_blip.py --limit 16 --max_steps 2 --batch_size 2`

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests
```

The tests use stand-in models, so they run in seconds and download nothing. GitHub Actions runs them on every push. `python test_installation.py` is the slower end-to-end check with the real models.

## Configuration

Settings live in `config.py`. Each can be overridden with an environment variable prefixed `BLIND_READER_`:

| Setting | Default | Meaning |
|---|---|---|
| `BLIP_MODEL` | `adityawagh07/blip-vizwiz` | Summary + blurry-photo model |
| `FLORENCE_MODEL` | `florence-community/Florence-2-base` | Detailed description + OCR (`-large` is more accurate, needs a GPU) |
| `UNREADABLE_THRESHOLD` | calibrated value | Probability above which a photo is called too blurry |
| `MAX_FILE_SIZE_MB` | `10` | Upload limit |
| `HOST`, `PORT` | `127.0.0.1`, `8000` | Where the website is served |

## API

| Method | Path | Returns |
|---|---|---|
| `GET` | `/api/status` | whether the models are loaded |
| `POST` | `/api/describe` (form field `image`) | `summary`, `description`, `text_lines`, `unclear`, `unreadable_probability`, `speech`, timings |
| `GET` | `/api/eval` | evaluation results (local `eval/results.json` or the copy on the model's Hub page) |

Interactive API docs: http://127.0.0.1:8000/docs

## Project structure

```
app.py                     FastAPI server: website + API
config.py                  settings
static/                    website (index.html, styles.css, app.js)
utils/image_captioning.py  BLIP: summary + unreadable probability
utils/scene_describer.py   Florence-2: detailed description + OCR
training/finetune_blip.py  fine-tuning script
training/finetune_blip_colab.ipynb  Colab notebook: train, publish, evaluate
training/evaluate.py       held-out evaluation and threshold calibration
tests/                     fast API and text-reading tests (pytest)
docs/PROJECT_GUIDE.md      the whole project explained, with every metric and common questions
eval/                      evaluation results and every prediction
test_installation.py       end-to-end installation check
run.bat / run.sh / run.py  launchers
```

## Limitations

- Detailed descriptions can occasionally contain small mistakes, such as a wrong colour or count.
- Florence-2's text reader can invent text (e.g. a stock-photo watermark on a blank image, or digits on a blurry label). The app therefore reads text only when the description mentions text and the photo is not flagged as unclear.
- The blurry-photo check still misses about half of the truly unreadable photos at the chosen threshold, a deliberate trade-off for far fewer false alarms.
- Captions are scored against one human caption per photo, so absolute BLEU and CIDEr values are lower than published benchmarks that use five.
- On a CPU a photo takes 10–25 seconds; a GPU brings this to a few seconds.

## License

The code is MIT licensed (see [LICENSE](LICENSE)). The models and data keep their own licences: BLIP (BSD-3-Clause), Florence-2 (MIT) and VizWiz-Captions (CC BY 4.0).

## Acknowledgments

Salesforce (BLIP), Microsoft (Florence-2), the VizWiz project and lmms-lab (dataset), Hugging Face (Transformers, Hub), FastAPI.
