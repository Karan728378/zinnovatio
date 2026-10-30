#!/usr/bin/env python3
"""
scripts/sync_frontend.py
Canonical synchronization tool for Parali Mitra / KilnLink frontend.
Source of truth: frontend/index.html
Targets: index.html (repo root) and paralimitra_app.html (repo root)

Copies the source of truth to the targets, calculates SHA-256 hashes,
and verifies byte-for-byte identity.
"""
import os
import sys
import hashlib
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE = os.path.join(REPO_ROOT, "frontend", "index.html")
TARGET_ROOT = os.path.join(REPO_ROOT, "index.html")
TARGET_APP = os.path.join(REPO_ROOT, "paralimitra_app.html")

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def sync_frontend() -> bool:
    if not os.path.exists(SOURCE):
        print(f"ERROR: Source file not found: {SOURCE}", file=sys.stderr)
        return False

    # Copy to targets
    shutil.copyfile(SOURCE, TARGET_ROOT)
    shutil.copyfile(SOURCE, TARGET_APP)

    source_hash = compute_sha256(SOURCE)
    root_hash = compute_sha256(TARGET_ROOT)
    app_hash = compute_sha256(TARGET_APP)

    print(f"Source: {SOURCE}")
    print(f"  SHA-256: {source_hash}")
    print(f"Target 1: {TARGET_ROOT}")
    print(f"  SHA-256: {root_hash}")
    print(f"Target 2: {TARGET_APP}")
    print(f"  SHA-256: {app_hash}")

    if source_hash == root_hash == app_hash:
        print("\nSUCCESS: All 3 frontend HTML files are synchronized and byte-identical.")
        return True
    else:
        print("\nFAILURE: Checksum mismatch after sync!", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = sync_frontend()
    sys.exit(0 if success else 1)

