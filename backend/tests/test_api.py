"""API tests. They only rely on the committed fingerspelling images, so they run without sign clips."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_reports_alphabet():
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["fingerspelling"]["letters_with_assets"] == 26


def test_alphabet_lists_26_letters():
    letters = client.get("/api/alphabet").json()["letters"]
    assert len(letters) == 26 and all(l["has_asset"] for l in letters)


def test_empty_input_is_rejected():
    r = client.post("/api/translate", json={"text": "   "})
    assert r.status_code == 400


def test_too_long_input_is_rejected():
    assert client.post("/api/translate", json={"text": "a " * 1000}).status_code == 400


def test_translate_renders_a_video_with_synced_timeline():
    r = client.post("/api/translate", json={"text": "Zebra"})
    assert r.status_code == 200
    body = r.json()
    assert body["timeline"] and body["timeline"][0]["kind"] in ("sign", "spell")
    # timeline is contiguous and ends where the video ends
    for a, b in zip(body["timeline"], body["timeline"][1:]):
        assert abs(a["end"] - b["start"]) < 1e-6
    assert abs(body["timeline"][-1]["end"] - body["duration"]) < 1e-6
    assert client.get(body["video_url"]).status_code == 200
    assert client.get(body["srt_url"]).status_code == 200


def test_input_with_no_signable_words_returns_no_video():
    body = client.post("/api/translate", json={"text": "the a of"}).json()
    assert body["video_url"] is None and body["timeline"] == []
