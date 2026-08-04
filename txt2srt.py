#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Align an accurate transcript to audio and write SRT subtitles.

The module deliberately keeps model imports lazy. Text segmentation, alignment,
timeline cleanup, and SRT rendering can therefore be tested without installing
the full speech-recognition stack.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import threading
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from project_paths import (
    FASTER_WHISPER_MODELS_DIR,
    OPENAI_WHISPER_MODELS_DIR,
    configure_project_environment,
)


configure_project_environment()


SUPPORTED_MODELS = (
    "tiny",
    "base",
    "small",
    "medium",
    "large",
    "large-v2",
    "large-v3",
)
SUPPORTED_DEVICES = ("auto", "cpu", "cuda")
MAX_DTW_CELLS = 8_000_000
ProgressCallback = Callable[[float, str], None]


class Txt2SrtError(RuntimeError):
    """Base exception for user-facing txt2srt failures."""


class InputValidationError(Txt2SrtError, ValueError):
    """Raised when an input cannot be processed safely."""


class DependencyError(Txt2SrtError):
    """Raised when the optional speech-recognition stack is unavailable."""


def format_timestamp(seconds: float) -> str:
    """Convert seconds to a non-negative SRT timestamp."""
    total_milliseconds = round(max(0.0, float(seconds)) * 1000)
    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def split_text_into_segments(text: str, max_chars: int = 30) -> List[str]:
    """Split transcript text into readable subtitle-sized segments.

    Explicit line breaks take precedence, followed by sentence punctuation,
    secondary punctuation, and finally a hard character limit.
    """
    if not isinstance(text, str) or not text.strip():
        return []
    if not 1 <= int(max_chars) <= 500:
        raise InputValidationError("每条字幕字数必须在 1 到 500 之间")

    segments: List[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        parts = re.split(r"([。！？；.!?;])", line)
        current = ""
        for index in range(0, len(parts), 2):
            sentence = parts[index]
            punctuation = parts[index + 1] if index + 1 < len(parts) else ""
            if not sentence.strip() and not punctuation:
                continue
            candidate = sentence + punctuation
            if current and len(current + candidate) <= max_chars:
                current += candidate
            elif not current and len(candidate) <= max_chars:
                current = candidate
            else:
                if current.strip():
                    segments.append(current.strip())
                split_parts = _split_long_sentence(candidate, max_chars)
                segments.extend(part.strip() for part in split_parts[:-1] if part.strip())
                current = split_parts[-1] if split_parts else ""

        if current.strip():
            segments.append(current.strip())

    return segments


def _split_long_sentence(sentence: str, max_chars: int) -> List[str]:
    if len(sentence) <= max_chars:
        return [sentence]

    result: List[str] = []
    parts = re.split(r"([，,、：:])", sentence)
    current = ""
    for index in range(0, len(parts), 2):
        text = parts[index]
        punctuation = parts[index + 1] if index + 1 < len(parts) else ""
        candidate = text + punctuation
        if not candidate:
            continue
        if len(current + candidate) <= max_chars:
            current += candidate
            continue
        if current.strip():
            result.append(current.strip())
        hard_parts = _force_split_by_chars(candidate, max_chars)
        result.extend(part for part in hard_parts[:-1] if part)
        current = hard_parts[-1] if hard_parts else ""

    if current.strip():
        result.append(current.strip())
    return result or [sentence]


def _force_split_by_chars(text: str, max_chars: int) -> List[str]:
    result: List[str] = []
    remaining = text.strip()
    while len(remaining) > max_chars:
        split_at = max_chars
        lower_bound = max(1, max_chars - 10)
        for index in range(max_chars - 1, lower_bound - 1, -1):
            if remaining[index] in "，,、：: 　":
                split_at = index + 1
                break
        result.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        result.append(remaining)
    return result


def normalize_for_alignment(text: str) -> str:
    """Normalize text while retaining only characters useful for alignment."""
    normalized = unicodedata.normalize("NFKC", str(text)).casefold()
    return "".join(
        character
        for character in normalized
        if not character.isspace()
        and not unicodedata.category(character).startswith(("P", "S"))
    )


def remove_punctuation(text: str) -> str:
    """Backward-compatible alias used by integrations based on the reference project."""
    return normalize_for_alignment(text)


def read_text_file(path: str) -> str:
    """Read common Chinese/UTF text encodings with actionable errors."""
    file_path = Path(path)
    if not file_path.is_file():
        raise InputValidationError(f"文本文件不存在: {path}")
    errors: List[str] = []
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise InputValidationError(
        "无法读取文本文件，请将文件保存为 UTF-8 或 GB18030 编码。"
        f" 详情: {'; '.join(errors)}"
    )


def validate_inputs(audio_path: str, text: str, max_chars: int) -> None:
    audio = Path(audio_path)
    if not audio.is_file():
        raise InputValidationError(f"音频文件不存在: {audio_path}")
    if not isinstance(text, str) or not text.strip():
        raise InputValidationError("文本内容为空，请输入文稿或上传非空文本文件")
    if not 1 <= int(max_chars) <= 500:
        raise InputValidationError("每条字幕字数必须在 1 到 500 之间")


def _import_torch() -> Any:
    try:
        import torch
    except ImportError as exc:
        raise DependencyError(
            "缺少 PyTorch，无法执行语音识别。Windows 请先运行 setup.bat"
        ) from exc
    return torch


def resolve_device(device: str = "auto") -> str:
    """Resolve auto/cpu/cuda and reject an unavailable explicit CUDA request."""
    requested = str(device or "auto").strip().lower()
    if requested not in SUPPORTED_DEVICES:
        raise InputValidationError(
            f"不支持的运行设备: {device}（可选: {', '.join(SUPPORTED_DEVICES)}）"
        )
    torch = _import_torch()
    cuda_available = bool(torch.cuda.is_available())
    if requested == "cuda" and not cuda_available:
        raise InputValidationError("CUDA 当前不可用，请选择“自动选择”或 CPU")
    return "cuda" if requested == "auto" and cuda_available else (
        "cpu" if requested == "auto" else requested
    )


def find_local_faster_whisper_model(model_name: str) -> Optional[str]:
    """Find a complete faster-whisper snapshot in project-local storage."""
    cache_roots: List[Path] = []
    explicit_cache = os.environ.get("HUGGINGFACE_HUB_CACHE")
    hf_hub_cache = os.environ.get("HF_HUB_CACHE")
    hf_home = os.environ.get("HF_HOME")
    if explicit_cache:
        cache_roots.append(Path(explicit_cache))
    if hf_hub_cache:
        cache_roots.append(Path(hf_hub_cache))
    if hf_home:
        cache_roots.append(Path(hf_home) / "hub")
    cache_roots.append(FASTER_WHISPER_MODELS_DIR)

    model_folder = f"models--Systran--faster-whisper-{model_name}"
    for cache_root in dict.fromkeys(cache_roots):
        snapshots = cache_root / model_folder / "snapshots"
        if not snapshots.is_dir():
            continue
        candidates = sorted(
            (item for item in snapshots.iterdir() if item.is_dir()),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for candidate in candidates:
            if (candidate / "model.bin").is_file() and (candidate / "config.json").is_file():
                return str(candidate)
    return None


_model_cache: Dict[Tuple[str, str, str], Tuple[Any, bool, str]] = {}
_model_cache_lock = threading.Lock()


def get_whisper_model(
    model_name: str,
    device: str = "auto",
    backend: str = "auto",
) -> Tuple[Any, bool, str]:
    """Load and cache a Whisper model, preferring faster-whisper and local files."""
    model_name = str(model_name).strip().lower()
    if model_name not in SUPPORTED_MODELS:
        raise InputValidationError(
            f"不支持的 Whisper 模型: {model_name}（可选: {', '.join(SUPPORTED_MODELS)}）"
        )
    runtime_device = resolve_device(device)
    backend = str(backend or "auto").strip().lower()
    if backend not in ("auto", "faster", "openai"):
        raise InputValidationError("识别后端仅支持 auto、faster 或 openai")

    cache_key = (model_name, runtime_device, backend)
    with _model_cache_lock:
        if cache_key in _model_cache:
            return _model_cache[cache_key]

        try:
            import stable_whisper
        except ImportError as exc:
            raise DependencyError(
                "缺少 stable-ts，无法加载 Whisper。Windows 请先运行 setup.bat"
            ) from exc

        load_errors: List[str] = []
        if backend in ("auto", "faster"):
            source = find_local_faster_whisper_model(model_name) or model_name
            compute_type = "float16" if runtime_device == "cuda" else "int8"
            try:
                model = stable_whisper.load_faster_whisper(
                    source,
                    device=runtime_device,
                    compute_type=compute_type,
                    download_root=str(FASTER_WHISPER_MODELS_DIR),
                )
                loaded = (model, True, "faster-whisper")
                _model_cache[cache_key] = loaded
                return loaded
            except Exception as exc:  # model loaders expose backend-specific errors
                load_errors.append(f"faster-whisper: {exc}")
                if backend == "faster":
                    raise Txt2SrtError("Faster-Whisper 模型加载失败: " + str(exc)) from exc

        try:
            model = stable_whisper.load_model(
                model_name,
                device=runtime_device,
                download_root=str(OPENAI_WHISPER_MODELS_DIR),
            )
            loaded = (model, False, "openai-whisper")
            _model_cache[cache_key] = loaded
            return loaded
        except Exception as exc:
            load_errors.append(f"openai-whisper: {exc}")
            raise Txt2SrtError(
                "Whisper 模型加载失败。请检查网络、项目 models 目录和可用磁盘空间。"
                f" 详情: {'; '.join(load_errors)}"
            ) from exc


def clear_model_cache() -> None:
    """Release cached model references, primarily useful for tests or device changes."""
    with _model_cache_lock:
        _model_cache.clear()


def _notify(callback: Optional[ProgressCallback], progress: float, message: str) -> None:
    print(message)
    if callback:
        callback(max(0.0, min(1.0, float(progress))), message)


def _normalize_language(language: Optional[str]) -> Optional[str]:
    if language is None:
        return None
    normalized = str(language).strip().lower()
    return None if normalized in ("", "auto", "none", "自动检测") else normalized


def transcribe_audio(
    audio_path: str,
    model_name: str = "small",
    language: Optional[str] = "zh",
    device: str = "auto",
    progress_callback: Optional[ProgressCallback] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Transcribe audio into timestamped recognition segments."""
    runtime_device = resolve_device(device)
    _notify(progress_callback, 0.08, f"运行设备：{runtime_device.upper()}")
    _notify(progress_callback, 0.14, f"加载 Whisper 模型：{model_name}")
    model, is_faster, backend_name = get_whisper_model(model_name, runtime_device)

    transcribe_kwargs: Dict[str, Any] = {
        "word_timestamps": True,
        "verbose": False,
        "regroup": True,
        "beam_size": 1,
        "temperature": 0,
    }
    normalized_language = _normalize_language(language)
    if normalized_language:
        transcribe_kwargs["language"] = normalized_language
    if is_faster:
        transcribe_kwargs.update(
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )

    _notify(progress_callback, 0.28, f"识别音频（{backend_name}）")
    try:
        result = model.transcribe(audio_path, **transcribe_kwargs)
    except TypeError as exc:
        # Older stable-ts/faster-whisper combinations may not expose VAD tuning.
        if "vad_parameters" not in str(exc):
            raise
        transcribe_kwargs.pop("vad_parameters", None)
        result = model.transcribe(audio_path, **transcribe_kwargs)
    except Exception as exc:
        raise Txt2SrtError(
            f"音频识别失败: {exc}。请确认音频可解码，并检查 FFmpeg 是否可用。"
        ) from exc

    raw_segments = getattr(result, "segments", None)
    if raw_segments is None and isinstance(result, dict):
        raw_segments = result.get("segments", [])

    segments: List[Dict[str, Any]] = []
    for raw_segment in raw_segments or []:
        if isinstance(raw_segment, dict):
            start = raw_segment.get("start", 0.0)
            end = raw_segment.get("end", start)
            recognized_text = raw_segment.get("text", "")
        else:
            start = getattr(raw_segment, "start", 0.0)
            end = getattr(raw_segment, "end", start)
            recognized_text = getattr(raw_segment, "text", "")
        recognized_text = str(recognized_text).strip()
        if recognized_text and float(end) > float(start):
            segments.append(
                {"start": float(start), "end": float(end), "text": recognized_text}
            )

    if not segments:
        raise Txt2SrtError("未识别到有效语音，请检查音频是否包含清晰人声")
    _notify(progress_callback, 0.5, f"识别到 {len(segments)} 个语音段落")
    return segments, {
        "model": model_name,
        "device": runtime_device,
        "backend": backend_name,
        "language": normalized_language or "auto",
    }


def _fill_character_mapping(
    mapping: List[Optional[int]], recognized_count: int
) -> List[int]:
    """Fill unmatched character positions by monotonic linear interpolation."""
    user_count = len(mapping)
    if user_count == 0 or recognized_count == 0:
        return []
    anchors = [(index, value) for index, value in enumerate(mapping) if value is not None]
    if not anchors:
        if user_count == 1:
            return [0]
        return [
            round(index * (recognized_count - 1) / (user_count - 1))
            for index in range(user_count)
        ]

    if anchors[0][0] != 0:
        anchors.insert(0, (0, 0))
    if anchors[-1][0] != user_count - 1:
        anchors.append((user_count - 1, recognized_count - 1))

    filled: List[Optional[int]] = list(mapping)
    for (left_index, left_value), (right_index, right_value) in zip(anchors, anchors[1:]):
        width = right_index - left_index
        for index in range(left_index, right_index + 1):
            if filled[index] is None:
                ratio = 0.0 if width == 0 else (index - left_index) / width
                filled[index] = round(left_value + ratio * (right_value - left_value))

    result: List[int] = []
    last_value = 0
    for value in filled:
        bounded = max(last_value, min(recognized_count - 1, int(value or 0)))
        result.append(bounded)
        last_value = bounded
    return result


def _sequence_character_mapping(user_text: str, recognized_text: str) -> List[int]:
    matcher = SequenceMatcher(None, user_text, recognized_text, autojunk=False)
    mapping: List[Optional[int]] = [None] * len(user_text)
    for user_start, recognized_start, size in matcher.get_matching_blocks():
        for offset in range(size):
            mapping[user_start + offset] = recognized_start + offset
    return _fill_character_mapping(mapping, len(recognized_text))


def _dtw_character_mapping(user_text: str, recognized_text: str) -> Optional[List[int]]:
    if len(user_text) * len(recognized_text) > MAX_DTW_CELLS:
        return None
    try:
        import numpy as np
        from dtw import dtw
    except ImportError:
        return None

    user_chars = np.asarray(list(user_text), dtype="U1")[:, None]
    recognized_chars = np.asarray(list(recognized_text), dtype="U1")[None, :]
    distance_matrix = (user_chars != recognized_chars).astype(np.float64)
    alignment = dtw(distance_matrix)

    sums = [0] * len(user_text)
    counts = [0] * len(user_text)
    for user_index, recognized_index in zip(alignment.index1, alignment.index2):
        user_index = int(user_index)
        sums[user_index] += int(recognized_index)
        counts[user_index] += 1
    mapping: List[Optional[int]] = [
        round(total / count) if count else None
        for total, count in zip(sums, counts)
    ]
    return _fill_character_mapping(mapping, len(recognized_text))


def _recognized_character_times(
    recognized_segments: Sequence[Dict[str, Any]],
) -> Tuple[str, List[Tuple[float, float]]]:
    recognized_text_parts: List[str] = []
    character_times: List[Tuple[float, float]] = []
    for segment in recognized_segments:
        clean_text = normalize_for_alignment(segment.get("text", ""))
        if not clean_text:
            continue
        start = max(0.0, float(segment.get("start", 0.0)))
        end = max(start, float(segment.get("end", start)))
        duration = end - start
        character_count = len(clean_text)
        recognized_text_parts.append(clean_text)
        for index in range(character_count):
            character_times.append(
                (
                    start + duration * index / character_count,
                    start + duration * (index + 1) / character_count,
                )
            )
    return "".join(recognized_text_parts), character_times


def match_user_text_to_timestamps(
    recognized_segments: Sequence[Dict[str, Any]],
    user_sentences: Sequence[str],
    diagnostics: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Map the accurate user transcript onto Whisper's recognition timeline."""
    if not recognized_segments:
        raise Txt2SrtError("Whisper 没有返回可用于对齐的语音段落")
    if not user_sentences:
        raise InputValidationError("文本切分后为空，无法生成字幕")

    recognized_text, character_times = _recognized_character_times(recognized_segments)
    user_text = "".join(normalize_for_alignment(sentence) for sentence in user_sentences)
    if not recognized_text:
        raise Txt2SrtError("识别结果仅包含标点或空白，无法建立时间轴")
    if not user_text:
        raise InputValidationError("文本不包含可对齐的文字或数字")

    length_difference = abs(len(user_text) - len(recognized_text)) / max(
        len(user_text), len(recognized_text), 1
    )
    similarity = SequenceMatcher(
        None, user_text, recognized_text, autojunk=False
    ).ratio()
    mapping = _dtw_character_mapping(user_text, recognized_text)
    algorithm = "dtw" if mapping is not None else "sequence"
    if mapping is None:
        mapping = _sequence_character_mapping(user_text, recognized_text)

    warnings: List[str] = []
    if length_difference > 0.2:
        warnings.append(
            f"文稿与识别文本的字符数相差 {length_difference:.0%}，请抽查字幕时间轴"
        )
    if similarity < 0.55:
        warnings.append(
            f"文稿与识别文本的相似度仅 {similarity:.0%}，两者可能不是同一内容"
        )
    if algorithm == "sequence" and len(user_text) * len(recognized_text) > MAX_DTW_CELLS:
        warnings.append("文本较长，已自动使用低内存对齐模式")

    if diagnostics is not None:
        diagnostics.update(
            recognized_chars=len(recognized_text),
            source_chars=len(user_text),
            length_difference=length_difference,
            similarity=similarity,
            alignment_algorithm=algorithm,
            warnings=warnings,
        )

    aligned: List[Dict[str, Any]] = []
    user_offset = 0
    for sentence in user_sentences:
        clean_sentence = normalize_for_alignment(sentence)
        if not clean_sentence:
            continue
        start_user_index = user_offset
        end_user_index = user_offset + len(clean_sentence) - 1
        start_recognized_index = mapping[start_user_index]
        end_recognized_index = mapping[end_user_index]
        start_time = character_times[start_recognized_index][0]
        end_time = character_times[end_recognized_index][1]
        aligned.append(
            {
                "start": start_time,
                "end": max(end_time, start_time + 0.5),
                "text": sentence.strip(),
            }
        )
        user_offset += len(clean_sentence)
    return aligned


def fix_overlapping_timestamps(
    segments: Sequence[Dict[str, Any]],
    min_duration: float = 0.5,
) -> List[Dict[str, Any]]:
    """Preserve transcript order while producing a non-overlapping timeline."""
    if not segments:
        return []
    starts: List[float] = []
    for segment in segments:
        start = max(0.0, float(segment.get("start", 0.0)))
        if starts and start <= starts[-1]:
            start = starts[-1] + 0.01
        starts.append(start)

    fixed: List[Dict[str, Any]] = []
    for index, segment in enumerate(segments):
        start = starts[index]
        raw_end = max(start, float(segment.get("end", start)))
        end = max(raw_end, start + max(0.01, min_duration))
        if index + 1 < len(starts):
            end = min(end, starts[index + 1])
        if end <= start:
            end = start + 0.01
        item = dict(segment)
        item.update(start=start, end=end, text=str(segment.get("text", "")).strip())
        fixed.append(item)
    return fixed


def optimize_subtitle_duration(
    segments: Sequence[Dict[str, Any]],
    max_extension: float = 0.5,
    subtitle_gap: float = 0.08,
    last_extension: float = 0.5,
) -> List[Dict[str, Any]]:
    """Fill short visual gaps without allowing subtitle overlap."""
    optimized = [dict(segment) for segment in segments]
    for index in range(len(optimized) - 1):
        current = optimized[index]
        next_segment = optimized[index + 1]
        gap = float(next_segment["start"]) - float(current["end"])
        extension = min(max_extension, gap - subtitle_gap)
        if extension > 0:
            current["end"] = float(current["end"]) + extension
    if optimized and last_extension > 0:
        optimized[-1]["end"] = float(optimized[-1]["end"]) + last_extension
    return optimized


def align_audio_text(
    audio_path: str,
    text: str,
    model_name: str = "small",
    use_gpu: Optional[bool] = None,
    max_chars: int = 30,
    language: Optional[str] = "zh",
    device: str = "auto",
    progress_callback: Optional[ProgressCallback] = None,
    diagnostics: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Align transcript text to audio while preserving the user's exact wording."""
    validate_inputs(audio_path, text, max_chars)
    if use_gpu is False and device == "auto":
        device = "cpu"

    recognized_segments, runtime_meta = transcribe_audio(
        audio_path,
        model_name=model_name,
        language=language,
        device=device,
        progress_callback=progress_callback,
    )
    _notify(progress_callback, 0.58, "切分字幕文本")
    user_sentences = split_text_into_segments(text, int(max_chars))
    _notify(progress_callback, 0.68, f"文稿切分为 {len(user_sentences)} 条字幕")

    report: Dict[str, Any] = {}
    _notify(progress_callback, 0.74, "对齐文稿与语音时间轴")
    aligned = match_user_text_to_timestamps(
        recognized_segments, user_sentences, diagnostics=report
    )
    _notify(progress_callback, 0.9, "修正字幕重叠与显示间隔")
    aligned = fix_overlapping_timestamps(aligned)
    aligned = optimize_subtitle_duration(aligned)
    if not aligned:
        raise Txt2SrtError("未能生成有效字幕段落")

    if diagnostics is not None:
        diagnostics.clear()
        diagnostics.update(runtime_meta)
        diagnostics.update(report)
        diagnostics["segment_count"] = len(aligned)
    _notify(progress_callback, 1.0, f"完成：生成 {len(aligned)} 条字幕")
    return aligned


def generate_srt_content(segments: Sequence[Dict[str, Any]]) -> str:
    """Render standard SRT content without touching the filesystem."""
    lines: List[str] = []
    for index, segment in enumerate(segments, 1):
        lines.extend(
            (
                str(index),
                f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}",
                str(segment.get("text", "")).strip(),
                "",
            )
        )
    return "\n".join(lines)


def generate_srt(segments: Sequence[Dict[str, Any]], output_path: str) -> str:
    """Write aligned segments to an SRT file and return its absolute path."""
    if not segments:
        raise InputValidationError("字幕段落为空，不会写入空 SRT 文件")
    target = Path(output_path).expanduser().resolve()
    if not target.parent.is_dir():
        raise InputValidationError(f"输出目录不存在: {target.parent}")
    target.write_text(generate_srt_content(segments), encoding="utf-8", newline="\n")
    print(f"SRT 字幕已保存: {target}")
    return str(target)


def generate_srt_from_audio(
    audio_path: str,
    text: str,
    output_path: Optional[str] = None,
    model_name: str = "small",
    language: Optional[str] = "zh",
    max_chars: int = 30,
    device: str = "auto",
    progress_callback: Optional[ProgressCallback] = None,
) -> Dict[str, Any]:
    """Unified service entry point inspired by the reference project."""
    target = output_path or str(Path(audio_path).with_suffix(".srt"))
    diagnostics: Dict[str, Any] = {}
    segments = align_audio_text(
        audio_path,
        text,
        model_name=model_name,
        max_chars=max_chars,
        language=language,
        device=device,
        progress_callback=progress_callback,
        diagnostics=diagnostics,
    )
    srt_path = generate_srt(segments, target)
    return {
        "srt_path": srt_path,
        "segments": segments,
        "meta": {key: value for key, value in diagnostics.items() if key != "warnings"},
        "warnings": diagnostics.get("warnings", []),
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="将音频与准确文稿对齐并生成 SRT 字幕")
    parser.add_argument("audio", help="输入音频文件路径")
    parser.add_argument("text", help="文本文件路径或直接文本内容")
    parser.add_argument("-o", "--output", help="输出 SRT 路径，默认与音频同名")
    parser.add_argument(
        "-m", "--model", default="small", choices=SUPPORTED_MODELS, help="Whisper 模型"
    )
    parser.add_argument(
        "-l", "--language", default="zh", help="语言代码；使用 auto 自动检测"
    )
    parser.add_argument(
        "-c", "--max-chars", type=int, default=30, help="每条字幕最大字数"
    )
    parser.add_argument(
        "--device", default="auto", choices=SUPPORTED_DEVICES, help="运行设备"
    )
    return parser


def _configure_windows_console() -> None:
    """Keep CLI status and error messages readable in legacy Windows terminals."""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: Optional[Sequence[str]] = None) -> int:
    _configure_windows_console()
    args = build_argument_parser().parse_args(argv)
    try:
        text_content = (
            read_text_file(args.text) if Path(args.text).is_file() else args.text
        )

        def print_progress(progress: float, message: str) -> None:
            print(f"[{progress:>5.0%}] {message}")

        result = generate_srt_from_audio(
            args.audio,
            text_content,
            output_path=args.output,
            model_name=args.model,
            language=args.language,
            max_chars=args.max_chars,
            device=args.device,
            progress_callback=print_progress,
        )
        print(f"完成：{result['srt_path']}")
        for warning in result["warnings"]:
            print(f"警告：{warning}")
        return 0
    except Txt2SrtError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
