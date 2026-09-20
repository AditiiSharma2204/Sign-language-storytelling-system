# Build the UI (if needed) and start SignStory on http://127.0.0.1:8000
$root = $PSScriptRoot
if (-not (Test-Path "$root\frontend\dist")) {
    Push-Location "$root\frontend"; npm install; npm run build; Pop-Location
}
Push-Location "$root\backend"
python -m uvicorn app.main:app --port 8000
Pop-Location
