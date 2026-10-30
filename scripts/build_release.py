#!/usr/bin/env python3
"""
scripts/build_release.py
Builds submission-ready release ZIP from git tracked files (`git ls-files`) only.
Enforces strict secret and hygiene checks:
- Fails if any file matches .env*, *.db, or __pycache__
- Fails if any text file contains a 32-hex character secret next to 'KEY'
- Writes the SHA-256 hash to KilnLink_Hackathon_Release.zip.sha256
"""
import os
import re
import sys
import hashlib
import zipfile
import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT_ZIP = REPO_ROOT / "KilnLink_Hackathon_Release.zip"
OUTPUT_SHA = REPO_ROOT / "KilnLink_Hackathon_Release.zip.sha256"

DENY_PATTERNS = [
    re.compile(r'(^|[/\\])\.env', re.IGNORECASE),
    re.compile(r'\.env', re.IGNORECASE),
    re.compile(r'\.db$', re.IGNORECASE),
    re.compile(r'__pycache__', re.IGNORECASE),
]

KEY_SECRET_PATTERN = re.compile(r'KEY\s*[:=]\s*["\']?[a-f0-9]{32}["\']?', re.IGNORECASE)

TEXT_EXTENSIONS = {
    ".py", ".txt", ".md", ".json", ".yaml", ".yml", ".html",
    ".js", ".css", ".csv", ".toml", ".sh", ".bat", ".ps1"
}


def check_file(rel_path: str) -> str:
    """
    Validates a file path and content against secret leak rules.
    Returns error string if forbidden, or empty string if clean.
    """
    normalized = rel_path.replace("\\", "/")

    # Check deny patterns (except harmless .env.example which is allowed)
    if normalized.endswith(".env.example"):
        pass
    else:
        for pat in DENY_PATTERNS:
            if pat.search(normalized):
                return f"Forbidden file pattern ({pat.pattern}): {rel_path}"

    abs_path = REPO_ROOT / rel_path
    if not abs_path.is_file():
        return ""

    # Content scan for text files
    if abs_path.suffix.lower() in TEXT_EXTENSIONS or abs_path.name.startswith("."):
        try:
            content = abs_path.read_text(encoding="utf-8", errors="replace")
            # Don't flag placeholder text in .env.example
            if "YOUR_NASA_FIRMS_MAP_KEY_HERE" in content and rel_path == ".env.example":
                pass
            elif KEY_SECRET_PATTERN.search(content):
                return f"Contains key-like secret adjacent to KEY: {rel_path}"
        except Exception:
            pass

    return ""


def get_tracked_files() -> list:
    """Retrieves list of files tracked by git."""
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True
        )
        files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return files
    except Exception as e:
        print(f"Error running git ls-files: {e}")
        return []


def build_release() -> bool:
    print("=" * 60)
    print("Building Submission Release ZIP...")
    print(f"Root: {REPO_ROOT}")
    files = get_tracked_files()
    if not files:
        print("ERROR: No tracked files found via git ls-files.")
        return False

    violations = []
    clean_files = []

    for f in files:
        err = check_file(f)
        if err:
            violations.append(err)
        else:
            clean_files.append(f)

    if violations:
        print("RELEASE BUILD FAILED — Hygiene / Secret Violations:")
        for v in violations:
            print(f"  [X] {v}")
        return False

    # Build ZIP archive
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in clean_files:
            abs_p = REPO_ROOT / rel
            if abs_p.is_file():
                zf.write(abs_p, rel)

    # Compute and record SHA-256
    sha256 = hashlib.sha256(OUTPUT_ZIP.read_bytes()).hexdigest()
    OUTPUT_SHA.write_text(f"{sha256}  {OUTPUT_ZIP.name}\n", encoding="utf-8")

    print(f"Successfully packaged {len(clean_files)} files into {OUTPUT_ZIP.name}")
    print(f"SHA-256: {sha256}")
    print("Release build passed all hygiene checks.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = build_release()
    sys.exit(0 if success else 1)

