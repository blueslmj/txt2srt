#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频-文本对齐工具 - WhisperX 版本
使用 WhisperX 的强制对齐功能，获得更精确的时间戳
"""

import os
import sys
import argparse
import re
from typing import List, Dict

from project_paths import FASTER_WHISPER_MODELS_DIR, configure_project_environment


configure_project_environment()

# WhisperX 相关导入
import whisperx
import torch


def format_timestamp(seconds: float) -> str:
    """
    将秒数转换为SRT时间戳格式 (HH:MM:SS,mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def split_text_into_segments(text: str, max_chars: int = 30) -> List[str]:
    """
    将长文本分割成适合字幕显示的短句
    
    Args:
        text: 输入文本
        max_chars: 每段最大字符数
    
    Returns:
        分割后的文本段落列表
    """
    segments = []
    
    # 按换行符分割
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 按主要标点符号分割
        sentences = re.split(r'([。！？；.!?;])', line)
        
        current_segment = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            if not sentence.strip():
                continue
            
            full_sentence = sentence + punct
            potential_segment = current_segment + full_sentence
            
            if len(potential_segment) <= max_chars:
                current_segment = potential_segment
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                
                if len(full_sentence) <= max_chars:
                    current_segment = full_sentence
                else:
                    # 句子太长，按逗号分割
                    sub_segments = _split_long_sentence(full_sentence, max_chars)
                    for sub in sub_segments[:-1]:
                        segments.append(sub.strip())
                    current_segment = sub_segments[-1] if sub_segments else ""
        
        if current_segment.strip():
            segments.append(current_segment.strip())
    
    return segments


def _split_long_sentence(sentence: str, max_chars: int) -> List[str]:
    """分割超长句子"""
    if len(sentence) <= max_chars:
        return [sentence]
    
    segments = []
    parts = re.split(r'([，,、])', sentence)
    
    current = ""
    for i in range(0, len(parts), 2):
        part = parts[i]
        comma = parts[i + 1] if i + 1 < len(parts) else ""
        
        if not part.strip():
            continue
        
        full_part = part + comma
        potential = current + full_part
        
        if len(potential) <= max_chars:
            current = potential
        else:
            if current:
                segments.append(current.strip())
            
            if len(full_part) > max_chars:
                # 强制按字数分割
                while len(full_part) > max_chars:
                    segments.append(full_part[:max_chars].strip())
                    full_part = full_part[max_chars:].strip()
                current = full_part
            else:
                current = full_part
    
    if current.strip():
        segments.append(current.strip())
    
    return segments if segments else [sentence]


def align_audio_text_whisperx(
    audio_path: str, 
    text: str, 
    model_name: str = "base", 
    use_gpu: bool = True,
    max_chars: int = 30,
    language: str = "zh"
) -> List[Dict]:
    """
    使用 WhisperX 进行音频-文本对齐
    
    WhisperX 的优势：
    1. 使用 wav2vec2 进行强制对齐，精度更高
    2. 直接分析音频波形，不受 Whisper 识别错误影响
    3. 可以获得词级甚至音素级时间戳
    
    Args:
        audio_path: 音频文件路径
        text: 用户提供的准确文本
        model_name: Whisper模型大小
        use_gpu: 是否使用GPU
        max_chars: 每行最大字符数
        language: 语言代码
    
    Returns:
        包含时间戳的文本段落列表
    """
    # 设置设备
    device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    
    if device == "cuda":
        try:
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ 使用设备: CUDA ({gpu_name})")
        except:
            print(f"✅ 使用设备: CUDA")
    else:
        print("⚠️ GPU不可用，使用CPU处理（速度较慢）")
    
    print(f"\n🎯 步骤1: 加载 WhisperX 模型 ({model_name})...")
    model = whisperx.load_model(
        model_name,
        device,
        compute_type=compute_type,
        download_root=str(FASTER_WHISPER_MODELS_DIR),
    )
    
    print(f"🎯 步骤2: 使用 Whisper 进行初步识别...")
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=16, language=language)
    
    print(f"   识别到 {len(result['segments'])} 个语音段落")
    
    print(f"\n🎯 步骤3: 加载对齐模型 (wav2vec2)...")
    # 加载对齐模型
    model_a, metadata = whisperx.load_align_model(
        language_code=language, 
        device=device
    )
    
    print(f"🎯 步骤4: 执行强制对齐...")
    # 执行对齐 - 这是 WhisperX 的核心优势
    result = whisperx.align(
        result["segments"], 
        model_a, 
        metadata, 
        audio, 
        device,
        return_char_alignments=True  # 获取字符级对齐
    )
    
    # 提取词级时间戳
    word_segments = []
    for segment in result["segments"]:
        if "words" in segment:
            for word in segment["words"]:
                if "start" in word and "end" in word:
                    word_segments.append({
                        "word": word["word"],
                        "start": word["start"],
                        "end": word["end"]
                    })
    
    print(f"   获得 {len(word_segments)} 个词级时间戳")
    
    print(f"\n🎯 步骤5: 将用户文本映射到时间戳...")
    
    # 分割用户文本
    user_sentences = split_text_into_segments(text, max_chars=max_chars)
    print(f"   用户文本有 {len(user_sentences)} 个句子（每行限制 {max_chars} 字）")
    
    # 使用词级时间戳为用户句子分配时间
    aligned_segments = align_user_sentences_to_words(user_sentences, word_segments)
    
    # 后处理：修复重叠
    aligned_segments = fix_overlapping_timestamps(aligned_segments)
    
    print(f"\n✅ 对齐完成！生成了 {len(aligned_segments)} 个字幕段落")
    
    return aligned_segments


def align_user_sentences_to_words(
    user_sentences: List[str], 
    word_segments: List[Dict]
) -> List[Dict]:
    """
    将用户句子与 WhisperX 的词级时间戳对齐
    
    策略：使用字符级匹配，找到每个用户句子对应的时间范围
    """
    if not word_segments:
        print("⚠️ 警告: 没有词级时间戳，使用估算")
        return []
    
    # 构建识别文本的字符-时间映射
    char_times = []
    for word in word_segments:
        word_text = word["word"]
        word_start = word["start"]
        word_end = word["end"]
        word_duration = word_end - word_start
        
        # 为每个字符估算时间
        for i, char in enumerate(word_text):
            if char.strip():  # 跳过空格
                char_time = word_start + (i / len(word_text)) * word_duration
                char_times.append({
                    "char": char,
                    "time": char_time
                })
    
    # 提取识别的字符序列（去除标点）
    def remove_punct(text):
        return ''.join([c for c in text if c.strip() and c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
    
    recognized_chars = [ct["char"] for ct in char_times if ct["char"] not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]']
    recognized_times = [ct["time"] for ct in char_times if ct["char"] not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]']
    
    # 为每个用户句子找到对应的时间范围
    aligned_segments = []
    current_char_idx = 0
    
    for sentence in user_sentences:
        if not sentence.strip():
            continue
        
        sentence_chars = remove_punct(sentence)
        if not sentence_chars:
            continue
        
        # 在识别字符中查找匹配
        best_start_idx = current_char_idx
        best_end_idx = min(current_char_idx + len(sentence_chars), len(recognized_chars))
        
        # 简单的滑动窗口匹配
        best_match_score = 0
        search_range = min(50, len(recognized_chars) - current_char_idx)
        
        for offset in range(search_range):
            start_idx = current_char_idx + offset
            end_idx = min(start_idx + len(sentence_chars), len(recognized_chars))
            
            if end_idx > len(recognized_chars):
                break
            
            # 计算匹配分数
            match_count = sum(
                1 for i, char in enumerate(sentence_chars) 
                if start_idx + i < len(recognized_chars) and recognized_chars[start_idx + i] == char
            )
            
            if match_count > best_match_score:
                best_match_score = match_count
                best_start_idx = start_idx
                best_end_idx = min(start_idx + len(sentence_chars), len(recognized_chars))
        
        # 获取时间戳
        if best_start_idx < len(recognized_times) and best_end_idx > 0:
            start_time = recognized_times[best_start_idx]
            end_time = recognized_times[min(best_end_idx - 1, len(recognized_times) - 1)]
            
            # 确保最小时长
            if end_time - start_time < 0.5:
                end_time = start_time + max(0.5, len(sentence_chars) * 0.15)
            
            aligned_segments.append({
                "start": start_time,
                "end": end_time,
                "text": sentence.strip()
            })
            
            # 更新当前位置
            current_char_idx = best_end_idx
        else:
            # 无法匹配，使用估算
            if aligned_segments:
                last_end = aligned_segments[-1]["end"]
                estimated_duration = max(1.0, len(sentence_chars) * 0.15)
                aligned_segments.append({
                    "start": last_end,
                    "end": last_end + estimated_duration,
                    "text": sentence.strip()
                })
    
    return aligned_segments


def fix_overlapping_timestamps(segments: List[Dict]) -> List[Dict]:
    """
    修复重叠的时间戳
    """
    if len(segments) == 0:
        return segments
    
    segments = sorted(segments, key=lambda x: x["start"])
    fixed_segments = []
    
    for i, segment in enumerate(segments):
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]
        
        # 计算合理的最大时长
        text_chars = len([c for c in text if c.strip() and c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
        max_duration = max(2.0, 1.0 + text_chars * 0.4)
        min_duration = max(0.8, 0.5 + text_chars * 0.12)
        
        # 确保不与前一个重叠
        if i > 0:
            prev_end = fixed_segments[-1]["end"]
            if start < prev_end:
                start = prev_end
        
        # 修复时长
        duration = end - start
        if duration > max_duration:
            end = start + max_duration
        if duration < min_duration:
            end = start + min_duration
        
        # 添加阅读缓冲
        end = end + 0.3
        
        # 确保不超过下一个字幕
        if i + 1 < len(segments):
            next_start = segments[i + 1]["start"]
            if end > next_start:
                end = max(start + 0.5, next_start - 0.05)
        
        # 确保最小时长
        if end <= start:
            end = start + max(1.0, text_chars * 0.15)
        
        fixed_segments.append({
            "start": start,
            "end": end,
            "text": text
        })
    
    return fixed_segments


def generate_srt(segments: List[Dict], output_path: str):
    """
    生成SRT字幕文件
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            f.write(f"{i}\n")
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{segment['text']}\n")
            f.write("\n")
    
    print(f"SRT字幕文件已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="音频-文本对齐工具 (WhisperX 版本)"
    )
    parser.add_argument(
        "audio",
        help="输入音频文件路径"
    )
    parser.add_argument(
        "text",
        help="输入文本文件路径或直接输入文本"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出SRT文件路径",
        default=None
    )
    parser.add_argument(
        "-m", "--model",
        help="Whisper模型大小",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"]
    )
    parser.add_argument(
        "-l", "--language",
        help="语言代码",
        default="zh"
    )
    parser.add_argument(
        "-c", "--max-chars",
        help="每行最大字符数",
        type=int,
        default=30
    )
    
    args = parser.parse_args()
    
    # 检查音频文件
    if not os.path.exists(args.audio):
        print(f"错误: 音频文件不存在: {args.audio}")
        sys.exit(1)
    
    # 读取文本
    if os.path.exists(args.text):
        with open(args.text, 'r', encoding='utf-8') as f:
            text_content = f.read()
    else:
        text_content = args.text
    
    # 设置输出路径
    if args.output is None:
        base_name = os.path.splitext(args.audio)[0]
        output_path = f"{base_name}.srt"
    else:
        output_path = args.output
    
    # 执行对齐
    print("\n" + "=" * 60)
    print("🎵 音频-文本对齐工具 (WhisperX 版本)")
    print("=" * 60)
    
    segments = align_audio_text_whisperx(
        args.audio, 
        text_content, 
        args.model,
        max_chars=args.max_chars,
        language=args.language
    )
    
    # 生成SRT
    generate_srt(segments, output_path)
    
    print(f"\n✅ 完成！共生成 {len(segments)} 个字幕段落")


if __name__ == "__main__":
    main()

