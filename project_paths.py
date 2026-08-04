#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Project-local storage paths used by installers and runtime entry points."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Dict


PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
FASTER_WHISPER_MODELS_DIR = MODELS_DIR / "faster-whisper"
OPENAI_WHISPER_MODELS_DIR = MODELS_DIR / "openai-whisper"
HUGGINGFACE_HOME_DIR = MODELS_DIR / "huggingface"
TORCH_HOME_DIR = MODELS_DIR / "torch"
RUNTIME_DIR = PROJECT_ROOT / ".runtime"
TEMP_DIR = RUNTIME_DIR / "temp"
GRADIO_TEMP_DIR = RUNTIME_DIR / "gradio"


def project_environment() -> Dict[str, str]:
    """Return download/cache environment variables pinned inside the project."""
    return {
        "TXT2SRT_PROJECT_ROOT": str(PROJECT_ROOT),
        "TXT2SRT_MODELS_DIR": str(MODELS_DIR),
        "TXT2SRT_WHISPER_DOWNLOAD_ROOT": str(OPENAI_WHISPER_MODELS_DIR),
        "HF_HOME": str(HUGGINGFACE_HOME_DIR),
        "HF_HUB_CACHE": str(FASTER_WHISPER_MODELS_DIR),
        "HUGGINGFACE_HUB_CACHE": str(FASTER_WHISPER_MODELS_DIR),
        "HF_ASSETS_CACHE": str(MODELS_DIR / "huggingface-assets"),
        "HF_XET_CACHE": str(MODELS_DIR / "huggingface-xet"),
        "TORCH_HOME": str(TORCH_HOME_DIR),
        "XDG_CACHE_HOME": str(MODELS_DIR / "misc"),
        "GRADIO_TEMP_DIR": str(GRADIO_TEMP_DIR),
        "NUMBA_CACHE_DIR": str(RUNTIME_DIR / "numba"),
        "MPLCONFIGDIR": str(RUNTIME_DIR / "matplotlib"),
        "TEMP": str(TEMP_DIR),
        "TMP": str(TEMP_DIR),
    }


def configure_project_environment() -> None:
    """Force application-created files into folders below the project root."""
    for directory in (
        MODELS_DIR,
        FASTER_WHISPER_MODELS_DIR,
        OPENAI_WHISPER_MODELS_DIR,
        HUGGINGFACE_HOME_DIR,
        TORCH_HOME_DIR,
        TEMP_DIR,
        GRADIO_TEMP_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    # Deliberately overwrite user-level cache variables. This application promises
    # that its downloaded models and temporary files remain beside the project.
    os.environ.update(project_environment())
    tempfile.tempdir = str(TEMP_DIR)
