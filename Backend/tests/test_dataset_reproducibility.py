
import json

import pytest

from app.storage.dataset_loader import (
    DATASET_PATH,
    verify_dataset_integrity,
)


def test_dataset_integrity():
    assert verify_dataset_integrity() is True


def test_dataset_reproducible():
    assert verify_dataset_integrity() is True
    assert verify_dataset_integrity() is True


def test_modified_dataset_detected(tmp_path):
    original = DATASET_PATH.read_bytes()

    modified = tmp_path / DATASET_PATH.name
    modified.write_bytes(original + b"\n")

    with pytest.raises(ValueError, match="SHA-256"):
        verify_dataset_integrity(modified)


def test_wrong_dataset_version(tmp_path):
    manifest_path = DATASET_PATH.with_suffix(
        ".manifest.json"
    )

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    manifest["dataset_version"] = "999.0.0"

    modified_manifest = tmp_path / "modified.manifest.json"
    modified_manifest.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="version"):
        verify_dataset_integrity(
            manifest_path=modified_manifest
        )


def test_missing_manifest(tmp_path):
    missing = tmp_path / "missing.manifest.json"

    with pytest.raises(FileNotFoundError):
        verify_dataset_integrity(
            manifest_path=missing
        )
