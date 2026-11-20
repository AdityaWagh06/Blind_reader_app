"""Text-reading filters of SceneDescriber, tested without loading Florence-2."""
from PIL import Image

from utils.scene_describer import SceneDescriber


def describer_returning(result):
    d = SceneDescriber.__new__(SceneDescriber)  # skip __init__: no model download
    d._run = lambda image, task, max_new_tokens=256: result
    return d


def test_read_text_strips_tokens_and_noise():
    d = describer_returning({"labels": ["</s>PARACETAMOL 500 mg", "....", "EXP 03/2027</s>", "a."]})
    assert d.read_text(Image.new("RGB", (8, 8))) == ["PARACETAMOL 500 mg", "EXP 03/2027"]


def test_read_text_handles_no_labels():
    assert describer_returning({}).read_text(Image.new("RGB", (8, 8))) == []


def test_mentions_text():
    assert SceneDescriber.mentions_text("A bottle with a white label.")
    assert SceneDescriber.mentions_text("The sign reads EXIT.")
    assert not SceneDescriber.mentions_text("A cat sleeping on a red couch next to two remote controls.")
    # whole words only: "textured" or "signal" must not trigger OCR
    assert not SceneDescriber.mentions_text("A textured blanket near a signal lamp.")
