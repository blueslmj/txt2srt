#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频-文本对齐工具 - Gradio UI界面
现代化的Web界面，支持拖拽上传、实时进度显示
"""

import os
import sys
import tempfile
import socket

# 修复 Windows 终端中文乱码问题
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import gradio as gr
from txt2srt import align_audio_text, generate_srt, format_timestamp


def process_audio_text(audio_file, text_input, text_file, model_size, language, max_chars):
    """
    处理音频和文本，生成SRT字幕
    
    Args:
        audio_file: 上传的音频文件（可能是字符串路径或文件对象）
        text_input: 直接输入的文本
        text_file: 上传的文本文件（可能是字符串路径或文件对象）
        model_size: Whisper模型大小
        language: 语言代码
        max_chars: 每行最大字数
    
    Returns:
        (srt_file_path, preview_text, status_message)
    """
    try:
        # 验证输入
        if audio_file is None:
            return None, "", "❌ 错误：请上传音频文件"
        
        # 获取音频文件路径（兼容字符串和文件对象）
        if isinstance(audio_file, str):
            audio_path = audio_file
        else:
            audio_path = audio_file.name if hasattr(audio_file, 'name') else str(audio_file)
        
        # 获取文本内容
        text_content = ""
        if text_file is not None:
            # 兼容字符串路径和文件对象
            if isinstance(text_file, str):
                text_path = text_file
            else:
                text_path = text_file.name if hasattr(text_file, 'name') else str(text_file)
            
            with open(text_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        elif text_input and text_input.strip():
            text_content = text_input.strip()
        else:
            return None, "", "❌ 错误：请提供文本内容（直接输入或上传文件）"
        
        # 显示处理信息
        status = f"⏳ 正在处理...\n"
        status += f"📁 音频文件: {os.path.basename(audio_path)}\n"
        status += f"🎯 模型大小: {model_size}\n"
        status += f"🌏 语言: {language}\n"
        status += f"📝 文本长度: {len(text_content)} 字符\n"
        status += f"📏 每行字数限制: {max_chars} 字\n"
        status += f"\n正在使用Whisper模型进行语音识别..."
        
        # 处理音频
        language_code = None if language == "自动检测" else language
        segments = align_audio_text(
            audio_path,
            text_content,
            model_name=model_size.lower(),
            use_gpu=True,  # 启用GPU加速
            max_chars=int(max_chars)  # 每行字数限制
        )
        
        # 生成SRT文件
        output_dir = tempfile.gettempdir()
        srt_filename = os.path.splitext(os.path.basename(audio_path))[0] + ".srt"
        srt_path = os.path.join(output_dir, srt_filename)
        
        generate_srt(segments, srt_path)
        
        # 生成预览内容（前10个段落）
        preview = "📄 字幕预览 (前10个段落):\n\n"
        for i, seg in enumerate(segments[:10], 1):
            start = format_timestamp(seg['start'])
            end = format_timestamp(seg['end'])
            preview += f"{i}\n{start} --> {end}\n{seg['text']}\n\n"
        
        if len(segments) > 10:
            preview += f"... (共 {len(segments)} 个段落)\n"
        
        # 成功消息
        success_msg = f"✅ 处理完成！\n\n"
        success_msg += f"📊 统计信息:\n"
        success_msg += f"  - 字幕段落数: {len(segments)}\n"
        success_msg += f"  - 音频时长: {segments[-1]['end']:.2f} 秒\n"
        success_msg += f"  - 输出文件: {srt_filename}\n"
        
        return srt_path, preview, success_msg
        
    except Exception as e:
        error_msg = f"❌ 处理出错: {str(e)}\n\n"
        error_msg += "请检查:\n"
        error_msg += "1. 音频文件格式是否正确\n"
        error_msg += "2. 文本内容是否有效\n"
        error_msg += "3. 是否有足够的磁盘空间\n"
        return None, "", error_msg


def create_ui():
    """
    创建Gradio用户界面
    """
    
    # 自定义CSS样式
    custom_css = """
    .main-title {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 20px;
    }
    .subtitle {
        text-align: center;
        color: #7f8c8d;
        margin-bottom: 30px;
    }
    .output-box {
        font-family: 'Courier New', monospace;
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
    }
    """
    
    # Gradio 应用配置（兼容新版本）
    app = gr.Blocks(css=custom_css, title="音频文本对齐工具", theme=gr.themes.Soft())
    
    with app:
        
        # 标题
        gr.Markdown(
            """
            # 🎵 音频-文本对齐工具
            ### 自动将音频和文本对齐，生成SRT字幕文件
            """
        )
        
        with gr.Row():
            # 左侧：输入区域
            with gr.Column(scale=1):
                gr.Markdown("## 📥 输入")
                
                # 音频文件上传
                audio_input = gr.Audio(
                    label="1️⃣ 上传音频文件",
                    type="filepath",
                    sources=["upload"],
                )
                
                gr.Markdown("---")
                
                # 文本输入方式选择
                gr.Markdown("### 2️⃣ 提供文本内容 (选择一种方式)")
                
                with gr.Tab("📝 直接输入"):
                    text_input = gr.Textbox(
                        label="在此输入文本",
                        placeholder="请输入需要对齐的文本内容...",
                        lines=8,
                    )
                
                with gr.Tab("📁 上传文件"):
                    text_file_input = gr.File(
                        label="上传文本文件 (.txt)",
                        file_types=[".txt"],
                    )
                
                gr.Markdown("---")
                
                # 设置选项
                gr.Markdown("### ⚙️ 设置")
                
                model_size = gr.Dropdown(
                    label="模型大小",
                    choices=["Tiny", "Base", "Small", "Medium", "Large"],
                    value="Small",
                    info="更大的模型更准确但更慢"
                )
                
                language = gr.Dropdown(
                    label="语言",
                    choices=["自动检测", "zh", "en", "ja", "ko", "es", "fr", "de"],
                    value="zh",
                    info="音频语言 (zh=中文, en=英文)"
                )
                
                max_chars = gr.Slider(
                    label="每行字数限制",
                    minimum=10,
                    maximum=80,
                    value=40,
                    step=5,
                    info="控制每条字幕的最大字符数（推荐20-40字）"
                )
                
                # 处理按钮
                process_btn = gr.Button(
                    "🚀 开始处理",
                    variant="primary",
                    size="lg"
                )
            
            # 右侧：输出区域
            with gr.Column(scale=1):
                gr.Markdown("## 📤 输出")
                
                # 状态信息
                status_output = gr.Textbox(
                    label="处理状态",
                    lines=8,
                    interactive=False,
                    placeholder="等待处理..."
                )
                
                # SRT预览
                preview_output = gr.Textbox(
                    label="字幕预览",
                    lines=12,
                    interactive=False,
                    elem_classes="output-box"
                )
                
                # 下载按钮
                download_output = gr.File(
                    label="📥 下载SRT文件"
                )
        
        # 底部：使用说明
        with gr.Accordion("📖 使用说明", open=False):
            gr.Markdown(
                """
                ### 使用步骤
                1. **上传音频文件** - 支持 MP3, WAV, M4A, FLAC, OGG 等格式
                2. **提供文本内容** - 可以直接输入或上传 .txt 文件
                3. **选择模型大小** - Base 适合日常使用，Small/Medium 更准确
                4. **选择语言** - 默认中文，也可选择其他语言或自动检测
                5. **点击"开始处理"** - 等待处理完成
                6. **下载SRT文件** - 生成后可直接下载使用
                
                ### 模型选择建议
                - **Tiny/Base**: 快速测试，速度快但准确度一般
                - **Small**: 推荐使用，平衡速度和准确度
                - **Medium/Large**: 最高准确度，但处理较慢
                
                ### 注意事项
                - 首次使用会自动下载模型文件（约75MB-2.9GB）
                - 音频质量越好，对齐效果越准确
                - 建议单个音频不超过30分钟
                - 处理时间取决于音频长度和模型大小
                """
            )
        
        # 绑定处理函数
        process_btn.click(
            fn=process_audio_text,
            inputs=[
                audio_input,
                text_input,
                text_file_input,
                model_size,
                language,
                max_chars
            ],
            outputs=[
                download_output,
                preview_output,
                status_output
            ]
        )
        
        # 示例
        gr.Examples(
            examples=[
                [
                    None,  # audio
                    "这是一个示例文本。你可以输入你的文本内容。",  # text
                    None,  # text_file
                    "Base",  # model
                    "zh",  # language
                    30  # max_chars
                ]
            ],
            inputs=[
                audio_input,
                text_input,
                text_file_input,
                model_size,
                language,
                max_chars
            ]
        )
    
    return app


def main():
    """
    启动Gradio应用
    """
    print("=" * 60)
    print("🎵 音频-文本对齐工具 - Web界面")
    print("=" * 60)
    print()
    print("正在启动服务器...")
    print()
    
    app = create_ui()
    
    # 启动应用
    # Gradio会自动寻找可用端口（从7860开始）
    app.launch(
        server_name="127.0.0.1",
        share=False,
        inbrowser=True,  # 自动打开浏览器
        show_error=True,
        # 兼容新版Gradio
        allowed_paths=None
    )


if __name__ == "__main__":
    main()

