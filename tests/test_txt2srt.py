import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import txt2srt
from project_paths import PROJECT_ROOT, project_environment


class TextSegmentationTests(unittest.TestCase):
    def test_explicit_lines_and_sentence_punctuation_are_preserved(self):
        result = txt2srt.split_text_into_segments(
            "第一行。第二句！\n第三行没有句号", max_chars=8
        )
        self.assertEqual(result, ["第一行。第二句！", "第三行没有句号"])

    def test_long_sentence_prefers_secondary_punctuation(self):
        result = txt2srt.split_text_into_segments(
            "这是较长的一段，应该优先在逗号处分开，然后继续。", max_chars=10
        )
        self.assertTrue(all(len(item) <= 10 for item in result))
        self.assertEqual("".join(result), "这是较长的一段，应该优先在逗号处分开，然后继续。")

    def test_unicode_normalization_improves_matching(self):
        self.assertEqual(txt2srt.normalize_for_alignment("ＡＢＣ，Hello！"), "abchello")


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.recognized = [
            {"start": 0.2, "end": 2.2, "text": "你好世界"},
            {"start": 2.5, "end": 5.0, "text": "这是测试"},
        ]

    def test_transcript_text_replaces_recognition_and_keeps_timeline(self):
        diagnostics = {}
        result = txt2srt.match_user_text_to_timestamps(
            self.recognized,
            ["你好，世界。", "这是测试！"],
            diagnostics,
        )
        self.assertEqual([item["text"] for item in result], ["你好，世界。", "这是测试！"])
        self.assertAlmostEqual(result[0]["start"], 0.2)
        self.assertAlmostEqual(result[-1]["end"], 5.0)
        self.assertGreaterEqual(diagnostics["similarity"], 0.99)
        self.assertEqual(diagnostics["warnings"], [])

    def test_large_text_difference_produces_warning(self):
        diagnostics = {}
        txt2srt.match_user_text_to_timestamps(
            self.recognized,
            ["这是一份完全不同而且长很多很多的文稿内容。"],
            diagnostics,
        )
        self.assertTrue(diagnostics["warnings"])

    def test_timeline_cleanup_preserves_order_and_removes_overlap(self):
        result = txt2srt.fix_overlapping_timestamps(
            [
                {"start": 1.0, "end": 3.0, "text": "一"},
                {"start": 2.0, "end": 2.1, "text": "二"},
                {"start": 2.0, "end": 4.0, "text": "三"},
            ]
        )
        self.assertEqual([item["text"] for item in result], ["一", "二", "三"])
        self.assertLessEqual(result[0]["end"], result[1]["start"])
        self.assertLessEqual(result[1]["end"], result[2]["start"])

    def test_align_pipeline_exposes_runtime_diagnostics(self):
        with tempfile.NamedTemporaryFile(suffix=".wav") as audio:
            diagnostics = {}
            with patch.object(
                txt2srt,
                "transcribe_audio",
                return_value=(
                    self.recognized,
                    {
                        "model": "small",
                        "device": "cpu",
                        "backend": "test-backend",
                        "language": "zh",
                    },
                ),
            ) as transcribe:
                result = txt2srt.align_audio_text(
                    audio.name,
                    "你好世界。这是测试！",
                    max_chars=5,
                    language="zh",
                    device="cpu",
                    diagnostics=diagnostics,
                )
        self.assertEqual(len(result), 2)
        self.assertEqual(diagnostics["backend"], "test-backend")
        self.assertEqual(diagnostics["segment_count"], 2)
        transcribe.assert_called_once()


class OutputAndCacheTests(unittest.TestCase):
    def test_download_and_temporary_locations_are_inside_project(self):
        project_root = PROJECT_ROOT.resolve()
        for name, value in project_environment().items():
            if name == "TXT2SRT_PROJECT_ROOT":
                continue
            self.assertTrue(
                Path(value).resolve().is_relative_to(project_root),
                f"{name} escaped the project: {value}",
            )
            self.assertEqual(os.environ.get(name), value)

    def test_timestamp_rounds_across_second_boundary(self):
        self.assertEqual(txt2srt.format_timestamp(1.9996), "00:00:02,000")
        self.assertEqual(txt2srt.format_timestamp(-2), "00:00:00,000")

    def test_srt_writer_returns_absolute_path(self):
        segments = [{"start": 0, "end": 1.25, "text": "字幕"}]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.srt"
            written = txt2srt.generate_srt(segments, str(output))
            self.assertEqual(written, str(output.resolve()))
            self.assertIn("00:00:00,000 --> 00:00:01,250", output.read_text("utf-8"))

    def test_local_model_lookup_honors_explicit_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = (
                Path(directory)
                / "models--Systran--faster-whisper-small"
                / "snapshots"
                / "revision"
            )
            snapshot.mkdir(parents=True)
            (snapshot / "model.bin").write_bytes(b"model")
            (snapshot / "config.json").write_text("{}", encoding="utf-8")
            with patch.dict(os.environ, {"HUGGINGFACE_HUB_CACHE": directory}):
                result = txt2srt.find_local_faster_whisper_model("small")
            self.assertEqual(result, str(snapshot))

    def test_gb18030_text_file_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            text_path = Path(directory) / "script.txt"
            text_path.write_bytes("中文字幕".encode("gb18030"))
            self.assertEqual(txt2srt.read_text_file(str(text_path)), "中文字幕")


if __name__ == "__main__":
    unittest.main()
