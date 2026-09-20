"""FastAPI application: JSON API, media files and (optionally) the built React UI."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import fingerspell, pipeline
from .config import AUTO_SIGNS_DIR, FRONTEND_DIST, OUTPUT_DIR, SIGNS_DIR
from .lexicon import SYNONYMS

app = FastAPI(title="SignStory API", version="2.0.0",
              description="English text to ASL gloss and sign-language video.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


class TranslateRequest(BaseModel):
    text: str


@app.get("/api/health")
def health():
    return {"status": "ok", "vocab_size": len(pipeline.VOCAB), "fingerspelling": fingerspell.alphabet_status()}


@app.get("/api/alphabet")
def alphabet():
    status = fingerspell.alphabet_status()
    letters = [{"letter": c, "url": f"/media/out/letters/{fingerspell.letter_clip(c).name}",
                "has_asset": c not in status["missing"]} for c in fingerspell.ALPHABET]
    return {"letters": letters, **status}


@app.get("/api/vocab")
def vocab():
    reverse: dict[str, list[str]] = {}
    for alias, target in SYNONYMS.items():
        reverse.setdefault(target, []).append(alias)
    words = sorted(pipeline.VOCAB)
    return {
        "count": len(words),
        "words": [{"word": w, "source": pipeline.sign_source(w),
                   "url": ("/media/signs/" if pipeline.sign_source(w) == "curated" else "/media/signs-auto/") + f"{w}.mp4",
                   "aliases": sorted(reverse.get(w, []))} for w in words],
    }


@app.post("/api/translate")
def translate(req: TranslateRequest):
    try:
        return pipeline.translate(req.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


SIGNS_DIR.mkdir(exist_ok=True)
AUTO_SIGNS_DIR.mkdir(exist_ok=True)
app.mount("/media/signs", StaticFiles(directory=SIGNS_DIR), name="signs")
app.mount("/media/signs-auto", StaticFiles(directory=AUTO_SIGNS_DIR), name="signs-auto")
app.mount("/media/out", StaticFiles(directory=OUTPUT_DIR), name="out")

# Serve the production React build when it exists (single-process deployment).
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = FRONTEND_DIST / path
        return FileResponse(candidate if path and candidate.is_file() else FRONTEND_DIST / "index.html")
