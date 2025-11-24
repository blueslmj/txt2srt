#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频-文本对齐工具，生成SRT字幕文件
"""

import os
import sys
import argparse
import whisper
import stable_whisper
from typing import List, Dict, Tuple
import re
from dtw import dtw
import numpy as np


def format_timestamp(seconds: float) -> str:
    """
    将秒数转换为SRT时间戳格式 (HH:MM:SS,mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def split_text_into_segments(text: str, max_chars: int = 50) -> List[str]:
    """
    将长文本分割成适合字幕显示的短句
    
    优先级：
    1. 换行符（最高优先级，强制分句）
    2. 句子标点（。！？；等）
    3. 长度限制（如果句子太长，强制分割）
    
    Args:
        text: 输入文本
        max_chars: 每段最大字符数
    
    Returns:
        分割后的文本段落列表
    """
    segments = []
    
    # 第一步：按换行符分割（保留原文的段落结构）
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 第二步：按标点符号分割每一行
        sentences = re.split(r'([。！？；\.,!?;])', line)
        
        current_segment = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            if not sentence.strip():
                continue
                
            potential_segment = current_segment + sentence + punct
            
            # 如果累积的句子没超过长度限制，继续累积
            if len(potential_segment) <= max_chars:
                current_segment = potential_segment
            else:
                # 超过限制了，输出当前段落
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = sentence + punct
        
        # 每一行结束后，强制输出累积的内容（重要！）
        if current_segment.strip():
            segments.append(current_segment.strip())
    
    return segments


def align_audio_text(audio_path: str, text: str, model_name: str = "base", use_gpu: bool = True) -> List[Dict]:
    """
    先用Whisper识别获取准确的时间戳，然后用用户文本替换识别文本
    
    核心思路：
    1. Whisper识别音频 → 获取准确的时间戳（基于音频特征）
    2. 提取识别出的句子 + 时间戳
    3. 使用DTW算法匹配识别句子和用户句子
    4. 用用户的正确文本替换识别文本，但保留Whisper的准确时间戳
    
    Args:
        audio_path: 音频文件路径
        text: 用户提供的准确文本
        model_name: Whisper模型大小 (tiny, base, small, medium, large)
        use_gpu: 是否使用GPU加速
    
    Returns:
        包含时间戳的文本段落列表（使用用户提供的文本 + Whisper的时间戳）
    """
    import torch
    
    # 检查GPU可用性
    device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
    if use_gpu and not torch.cuda.is_available():
        print("⚠️ 警告: GPU不可用，使用CPU处理（速度较慢）")
        print("   如需GPU加速，请安装CUDA版本的PyTorch")
    else:
        print(f"✅ 使用设备: {device.upper()}")
    
    print(f"加载Whisper模型 (stable-ts增强版): {model_name}...")
    # 使用stable-ts加载模型（提供更精确的时间戳）
    model = stable_whisper.load_model(model_name, device=device)
    
    print(f"正在处理音频文件: {audio_path}")
    print("🎯 步骤1: 使用Whisper识别音频，获取准确的时间戳...")
    
    # 使用stable-ts识别音频（获取精确的句子级时间戳）
    result = model.transcribe(
        audio_path,
        language="zh",
        word_timestamps=True,
        verbose=False,
        regroup=True,  # 重新分组，获得合理的句子切分
    )
    
    # 提取识别出的句子和时间戳
    recognized_segments = []
    for segment in result.segments:
        recognized_segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
    
    print(f"   Whisper识别到 {len(recognized_segments)} 个语音段落")
    
    # 显示前几个识别结果（调试用）
    if len(recognized_segments) > 0:
        print("\n📝 识别的前3个段落（含时间戳）:")
        for i, seg in enumerate(recognized_segments[:3]):
            print(f"   [{i+1}] {seg['start']:.1f}s - {seg['end']:.1f}s: {seg['text'][:30]}...")
    
    print("\n🎯 步骤2: 将用户文本分割成句子...")
    user_sentences = split_text_into_segments(text)
    print(f"   用户文本有 {len(user_sentences)} 个句子")
    
    # 显示前几个用户句子
    if len(user_sentences) > 0:
        print("\n📝 用户的前3个句子:")
        for i, sentence in enumerate(user_sentences[:3]):
            print(f"   [{i+1}] {sentence[:30]}...")
    
    print("\n🎯 步骤3: 使用DTW算法匹配识别文本和用户文本...")
    
    # 使用DTW在字符级别匹配
    aligned_segments = match_user_text_to_timestamps(
        recognized_segments, 
        user_sentences
    )
    
    print(f"\n🎯 步骤4: 修复时间戳重叠问题...")
    
    # 修复重叠的时间戳，确保严格按时间顺序
    aligned_segments = fix_overlapping_timestamps(aligned_segments)
    
    print(f"\n✅ 对齐完成！生成了 {len(aligned_segments)} 个字幕段落")
    print(f"   保留了Whisper的准确时间戳，使用了用户的正确文本")
    
    return aligned_segments


def match_user_text_to_timestamps(recognized_segments: List[Dict], user_sentences: List[str]) -> List[Dict]:
    """
    使用DTW算法匹配用户句子和识别句子，用用户文本替换识别文本但保留时间戳
    
    策略：
    1. 提取识别句子和用户句子的字符序列
    2. 使用DTW找到字符级别的对应关系
    3. 根据对应关系，将用户句子映射到识别句子的时间戳
    
    Args:
        recognized_segments: Whisper识别的句子列表（含准确时间戳）
        user_sentences: 用户提供的正确句子列表
    
    Returns:
        对齐后的句子列表（用户文本 + Whisper时间戳）
    """
    if len(recognized_segments) == 0 or len(user_sentences) == 0:
        print("⚠️ 文本为空，无法对齐")
        return []
    
    # 移除标点符号的辅助函数
    def remove_punctuation(text):
        return ''.join([c for c in text if c.strip() and c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
    
    # 提取识别文本的字符序列（去除标点）
    recognized_text = ''.join([seg["text"] for seg in recognized_segments])
    recognized_chars = list(remove_punctuation(recognized_text))
    
    # 提取用户文本的字符序列（去除标点）
    user_text = ''.join(user_sentences)
    user_chars = list(remove_punctuation(user_text))
    
    print(f"   识别文本: {len(recognized_chars)} 个字符")
    print(f"   用户文本: {len(user_chars)} 个字符")
    
    # 构建DTW距离矩阵
    n_user = len(user_chars)
    n_recognized = len(recognized_chars)
    
    distance_matrix = np.zeros((n_user, n_recognized))
    for i in range(n_user):
        for j in range(n_recognized):
            distance_matrix[i, j] = 0 if user_chars[i] == recognized_chars[j] else 1
    
    # 运行DTW算法
    print("   运行DTW算法进行字符级匹配...")
    alignment = dtw(distance_matrix)
    
    # 获取对齐路径
    path = list(zip(alignment.index1, alignment.index2))
    
    match_rate = (1 - alignment.normalizedDistance) * 100
    print(f"   ✅ DTW匹配成功，相似度: {match_rate:.1f}%")
    
    # 为每个识别字符建立索引（字符 → 所属的segment和segment内的位置）
    recognized_char_to_segment = []
    for seg_idx, segment in enumerate(recognized_segments):
        seg_text = remove_punctuation(segment["text"])
        for char_idx, char in enumerate(seg_text):
            recognized_char_to_segment.append({
                "seg_idx": seg_idx,
                "char_idx": char_idx,
                "total_chars": len(seg_text),
                "segment": segment
            })
    
    # 为每个用户字符找到对应的识别segment
    user_char_to_segment = [None] * n_user
    for user_idx, rec_idx in path:
        if rec_idx < len(recognized_char_to_segment):
            user_char_to_segment[user_idx] = recognized_char_to_segment[rec_idx]
    
    # 建立更精细的映射：为每个用户字符找到对应的时间戳
    user_char_times = []
    for i in range(n_user):
        if user_char_to_segment[i] is not None:
            seg_info = user_char_to_segment[i]
            segment = seg_info["segment"]
            
            # 在segment内部进行时间插值
            segment_duration = segment["end"] - segment["start"]
            total_chars = seg_info["total_chars"]
            
            if total_chars > 0:
                char_time = segment["start"] + (seg_info["char_idx"] / total_chars) * segment_duration
            else:
                char_time = segment["start"]
            
            user_char_times.append(char_time)
        else:
            # 没有匹配到，稍后插值
            user_char_times.append(None)
    
    # 对未匹配的字符进行线性插值
    for i in range(n_user):
        if user_char_times[i] is None:
            # 向前找最近的有效时间
            prev_time = 0.0
            for j in range(i - 1, -1, -1):
                if user_char_times[j] is not None:
                    prev_time = user_char_times[j]
                    break
            
            # 向后找最近的有效时间
            next_time = recognized_segments[-1]["end"] if recognized_segments else 0.0
            for j in range(i + 1, n_user):
                if user_char_times[j] is not None:
                    next_time = user_char_times[j]
                    break
            
            user_char_times[i] = (prev_time + next_time) / 2
    
    # 现在为每个用户句子分配时间戳
    aligned_segments = []
    char_idx = 0
    
    for sentence in user_sentences:
        if not sentence.strip():
            continue
        
        # 提取句子的纯字符
        sentence_chars = remove_punctuation(sentence)
        
        if len(sentence_chars) == 0:
            # 纯标点句子，使用估算时长
            if aligned_segments:
                last_end = aligned_segments[-1]["end"]
                aligned_segments.append({
                    "start": last_end,
                    "end": last_end + 0.5,
                    "text": sentence.strip()
                })
            continue
        
        # 找到这个句子对应的字符范围
        start_char_idx = char_idx
        end_char_idx = min(char_idx + len(sentence_chars), n_user)
        
        if start_char_idx >= n_user:
            # 超出范围，使用估算
            if aligned_segments:
                last_end = aligned_segments[-1]["end"]
                estimated_duration = len(sentence_chars) * 0.15
                aligned_segments.append({
                    "start": last_end,
                    "end": last_end + estimated_duration,
                    "text": sentence.strip()
                })
                print(f"   ⚠️ [{len(aligned_segments)}] 超出匹配范围，使用估算时长")
            break
        
        # 使用字符时间戳
        start_time = user_char_times[start_char_idx]
        end_time = user_char_times[min(end_char_idx - 1, n_user - 1)]
        
        # 确保时长合理（至少0.5秒）
        if end_time - start_time < 0.5:
            end_time = start_time + max(0.5, len(sentence_chars) * 0.15)
        
        aligned_segments.append({
            "start": start_time,
            "end": end_time,
            "text": sentence.strip()
        })
        
        # 调试信息（前5句和后5句）
        if len(aligned_segments) <= 5 or len(user_sentences) - len(aligned_segments) < 5:
            duration = end_time - start_time
            print(f"   [{len(aligned_segments)}] {start_time:.1f}s-{end_time:.1f}s ({duration:.1f}s): {sentence[:20]}...")
        
        char_idx = end_char_idx
    
    # 检查是否所有句子都被处理了
    if len(aligned_segments) < len(user_sentences):
        missing = len(user_sentences) - len(aligned_segments)
        print(f"   ⚠️ 警告: {missing} 个句子未能匹配，将使用估算时长")
    
    return aligned_segments


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（基于最长公共子序列）
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
    
    Returns:
        相似度 (0-1之间)
    """
    # 移除标点和空格
    clean1 = ''.join([c for c in text1 if c.strip() and c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
    clean2 = ''.join([c for c in text2 if c.strip() and c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
    
    if len(clean1) == 0 or len(clean2) == 0:
        return 0.0
    
    # 计算最长公共子序列长度（简化版，用于快速匹配）
    # 这里用简单的字符匹配计数
    matches = 0
    for char in clean1:
        if char in clean2:
            matches += 1
    
    # 相似度 = 匹配字符数 / 较长文本的长度
    similarity = matches / max(len(clean1), len(clean2))
    
    return similarity


def align_user_text_with_timestamps(user_sentences: List[str], words_with_time: List[Dict]) -> List[Dict]:
    """
    将用户提供的文本与带时间戳的识别词对齐（基于滑动窗口匹配）
    
    Args:
        user_sentences: 用户文本分割后的句子列表
        words_with_time: Whisper识别出的词及时间戳
    
    Returns:
        对齐后的段落列表
    """
    aligned_segments = []
    total_words = len(words_with_time)
    
    if total_words == 0:
        print("⚠️ 警告：Whisper没有识别出任何词，无法对齐")
        return aligned_segments
    
    audio_duration = words_with_time[-1]["end"]
    
    print(f"📊 对齐统计：")
    print(f"   - 用户文本: {len(user_sentences)} 个句子")
    print(f"   - Whisper识别: {total_words} 个词")
    print(f"   - 音频时长: {audio_duration:.1f} 秒")
    print(f"🔍 开始滑动窗口匹配...")
    
    # 当前在词列表中的起始位置
    current_word_idx = 0
    
    for sent_idx, user_sentence in enumerate(user_sentences):
        if not user_sentence.strip():
            continue
        
        # 移除标点的用户句子
        user_clean = ''.join([c for c in user_sentence if c.strip() and c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
        
        if len(user_clean) == 0:
            continue
        
        user_len = len(user_clean)
        
        # 估算这个句子需要多少个词（中文平均一个词2-3个字）
        estimated_words = max(5, int(user_len / 2.5))
        
        best_match_score = 0
        best_start_idx = current_word_idx
        best_end_idx = min(current_word_idx + estimated_words, total_words)
        
        # 滑动窗口查找最佳匹配
        # 窗口大小范围：estimated_words的50% 到 200%
        min_window = max(3, int(estimated_words * 0.5))
        max_window = min(int(estimated_words * 2), total_words - current_word_idx)
        
        for window_size in range(min_window, max_window + 1):
            # 尝试不同的起始位置（允许向前或向后微调）
            for start_offset in range(-3, 4):
                start_idx = current_word_idx + start_offset
                end_idx = start_idx + window_size
                
                if start_idx < 0 or end_idx > total_words:
                    continue
                
                # 提取这个窗口内的文本
                window_text = ""
                for i in range(start_idx, end_idx):
                    word = words_with_time[i]["word"].strip()
                    clean_word = ''.join([c for c in word if c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
                    window_text += clean_word
                
                # 计算相似度
                similarity = calculate_similarity(user_sentence, window_text)
                
                # 如果相似度更高，更新最佳匹配
                if similarity > best_match_score:
                    best_match_score = similarity
                    best_start_idx = start_idx
                    best_end_idx = end_idx
        
        # 使用最佳匹配的时间戳
        if best_start_idx < total_words and best_end_idx > best_start_idx:
            start_time = words_with_time[best_start_idx]["start"]
            end_time = words_with_time[min(best_end_idx - 1, total_words - 1)]["end"]
            
            aligned_segments.append({
                "start": start_time,
                "end": end_time,
                "text": user_sentence.strip()
            })
            
            # 更新当前位置
            current_word_idx = best_end_idx
            
            # 调试信息（前10句）
            if len(aligned_segments) <= 10:
                duration = end_time - start_time
                print(f"   句子 {len(aligned_segments)}: {start_time:.1f}s - {end_time:.1f}s ({duration:.1f}s), 相似度 {best_match_score*100:.0f}%")
        else:
            # 如果无法匹配，使用估算的时间
            if aligned_segments:
                last_end = aligned_segments[-1]["end"]
                estimated_duration = len(user_clean) * 0.3  # 假设每字0.3秒
                aligned_segments.append({
                    "start": last_end,
                    "end": min(last_end + estimated_duration, audio_duration),
                    "text": user_sentence.strip()
                })
            else:
                # 第一句话找不到匹配，从0开始
                estimated_duration = len(user_clean) * 0.3
                aligned_segments.append({
                    "start": 0.0,
                    "end": min(estimated_duration, audio_duration),
                    "text": user_sentence.strip()
                })
    
    print(f"✅ 对齐完成！生成了 {len(aligned_segments)} 个字幕段落")
    
    return aligned_segments


def align_text_by_segments(whisper_segments: List[Dict], user_sentences: List[str]) -> List[Dict]:
    """
    当没有词级时间戳时，使用段落级对齐
    
    Args:
        whisper_segments: Whisper识别的段落
        user_sentences: 用户文本句子
    
    Returns:
        对齐后的段落列表
    """
    aligned_segments = []
    
    # 简单策略：平均分配时间
    if not whisper_segments:
        return aligned_segments
    
    total_duration = whisper_segments[-1]["end"]
    sentence_duration = total_duration / len(user_sentences)
    
    for i, sentence in enumerate(user_sentences):
        if sentence.strip():
            aligned_segments.append({
                "start": i * sentence_duration,
                "end": (i + 1) * sentence_duration,
                "text": sentence.strip()
            })
    
    return aligned_segments


def generate_srt(segments: List[Dict], output_path: str):
    """
    生成SRT字幕文件
    
    Args:
        segments: 包含时间戳的文本段落列表
        output_path: 输出SRT文件路径
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            # 写入序号
            f.write(f"{i}\n")
            # 写入时间戳
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            f.write(f"{start_time} --> {end_time}\n")
            # 写入文本
            f.write(f"{segment['text']}\n")
            # 空行分隔
            f.write("\n")
    
    print(f"SRT字幕文件已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="音频-文本对齐工具，生成SRT字幕文件"
    )
    parser.add_argument(
        "audio",
        help="输入音频文件路径 (支持 mp3, wav, m4a, flac, ogg 等格式)"
    )
    parser.add_argument(
        "text",
        help="输入文本文件路径 或 直接输入文本内容"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出SRT文件路径 (默认: audio_name.srt)",
        default=None
    )
    parser.add_argument(
        "-m", "--model",
        help="Whisper模型大小 (tiny, base, small, medium, large)",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"]
    )
    parser.add_argument(
        "-l", "--language",
        help="语言代码 (zh: 中文, en: 英文, None: 自动检测)",
        default="zh"
    )
    
    args = parser.parse_args()
    
    # 检查音频文件是否存在
    if not os.path.exists(args.audio):
        print(f"错误: 音频文件不存在: {args.audio}")
        sys.exit(1)
    
    # 读取文本
    if os.path.exists(args.text):
        with open(args.text, 'r', encoding='utf-8') as f:
            text_content = f.read()
        print(f"从文件读取文本: {args.text}")
    else:
        text_content = args.text
        print("使用直接提供的文本内容")
    
    # 设置输出文件路径
    if args.output is None:
        base_name = os.path.splitext(args.audio)[0]
        output_path = f"{base_name}.srt"
    else:
        output_path = args.output
    
    # 执行对齐
    print("\n开始音频-文本对齐...")
    segments = align_audio_text(args.audio, text_content, args.model)
    
    # 生成SRT文件
    generate_srt(segments, output_path)
    
    print(f"\n✅ 完成！共生成 {len(segments)} 个字幕段落")


if __name__ == "__main__":
    main()



def fix_overlapping_timestamps(segments: List[Dict]) -> List[Dict]:
    """
    修复重叠的时间戳，确保字幕段落严格按时间顺序排列且不重叠
    
    Args:
        segments: 初始对齐的段落列表（可能有重叠）
    
    Returns:
        修复后的段落列表（无重叠）
    """
    if len(segments) == 0:
        return segments
    
    # 按开始时间排序
    segments = sorted(segments, key=lambda x: x["start"])
    
    fixed_segments = []
    
    for i, segment in enumerate(segments):
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]
        
        # 如果不是第一个段落，确保开始时间不早于上一个段落的结束时间
        if i > 0:
            prev_end = fixed_segments[-1]["end"]
            if start < prev_end:
                # 重叠了，调整开始时间为上一个段落结束时间
                start = prev_end
                # 如果调整后结束时间也变得不合理，重新计算
                if end <= start:
                    # 根据文本长度估算合理的时长（每个字约0.15秒）
                    text_chars = len([c for c in text if c.strip() and c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
                    estimated_duration = max(1.0, text_chars * 0.15)
                    end = start + estimated_duration
        
        # 给结束时间添加0.3秒的缓冲（让字幕多停留一会儿，便于阅读）
        end = end + 0.3
        
        # 如果有下一个字幕，确保不超过下一个字幕的开始时间
        if i + 1 < len(segments):
            next_start = segments[i + 1]["start"]
            if end > next_start:
                # 缩短到下一个字幕开始前0.05秒（留一点间隙）
                end = max(start + 0.5, next_start - 0.05)
        
        # 确保结束时间晚于开始时间
        if end <= start:
            text_chars = len([c for c in text if c.strip() and c not in '。，！？；：、,.!?;: 　「」『』""''（）()【】[]'])
            estimated_duration = max(1.0, text_chars * 0.15)
            end = start + estimated_duration
        
        # 确保最小显示时间（至少0.5秒）
        if end - start < 0.5:
            end = start + 0.5
            # 再次检查是否与下一个字幕冲突
            if i + 1 < len(segments):
                next_start = segments[i + 1]["start"]
                if end > next_start:
                    end = max(start + 0.5, next_start - 0.05)
        
        fixed_segments.append({
            "start": start,
            "end": end,
            "text": text
        })
    
    # 显示修复统计
    overlaps_fixed = sum(1 for i in range(len(segments)) if i > 0 and segments[i]["start"] < segments[i-1]["end"])
    if overlaps_fixed > 0:
        print(f"   修复了 {overlaps_fixed} 处时间重叠")
    
    print(f"   为每个字幕添加了 0.3秒 的阅读缓冲时间")
    
    return fixed_segments
