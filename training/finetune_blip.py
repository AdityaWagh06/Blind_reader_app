"""
Fine-tune BLIP on VizWiz-Captions (photos taken by blind people) and optionally push it to the Hugging Face Hub.

Colab (free T4 GPU):  python training/finetune_blip.py --hub_repo <your-username>/blip-vizwiz
Quick local check:    python training/finetune_blip.py --limit 16 --max_steps 2 --batch_size 2
"""
import argparse
import random

import torch
from datasets import Dataset, load_dataset
from transformers import BlipForConditionalGeneration, BlipProcessor, Trainer, TrainingArguments


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base_model", default="Salesforce/blip-image-captioning-base")
    p.add_argument("--dataset", default="lmms-lab/VizWiz-Caps")
    # The dataset's "test" split has hidden (empty) captions, so we train on "val" and hold part of it out
    p.add_argument("--split", default="val")
    p.add_argument("--eval_fraction", type=float, default=0.05)
    p.add_argument("--output_dir", default="blip-vizwiz")
    p.add_argument("--hub_repo", default=None, help="e.g. your-username/blip-vizwiz; omit to keep the model local")
    p.add_argument("--epochs", type=float, default=3)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--lr", type=float, default=5e-5)
    p.add_argument("--max_caption_tokens", type=int, default=40)
    p.add_argument("--limit", type=int, default=None, help="use only the first N examples (smoke test)")
    p.add_argument("--max_steps", type=int, default=-1)
    p.add_argument("--logging_steps", type=int, default=25)
    p.add_argument("--report_to", default="tensorboard", help='live charts: "tensorboard --logdir <output_dir>/logs"; "none" to disable')
    return p.parse_args()


def load_data(args):
    if args.limit:
        # Stream so a smoke test doesn't download the full ~3.6 GB split
        rows = list(load_dataset(args.dataset, split=args.split, streaming=True).take(args.limit))
        ds = Dataset.from_list(rows)
    else:
        ds = load_dataset(args.dataset, split=args.split)
    ds = ds.filter(lambda c: bool(c and c.strip()), input_columns="caption")
    split = ds.train_test_split(test_size=args.eval_fraction, seed=42)
    print(f"train: {len(split['train'])} examples, eval: {len(split['test'])} examples")
    return split["train"], split["test"]


def make_collator(processor, max_tokens):
    def collate(batch):
        images = [ex["image"].convert("RGB") for ex in batch]
        enc = processor(images=images, text=[ex["caption"].strip() for ex in batch],
                        padding="max_length", truncation=True, max_length=max_tokens, return_tensors="pt")
        labels = enc["input_ids"].clone()
        labels[enc["attention_mask"] == 0] = -100  # don't learn to predict padding
        enc["labels"] = labels
        return enc
    return collate


@torch.no_grad()
def show_samples(model, processor, examples, title):
    model.eval()
    print(f"\n=== {title} ===")
    for ex in examples:
        inputs = processor(images=ex["image"].convert("RGB"), return_tensors="pt").to(model.device)
        out = model.generate(**inputs, max_length=40, num_beams=3)
        print(f"model : {processor.decode(out[0], skip_special_tokens=True)}")
        print(f"human : {ex['caption']}\n")


def main():
    args = parse_args()
    processor = BlipProcessor.from_pretrained(args.base_model)
    model = BlipForConditionalGeneration.from_pretrained(args.base_model)
    train_ds, eval_ds = load_data(args)

    samples = [eval_ds[i] for i in random.Random(0).sample(range(len(eval_ds)), min(3, len(eval_ds)))]
    if torch.cuda.is_available():
        model.to("cuda")
    show_samples(model, processor, samples, "Before fine-tuning")

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        warmup_ratio=0.05,
        weight_decay=0.01,
        fp16=torch.cuda.is_available(),
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        logging_steps=args.logging_steps,
        logging_dir=f"{args.output_dir}/logs",
        remove_unused_columns=False,  # the collator needs the raw "image" and "caption" columns
        dataloader_num_workers=2 if torch.cuda.is_available() else 0,
        push_to_hub=bool(args.hub_repo),
        hub_model_id=args.hub_repo,
        report_to=args.report_to,
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=train_ds, eval_dataset=eval_ds,
                      data_collator=make_collator(processor, args.max_caption_tokens))
    trainer.model_accepts_loss_kwargs = False  # BLIP's forward() rejects the num_items_in_batch kwarg
    trainer.train()
    print("final eval:", trainer.evaluate())

    show_samples(trainer.model, processor, samples, "After fine-tuning")

    trainer.save_model(args.output_dir)
    processor.save_pretrained(args.output_dir)
    if args.hub_repo:
        processor.push_to_hub(args.hub_repo)
        trainer.push_to_hub(commit_message="Fine-tuned BLIP on VizWiz-Captions")
        print(f"\nPushed to https://huggingface.co/{args.hub_repo}")
        print(f'Use it in the app: set BLIP_MODEL = "{args.hub_repo}" in config.py')


if __name__ == "__main__":
    main()
