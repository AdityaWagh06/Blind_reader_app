"""API tests with stand-in models, so they run in seconds without downloading anything."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app as server
from utils.scene_describer import SceneDescriber


class FakeCaptioner:
    def __init__(self, p_unreadable):
        self.p = p_unreadable
        self.seen_size = None

    def unreadable_probability(self, image):
        self.seen_size = image.size
        return self.p

    def generate_caption(self, image, avoid_unreadable=False):
        return "a bottle of medicine on a table."


class FakeDescriber:
    def __init__(self, description="A white label with black text on a bottle."):
        self.description = description
        self.ocr_calls = 0

    def describe(self, image):
        return self.description

    def read_text(self, image):
        self.ocr_calls += 1
        return ["PARACETAMOL 500 mg"]

    mentions_text = staticmethod(SceneDescriber.mentions_text)


@pytest.fixture
def client(monkeypatch):
    # no background model loading during tests
    monkeypatch.setattr(server, "load_models", lambda: None)
    monkeypatch.setattr(server, "model_error", None)
    server.models.clear()
    with TestClient(server.app) as c:
        yield c
    server.models.clear()


def png(size=(64, 48), exif_rotate=False):
    buf = io.BytesIO()
    img = Image.new("RGB", size, "white")
    if exif_rotate:
        exif = Image.Exif()
        exif[0x0112] = 6  # orientation: rotate 90 degrees
        img.save(buf, "JPEG", exif=exif)
    else:
        img.save(buf, "PNG")
    return buf.getvalue()


def post(client, data, name="photo.png"):
    return client.post("/api/describe", files={"image": (name, data, "image/png")})


def use_models(p_unreadable=0.1, **describer_kwargs):
    server.models["captioner"] = FakeCaptioner(p_unreadable)
    server.models["describer"] = FakeDescriber(**describer_kwargs)


def test_status_reports_loading(client):
    assert client.get("/api/status").json()["ready"] is False


def test_describe_waits_for_models(client):
    assert post(client, png()).status_code == 503


def test_rejects_non_image(client):
    use_models()
    assert post(client, b"not an image").status_code == 415


def test_rejects_too_large(client, monkeypatch):
    use_models()
    monkeypatch.setattr(server.Config, "MAX_FILE_SIZE_MB", 1)
    assert post(client, b"x" * (1024 * 1024 + 1)).status_code == 413


def test_clear_photo_reads_text(client):
    use_models(p_unreadable=0.1)
    body = post(client, png()).json()
    assert body["unclear"] is False
    assert body["summary"] == "A bottle of medicine on a table."
    assert body["text_lines"] == ["PARACETAMOL 500 mg"]
    assert body["speech"].endswith("The text in the image reads: PARACETAMOL 500 mg.")


def test_unclear_photo_warns_and_skips_text(client):
    use_models(p_unreadable=0.9)
    body = post(client, png()).json()
    assert body["unclear"] is True and body["retake_tip"]
    assert body["text_lines"] == []
    assert server.models["describer"].ocr_calls == 0
    assert body["speech"].startswith("This photo looks blurry")


def test_no_text_mentioned_skips_ocr(client):
    use_models(description="A cat sleeping on a red couch.")
    assert post(client, png()).json()["text_lines"] == []
    assert server.models["describer"].ocr_calls == 0


def test_exif_rotation_applied(client):
    use_models()
    assert post(client, png((64, 48), exif_rotate=True), "photo.jpg").status_code == 200
    assert server.models["captioner"].seen_size == (48, 64)


def test_eval_results_served(client):
    body = client.get("/api/eval").json()
    assert "calibration" in body


def test_busy_server_answers_503(client, monkeypatch):
    use_models()
    monkeypatch.setattr(server.Config, "QUEUE_TIMEOUT_S", 0.01)
    server.model_lock.acquire()
    try:
        assert post(client, png()).status_code == 503
    finally:
        server.model_lock.release()


def test_model_crash_answers_500_and_frees_lock(client):
    use_models()

    def boom(image):
        raise RuntimeError("out of memory")

    server.models["describer"].describe = boom
    res = post(client, png())
    assert res.status_code == 500 and "out of memory" not in res.text  # no internals leaked
    assert server.model_lock.acquire(blocking=False)
    server.model_lock.release()
