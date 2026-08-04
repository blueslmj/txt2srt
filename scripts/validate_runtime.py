#!/usr/bin/env python
"""Validate the installed txt2srt runtime and selected hardware profile."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from project_paths import configure_project_environment


configure_project_environment()
import importlib.metadata as metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expect-cuda",
        action="store_true",
        help="Fail when the selected PyTorch build cannot access CUDA.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    import ctranslate2
    import faster_whisper  # noqa: F401 - import is the validation
    import gradio  # noqa: F401 - import is the validation
    import stable_whisper  # noqa: F401 - import is the validation
    import torch

    available = bool(torch.cuda.is_available())
    print(f"Python/Torch: {torch.__version__}")
    print(f"stable-ts: {metadata.version('stable-ts')}")
    print(f"faster-whisper: {metadata.version('faster-whisper')}")
    print(f"CUDA available: {available}")

    if args.expect_cuda and not available:
        raise SystemExit(
            "The NVIDIA profile is installed but CUDA is unavailable. "
            "Update the driver or install the CPU profile."
        )

    if available:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"Capability: {torch.cuda.get_device_capability(0)}")
        tensor = torch.randn((256, 256), device="cuda", dtype=torch.float16)
        _ = tensor @ tensor
        print("CUDA FP16 smoke: OK")

    ctranslate_devices = ctranslate2.get_cuda_device_count()
    print(f"CTranslate2 CUDA devices: {ctranslate_devices}")
    if args.expect_cuda and ctranslate_devices < 1:
        raise SystemExit("CTranslate2 cannot access the selected NVIDIA GPU.")

    print("Runtime imports: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
