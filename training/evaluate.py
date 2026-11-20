"""
Evaluate the caption models on the VizWiz photos held out from fine-tuning.

Rebuilds the exact held-out split used by finetune_blip.py (5% of "val", seed 42), runs every model on each
photo and scores the results against the human captions:

  * caption metrics  - BLEU-1/4, ROUGE-L, CIDEr (how close the wording is to the human caption)
  * held-out loss    - how probable the human caption is under each BLIP model (lower is better)
  * unreadable check - can the model tell when a photo is too blurry/dark to describe? (precision/recall/F1)
  * calibration      - picks the probability threshold for that check on one half of the held-out photos
                       and reports it on the other half, so the reported score is not tuned on its own data

Writes eval/results.json (shown on the website's Evaluation page) and eval/predictions.csv (every output).
Runs best on a GPU, e.g. Colab:  python training/evaluate.py --push_to <user>/blip-vizwiz
"""
import argparse
import csv
import json
import math
import os
import re
import sys
import time

import torch
from datasets import Dataset, load_dataset
from pycocoevalcap.bleu.bleu import Bleu
from pycocoevalcap.cider.cider import Cider
from pycocoevalcap.rouge.rouge import Rouge

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.image_captioning import ImageCaptioner  # noqa: E402
from utils.scene_describer import SceneDescriber  # noqa: E402

QUALITY_PHRASE = "quality issues"
BLIPS = {"Original BLIP": "Salesforce/blip-image-captioning-base",
         "Fine-tuned BLIP (ours)": "adityawagh07/blip-vizwiz"}
FLORENCE = "Florence-2 (short caption)"


def held_out_indices(n_rows, eval_fraction, seed):
    # train_test_split only depends on the row count and seed, so the same indices come back without images
    idx = Dataset.from_dict({"i": list(range(n_rows))}).train_test_split(test_size=eval_fraction, seed=seed)
    return sorted(idx["test"]["i"])


@torch.no_grad()
def caption_loss(captioner, image, caption, max_tokens=40):
    """Cross-entropy of the human caption under the model: the same number training minimised (eval_loss)"""
    enc = captioner.processor(images=image, text=caption.strip(), padding="max_length", truncation=True,
                              max_length=max_tokens, return_tensors="pt").to(captioner.device)
    labels = enc["input_ids"].clone()
    labels[enc["attention_mask"] == 0] = -100
    return captioner.model(**enc, labels=labels).loss.item()


def tokenize(text):
    # Same normalisation for every model: lowercase, words only (COCO's Java tokenizer is not needed)
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def caption_scores(refs, preds):
    gts = {i: [tokenize(r)] for i, r in enumerate(refs)}
    res = {i: [tokenize(p)] for i, p in enumerate(preds)}
    bleu, _ = Bleu(4).compute_score(gts, res, verbose=0)
    rouge, _ = Rouge().compute_score(gts, res)
    cider, _ = Cider().compute_score(gts, res)
    return {"BLEU-1": bleu[0], "BLEU-4": bleu[3], "ROUGE-L": rouge, "CIDEr": cider}


def classify(truth, guess):
    tp = sum(t and g for t, g in zip(truth, guess))
    fp = sum(g and not t for t, g in zip(truth, guess))
    fn = sum(t and not g for t, g in zip(truth, guess))
    tn = len(truth) - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "accuracy": (tp + tn) / len(truth),
            "precision": precision, "recall": recall, "f1": f1}


def is_unreadable(caption):
    return caption.lower().startswith(QUALITY_PHRASE)


def calibrate(truth, probs):
    """Choose the threshold on even-numbered photos, report it on odd-numbered ones (never used for choosing)"""
    thresholds = [round(t / 20, 2) for t in range(1, 20)]
    tune = [i for i in range(len(truth)) if i % 2 == 0]
    test = [i for i in range(len(truth)) if i % 2 == 1]
    pick = lambda idx, th: classify([truth[i] for i in idx], [probs[i] >= th for i in idx])  # noqa: E731
    # Ties go to the higher threshold: fewer false "too blurry" alarms for the user
    best = max(thresholds, key=lambda th: (pick(tune, th)["f1"], th))
    curve = [{"threshold": th, **{k: v for k, v in classify(truth, [p >= th for p in probs]).items()
                                  if k in ("precision", "recall", "f1")}} for th in thresholds]
    return {"threshold": best, "tuned_on": len(tune), "reported_on": len(test),
            "test_half": pick(test, best), "curve": curve}, test


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="lmms-lab/VizWiz-Caps")
    p.add_argument("--split", default="val")
    p.add_argument("--eval_fraction", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--out_dir", default="eval")
    p.add_argument("--push_to", default=None, help="Hub model repo to upload eval/ files to, e.g. you/blip-vizwiz")
    args = p.parse_args()

    ds = load_dataset(args.dataset, split=args.split, data_files={args.split: f"data/{args.split}-*.parquet"},
                      verification_mode="no_checks")  # the card also lists splits we did not download
    wanted = held_out_indices(len(ds), args.eval_fraction, args.seed)[: args.limit]
    ds = ds.select(wanted)
    print(f"Evaluating on {len(ds)} held-out photos", flush=True)

    blips = {name: ImageCaptioner(repo) for name, repo in BLIPS.items()}
    for c in blips.values():
        c.model.eval()
    florence = SceneDescriber()
    names = list(blips) + [FLORENCE]

    rows = []
    secs = {n: 0.0 for n in names}
    for k, ex in enumerate(ds):
        img = ex["image"].convert("RGB")
        row = {"row": wanted[k], "image_id": ex["image_id"], "human": ex["caption"]}
        for name, c in blips.items():
            t = time.time()
            row[name] = c.generate_caption(img)
            secs[name] += time.time() - t
            row[f"{name} | loss"] = caption_loss(c, img, ex["caption"])
            row[f"{name} | p_unreadable"] = c.unreadable_probability(img)
        t = time.time()
        row[FLORENCE] = florence.caption(img)
        secs[FLORENCE] += time.time() - t
        rows.append(row)
        if (k + 1) % 25 == 0 or k + 1 == len(ds):
            print(f"{k + 1}/{len(ds)} photos done", flush=True)

    refs = [r["human"] for r in rows]
    truth = [is_unreadable(h) for h in refs]
    results = {
        "dataset": f"{args.dataset} ({args.split} split, held-out {args.eval_fraction:.0%}, seed {args.seed})",
        "photos": len(rows),
        "photos_marked_unreadable_by_humans": sum(truth),
        "models": {},
    }
    for name in names:
        preds = [r[name] for r in rows]
        m = {"caption": caption_scores(refs, preds),
             "quality_check": classify(truth, [is_unreadable(x) for x in preds]),
             "avg_words": sum(len(x.split()) for x in preds) / len(rows),
             "seconds_per_photo": secs[name] / len(rows)}
        if name in blips:
            loss = sum(r[f"{name} | loss"] for r in rows) / len(rows)
            m.update(held_out_loss=loss, perplexity=math.exp(loss))
        results["models"][name] = m

    ours = "Fine-tuned BLIP (ours)"
    cal, test_idx = calibrate(truth, [r[f"{ours} | p_unreadable"] for r in rows])
    # The old rule (trust the caption's first words) on the same half, for a fair before/after
    cal["test_half_caption_rule"] = classify([truth[i] for i in test_idx], [is_unreadable(rows[i][ours]) for i in test_idx])
    results["calibration"] = cal
    results["examples"] = [{k: v for k, v in r.items() if " | " not in k} for r in rows[:12]]

    os.makedirs(args.out_dir, exist_ok=True)
    res_path = os.path.join(args.out_dir, "results.json")
    csv_path = os.path.join(args.out_dir, "predictions.csv")
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({k: v for k, v in results.items() if k != "examples"}, indent=2))

    if args.push_to:
        from huggingface_hub import upload_file
        for path in (res_path, csv_path):
            upload_file(path_or_fileobj=path, path_in_repo=f"eval/{os.path.basename(path)}", repo_id=args.push_to,
                        commit_message="Add held-out evaluation results")
        print(f"Uploaded results to https://huggingface.co/{args.push_to}/tree/main/eval")


if __name__ == "__main__":
    main()
