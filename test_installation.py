#!/usr/bin/env python3
"""
End-to-end check that the installation works: loads both models and describes assets/sample.png.

    python test_installation.py
"""
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def main():
    from app import build_speech
    from config import Config
    from utils.image_captioning import ImageCaptioner
    from utils.scene_describer import SceneDescriber

    image = Image.open(ROOT / "assets" / "sample.png").convert("RGB")

    t = time.time()
    summary = ImageCaptioner(Config.BLIP_MODEL).generate_caption(image)
    print(f"OK  summary model ({Config.BLIP_MODEL}): {summary!r}  [{time.time() - t:.1f}s incl. loading]")
    assert summary.strip(), "empty summary"

    t = time.time()
    describer = SceneDescriber(Config.FLORENCE_MODEL)
    description = describer.describe(image)
    print(f"OK  detail model ({Config.FLORENCE_MODEL}): {description!r}  [{time.time() - t:.1f}s incl. loading]")
    assert len(description.split()) >= 5, "description too short"

    # Florence-2 OCR alone can hallucinate stock-photo watermarks on empty images, so the app only reads
    # text when the description mentions some; check that gate keeps a blank image silent
    blank = describer.describe(Image.new("RGB", (640, 480), "white"))
    assert not describer.mentions_text(blank), f"blank image would trigger text reading: {blank!r}"
    speech = build_speech(True, "A cat.", ["EXIT"])
    assert speech.startswith("This photo looks blurry") and "reads: EXIT." in speech
    print("OK  text reading and speech assembly")
    print("\nAll checks passed. Start the app with:  python app.py")


if __name__ == "__main__":
    main()
