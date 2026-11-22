import logging
import re

import torch
from transformers import AutoProcessor, Florence2ForConditionalGeneration

logger = logging.getLogger(__name__)

# Words in a description that suggest the photo contains readable text worth a dedicated OCR pass
TEXT_HINTS = re.compile(
    r"\b(text|reads?|written|words?|label|sign|title|letters?|numbers?|screen|page|document)\b", re.IGNORECASE
)


class SceneDescriber:
    """Detailed scene descriptions and text reading with Microsoft Florence-2"""

    def __init__(self, model_name="florence-community/Florence-2-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Florence-2 model {model_name} on {self.device}...")
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.model = Florence2ForConditionalGeneration.from_pretrained(model_name).to(self.device).eval()

    @torch.no_grad()
    def _run(self, image, task, max_new_tokens=256):
        image = image.convert("RGB")
        inputs = self.processor(text=task, images=image, return_tensors="pt").to(self.device)
        out = self.model.generate(**inputs, max_new_tokens=max_new_tokens, num_beams=3)
        raw = self.processor.batch_decode(out, skip_special_tokens=False)[0]
        return self.processor.post_process_generation(raw, task=task, image_size=image.size)[task]

    def describe(self, image):
        """Paragraph describing everything visible: objects, colours, positions, people, text"""
        return self._run(image, "<MORE_DETAILED_CAPTION>").strip()

    def caption(self, image):
        """One short sentence (used for evaluation against short human captions)"""
        return self._run(image, "<CAPTION>", max_new_tokens=50).strip()

    def read_text(self, image):
        """Lines of text found in the image, top to bottom; empty list if none"""
        lines = self._run(image, "<OCR_WITH_REGION>", max_new_tokens=512).get("labels", [])
        lines = [re.sub(r"</?s>", "", line).strip() for line in lines]
        # Florence sometimes returns punctuation noise ("....") for photos without text
        return [line for line in lines if sum(ch.isalnum() for ch in line) >= 3]

    @staticmethod
    def mentions_text(description):
        return bool(TEXT_HINTS.search(description))
