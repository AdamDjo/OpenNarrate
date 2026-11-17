"""Render a generated two-shot project twice and verify that the shot cache is reused."""

import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "Outils"
sys.path.insert(0, str(TOOLS))
from commun import FFMPEG, FFPROBE


def run(*args):
    subprocess.run(args, check=True, cwd=ROOT)


def main():
    name = f"smoke-{uuid.uuid4().hex}"
    output = ROOT / "A_publier" / f"{name}.mp4"
    with tempfile.TemporaryDirectory(dir=ROOT / "Episodes", prefix="test-") as directory:
        project = Path(directory)
        narration = project / "voix" / "narration"
        narration.mkdir(parents=True)
        for number, color in enumerate(("blue", "green"), 1):
            run(FFMPEG, "-v", "error", "-f", "lavfi", "-i", f"color=c={color}:s=320x180",
                "-frames:v", "1", str(project / f"{number}.png"))
            run(FFMPEG, "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                "-af", "volume=3", str(narration / f"b{number:02d}.wav"))

        blocks = [{"n": i, "mots": 1, "chapitre": "", "texte": "Hello", "couche": "FEU"} for i in (1, 2)]
        settings = {
            "alias": {"A": "1.png", "B": "2.png"},
            "blocs": {"1": ["A"], "2": ["B"]},
            "centres": {},
            "zoom_images": False,
            "titre_apres_bloc": 0,
            "musiques": [],
            "bruitages": [],
        }
        (project / "blocs.json").write_text(json.dumps(blocks), encoding="utf-8")
        (project / "montage_images.json").write_text(json.dumps(settings), encoding="utf-8")

        def step(command, *arguments):
            run(sys.executable, str(TOOLS / "fabriquer.py"), command, project.name, *arguments)

        def cache_state():
            return {p.name: p.stat().st_mtime_ns for p in (project / ".render-cache").glob("*.mp4")}

        try:
            step("check")
            step("plan", name)
            step("render")
            cache = cache_state()
            assert len(cache) == 2, cache
            step("render")
            assert cache_state() == cache
            run(FFPROBE, "-v", "error", "-show_entries", "format=duration", str(output))
            step("verify", "--report")
            report = json.loads((project / "verification.json").read_text(encoding="utf-8"))
            assert report["status"] == "pass", report
            ranges = report["voice_ranges"]
            assert [item["block"] for item in ranges] == ["b01", "b02"], ranges
            assert 0 < ranges[0]["start_seconds"] < ranges[0]["end_seconds"] < ranges[1]["start_seconds"], ranges
            run(FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=320x180",
                "-frames:v", "1", str(project / "2.png"))
            step("render")
            updated = cache_state()
            assert len(updated) == 3, updated
            assert all(updated.get(path) == timestamp for path, timestamp in cache.items())
            print("Smoke test passed. Both shots were reused, then only the changed shot was regenerated.")
        finally:
            output.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
