import logging

import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor

logger = logging.getLogger(__name__)

MAX_SIDE = 512  # BLIP works at 384 px; shrinking first keeps preprocessing fast on huge photos


class ImageCaptioner:
    """Short captions and the "is this photo unreadable?" probability from a BLIP model"""

    def __init__(self, model_name="Salesforce/blip-image-captioning-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading BLIP model {model_name} on {self.device}...")
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(model_name).to(self.device).eval()
        self.quality_token = self.processor.tokenizer.convert_tokens_to_ids("quality")

    @staticmethod
    def preprocess_image(image):
        image = image.convert("RGB")
        if max(image.size) > MAX_SIDE:
            image = image.copy()
            image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        return image

    @torch.no_grad()
    def unreadable_probability(self, image):
        """
        Probability (0-1) that the caption starts with "quality" - how sure the VizWiz-tuned model is
        that the photo is too blurry/dark to describe ("quality issues are too severe ...").
        Thresholding this is more reliable than trusting the single best caption.
        """
        image = self.preprocess_image(image)
        inputs = self.processor(images=image, text="quality", return_tensors="pt").to(self.device)
        # BLIP replaces the first token with its decoder start token; logits[0, 0] predicts the first caption word
        logits = self.model(**inputs).logits[0, 0]
        quality_id = inputs["input_ids"][0, 1]
        return torch.softmax(logits.float(), dim=-1)[quality_id].item()

    @torch.no_grad()
    def generate_caption(self, image, avoid_unreadable=False):
        """
        One-sentence caption ending with a full stop.
        avoid_unreadable: never start with "quality ..." (use when the photo was judged readable)
        """
        inputs = self.processor(self.preprocess_image(image), return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_length=50,
            num_beams=5,
            early_stopping=True,
            do_sample=False,
            bad_words_ids=[[self.quality_token]] if avoid_unreadable else None,
        )
        caption = self.processor.decode(outputs[0], skip_special_tokens=True).strip()
        return caption if caption.endswith(".") else caption + "."
