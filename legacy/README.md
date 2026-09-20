# Legacy prototype

The original SignStory prototype (CLI and Tkinter UI, exact-match word lookup, FFmpeg concatenation).
Kept for reference; the current system lives in `backend/` and `frontend/`.

Run from the repository root so the relative paths (`asl_videos_std/`, `vocab.txt`) resolve:

```bash
python legacy/run_system.py     # command line
python legacy/ui_tkinter.py     # desktop UI
```

These scripts need FFmpeg on your PATH and the sign clips (see the main README). `test_concat.py` and
`evaluation/` import a `metrics` module that was never part of this repository.
