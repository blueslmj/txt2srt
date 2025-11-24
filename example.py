#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
示例代码：演示如何在Python脚本中使用音频-文本对齐功能
"""

from txt2srt import align_audio_text, generate_srt


def example_usage():
    """
    示例：如何在代码中使用音频对齐功能
    """
    
    # 示例1: 基本使用
    print("=" * 50)
    print("示例1: 基本使用")
    print("=" * 50)
    
    audio_file = "sample_audio.mp3"  # 替换为你的音频文件
    text_content = "这是需要对齐的文本内容"
    
    # 执行对齐
    segments = align_audio_text(audio_file, text_content, model_name="base")
    
    # 生成SRT文件
    generate_srt(segments, "output.srt")
    
    print(f"生成了 {len(segments)} 个字幕段落\n")
    
    # 打印前3个段落
    print("前3个段落预览:")
    for i, seg in enumerate(segments[:3], 1):
        print(f"\n段落 {i}:")
        print(f"  开始时间: {seg['start']:.2f}秒")
        print(f"  结束时间: {seg['end']:.2f}秒")
        print(f"  文本内容: {seg['text']}")


def batch_processing_example():
    """
    示例：批量处理多个音频文件
    """
    
    print("\n" + "=" * 50)
    print("示例2: 批量处理")
    print("=" * 50)
    
    # 定义多个音频和对应的文本
    tasks = [
        {"audio": "audio1.mp3", "text": "第一段音频的文本内容", "output": "subtitle1.srt"},
        {"audio": "audio2.mp3", "text": "第二段音频的文本内容", "output": "subtitle2.srt"},
        {"audio": "audio3.mp3", "text": "第三段音频的文本内容", "output": "subtitle3.srt"},
    ]
    
    for i, task in enumerate(tasks, 1):
        print(f"\n处理任务 {i}/{len(tasks)}: {task['audio']}")
        
        try:
            # 对齐音频和文本
            segments = align_audio_text(
                task["audio"],
                task["text"],
                model_name="base"
            )
            
            # 生成SRT
            generate_srt(segments, task["output"])
            
            print(f"✅ 完成: {task['output']}")
            
        except Exception as e:
            print(f"❌ 错误: {e}")


def advanced_example():
    """
    示例：高级用法 - 自定义处理
    """
    
    print("\n" + "=" * 50)
    print("示例3: 高级用法")
    print("=" * 50)
    
    audio_file = "sample_audio.mp3"
    text_content = "这是需要对齐的文本内容"
    
    # 使用更大的模型获得更好的准确度
    segments = align_audio_text(audio_file, text_content, model_name="small")
    
    # 自定义处理：过滤太短的段落
    filtered_segments = [
        seg for seg in segments
        if seg['end'] - seg['start'] >= 0.5  # 只保留至少0.5秒的段落
    ]
    
    print(f"原始段落数: {len(segments)}")
    print(f"过滤后段落数: {len(filtered_segments)}")
    
    # 自定义处理：合并相邻的短段落
    merged_segments = []
    current = None
    
    for seg in filtered_segments:
        if current is None:
            current = seg.copy()
        elif seg['start'] - current['end'] < 1.0:  # 间隔小于1秒则合并
            current['end'] = seg['end']
            current['text'] += " " + seg['text']
        else:
            merged_segments.append(current)
            current = seg.copy()
    
    if current:
        merged_segments.append(current)
    
    print(f"合并后段落数: {len(merged_segments)}")
    
    # 生成SRT
    generate_srt(merged_segments, "advanced_output.srt")


if __name__ == "__main__":
    print("音频-文本对齐功能示例\n")
    
    # 注意：运行这些示例前，请确保有对应的音频文件
    print("⚠️ 注意：请先准备好示例音频文件，或修改代码中的文件路径\n")
    
    # 取消下面的注释来运行示例
    # example_usage()
    # batch_processing_example()
    # advanced_example()
    
    print("\n💡 提示：请编辑 example.py 并取消注释相应的函数调用来运行示例")

