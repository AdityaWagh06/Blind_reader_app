# Project guide: everything you need to explain this project

This guide is for presenting the project and answering questions about it. The README covers installing and running it.

## 1. The problem in one paragraph

Blind and visually impaired people take photos of everyday things, such as medicine boxes, food packets, screens and letters, and need to know what is in them. Their photos are often blurry, dark or badly framed, because they cannot see the screen. A useful assistant must (1) describe the photo in detail, (2) read any text exactly, and (3) **say honestly when the photo is too poor to describe**, instead of guessing.

## 2. What the app does, step by step

1. The user uploads, pastes or takes a photo on the website. The browser shrinks very large photos to 2048 px and turns them upright.
2. The server (`app.py`, FastAPI) receives the photo and runs three steps, one photo at a time:
   - **Blurry check and summary.** Our fine-tuned BLIP model (`adityawagh07/blip-vizwiz`) gives the probability that the photo is unreadable. If it is 0.40 or more, the photo is flagged as unclear. BLIP also writes a one-line summary.
   - **Detailed description.** Florence-2 (`<MORE_DETAILED_CAPTION>`) writes a paragraph about the objects, colours, positions and small details. For example, it mentions the two remotes on the couch in the cats photo.
   - **Text reading (OCR).** This runs only if the description mentions text (label, sign, words…) **and** the photo is not flagged as unclear. Florence-2 (`<OCR_WITH_REGION>`) returns every line of text.
3. The website shows the result and reads it aloud with the browser's built-in voices (Web Speech API).

Why two models? BLIP is small and easy to fine-tune, so we specialised it on blind users' photos. Florence-2 gives much richer detail and can read text. Each model does what it is best at.

## 3. What we built, in order

| Step | What | Why |
|---|---|---|
| 1 | Fixed the original Streamlit app (installs, bugs, launcher) | It did not run |
| 2 | Fine-tuned BLIP on VizWiz-Captions in Google Colab (free T4 GPU) | Generic BLIP never learnt what blind users' photos look like, or how to say "this is too blurry" |
| 3 | Published the model to Hugging Face | So the app (and anyone) can download it |
| 4 | Added Florence-2 | Detailed descriptions and accurate text reading |
| 5 | Replaced Streamlit with a FastAPI website | A professional, accessible product with an API |
| 6 | Evaluated all models on 388 held-out photos | To prove the fine-tuning helped, with numbers |
| 7 | Calibrated the blurry check | The raw model raised far too many false alarms |
| 8 | Tests, CI, Docker, licence | So the project is maintainable and easy to run anywhere |
| 9 | Production hardening: request queue limit, clean error handling, security headers, non-root Docker, linting | So it behaves safely under load, bad input and failures |

## 4. The data

- **VizWiz-Captions**: real photos taken by blind people, each with captions written by humans. We used the `lmms-lab/VizWiz-Caps` copy on Hugging Face (its `val` split has 7,750 captioned photos).
- **Split**: `train_test_split(test_size=0.05, seed=42)` gives **7,362 training photos** and **388 held-out photos**. The held-out photos are never used for training. The fixed seed means anyone gets exactly the same split.
- About 1 in 7 VizWiz captions say something like *"Quality issues are too severe to recognize visual content."* That is how the model learnt to recognise unreadable photos.

## 5. The training

- Base model: `Salesforce/blip-image-captioning-base` (about 250 million parameters).
- Hugging Face `Trainer`: 3 epochs, batch size 16 (1,383 steps), learning rate 5e-5, fp16 (half precision, for speed), on a free Colab T4 GPU in **27.5 minutes**.
- After each epoch it measured the loss on the held-out photos: **2.326 → 2.291 → 2.338**. The loss rose in epoch 3, which means the model was starting to memorise the training photos (overfitting). `load_best_model_at_end` kept epoch 2 automatically.
- **Loss** is the training objective: for every word of the human caption, how much probability the model gave to that word. Loss = average of −log(probability). If the model gives the right word probability 1, the loss is 0.

## 6. Every metric, explained

### Caption quality

The model's caption is compared with the human caption for the same photo.

- **BLEU-n**: what fraction of the model's word sequences (1 word for BLEU-1, up to 4 words for BLEU-4) also appear in the human caption. It also applies a penalty for captions that are too short. BLEU-4 rewards getting whole phrases right.
  *Example:* human "a can of pepsi on a table", model "a can of coke on a table". Most single words match, so BLEU-1 is high. Fewer 4-word phrases match, so BLEU-4 is lower.
- **ROUGE-L**: the longest sequence of words that appears in both captions in the same order (gaps are allowed), turned into an F-score.
- **CIDEr**: the main captioning metric. Each word sequence is weighted with TF-IDF, so words that are rare across all captions ("pepsi", "insulin") count far more than common ones ("a", "the", "of"). The score is the similarity between the two weighted vectors, scaled by 10. That scaling is why CIDEr can be above 1.
- **Held-out loss and perplexity**: we feed the model the human caption and measure how surprised it is. Perplexity = e^loss: roughly, how many words the model is choosing between at each step. Original BLIP: perplexity 73.6. Ours: 9.1.

### The blurry check (a yes/no classifier)

Each held-out photo is labelled "unreadable" if its human caption says the quality is too poor. 50 of the 388 photos are labelled this way.

|                   | Human: unreadable | Human: fine |
|---|---|---|
| **App: unreadable** | True positive (caught) | False positive (false alarm) |
| **App: fine**       | False negative (missed) | True negative |

- **Precision** = caught ÷ (caught + false alarms). When the app says "blurry", how often is it right?
- **Recall** = caught ÷ (caught + missed). Of the truly blurry photos, how many does it catch?
- **F1** = 2 × P × R ÷ (P + R). One number that balances both.
- **Accuracy** = (caught + true negatives) ÷ all. This is misleading here: most photos are fine, so an app that never warns already scores 87%.

### Calibration (choosing the 0.40 threshold)

Trusting the model's caption ("does it start with *quality issues*?") raised 67 false alarms on 194 photos. Even a sharp medicine label was flagged. The reason: that sentence is very common in the training data, so beam search picks it even when the model is only about 10% sure.

The fix:

1. Measure the model's *probability* that the caption starts with "quality".
2. Try thresholds from 0.05 to 0.95 (steps of 0.05) on **half** of the held-out photos (even positions) and pick the one with the best F1: 0.40.
3. Report the result on the **other half** (odd positions), which played no part in choosing.

Choosing and reporting on the same photos would overstate the score. This is the same reason we hold out test data at all.

## 7. The results

**Captions (388 held-out photos):**

| Model | Loss ↓ | Perplexity ↓ | BLEU-1 | BLEU-4 | ROUGE-L | CIDEr |
|---|---|---|---|---|---|---|
| Original BLIP | 4.298 | 73.6 | 0.254 | 0.049 | 0.253 | 0.491 |
| **Fine-tuned BLIP (ours)** | **2.212** | **9.1** | 0.283 | **0.159** | **0.292** | **1.684** |
| Florence-2 (short caption) | – | – | 0.305 | 0.077 | 0.276 | 0.756 |

Loss fell by 49% and CIDEr rose 3.4×. Florence-2 has the best BLEU-1 because it uses many of the right words, but its phrasing differs from VizWiz captions, so its BLEU-4 and CIDEr are lower. That is why we use Florence-2 for detail and our model for the summary and the blurry check.

**Blurry check (194 report photos):**

| Rule | Caught | False alarms | Missed | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Trust the caption | 32 | 67 | 3 | 32.3% | 91.4% | 47.8% |
| **Probability ≥ 0.40 (used)** | 18 | **5** | 17 | **78.3%** | 51.4% | **62.1%** |

Accuracy rose from 63.9% to 88.7%. The trade-off: it now misses about half of the blurry photos. Because the app still describes the scene anyway, a missed warning costs less than a false alarm on a good photo.

## 8. Safety decisions

- **No text from blurry photos.** OCR invents characters on blurry photos (we saw "1.1.2.3…" on a blurred label). Reading a wrong medicine dose aloud is worse than reading nothing.
- **OCR only when text is mentioned.** On a blank white image, Florence-2's OCR invented a website address. Gating OCR on the description prevents this.
- **Everything runs locally.** Photos never leave the computer. There is no API key and no cost.

## 9. Technology used

| Area | Tool |
|---|---|
| Models | PyTorch, Hugging Face Transformers, BLIP (Salesforce, BSD-3), Florence-2 (Microsoft, MIT) |
| Data | Hugging Face Datasets, VizWiz-Captions (CC BY 4.0) |
| Training | Hugging Face Trainer, Google Colab T4 GPU, TensorBoard, Hugging Face Hub |
| Evaluation | pycocoevalcap (BLEU, ROUGE-L, CIDEr), our own precision/recall/calibration code |
| Server | FastAPI, Uvicorn, Pillow |
| Website | Plain HTML, CSS and JavaScript (no framework), Web Speech API |
| Quality | pytest, ruff, GitHub Actions, Docker |

## 10. Questions people ask

**Is this ChatGPT or a paid API?** No. Two small open models run on your own computer. There is no internet after the first download and no cost.

**What does "fine-tuning" mean here?** We took a model that was already trained on general internet photos and trained it further on 7,362 photos taken by blind people, so it learnt their kind of photos and captions.

**How do you know it is not just memorising?** All scores come from 388 photos it never saw during training. The training also stopped at the epoch where the held-out loss was lowest.

**Why is BLEU so low (0.28)?** Each photo has many valid descriptions, and we compare against only one human caption. Published benchmarks use five, which raises scores. What matters is the comparison between models on the same data: ours is clearly better.

**Why not use one big model?** Big vision-language models need a GPU and a lot of memory. Ours runs on a normal laptop in about 20 seconds per photo.

**What would you improve next?**
- Train on the full VizWiz training split (about 23,000 photos), not just the validation split.
- Fine-tune Florence-2 too.
- Run on a GPU or quantise the models for speed.
- Use more human captions per photo for evaluation.
- Ask blind users to test the app.

**Is it production ready?** For a single user or a small group on one machine, yes. It validates every upload, never stores photos, limits how long requests wait, fails cleanly, sends strict security headers, and is tested in CI, including the Docker build. Serving many users at once would need a GPU and a job queue, because it describes one photo at a time.

**What are the limitations?**
- Descriptions can contain small mistakes, such as a wrong colour or count.
- The blurry check misses about half of the unreadable photos.
- On a CPU, a photo takes about 20 seconds.
