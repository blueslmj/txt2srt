#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频-文本对齐工具 - Gradio UI界面
现代化的Web界面，支持拖拽上传、实时进度显示
"""

import os
import sys
import tempfile

from project_paths import configure_project_environment


configure_project_environment()

# 修复 Windows 终端中文乱码问题
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import gradio as gr
from txt2srt import (
    Txt2SrtError,
    align_audio_text,
    format_timestamp,
    generate_srt,
    read_text_file,
)


DEVICE_VALUES = {
    "自动选择": "auto",
    "NVIDIA GPU (CUDA)": "cuda",
    "CPU": "cpu",
}


def process_audio_text(
    audio_file,
    text_input,
    text_file,
    model_size,
    language,
    max_chars,
    device,
    progress=gr.Progress(),
):
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
            return None, "", "缺少音频文件\n\n请先上传需要生成字幕的音频。"
        
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
            
            text_content = read_text_file(text_path)
        elif text_input and text_input.strip():
            text_content = text_input.strip()
        else:
            return None, "", "缺少文稿\n\n请直接输入文稿或上传 TXT 文件。"
        
        diagnostics = {}
        language_code = None if language == "自动检测" else language

        def update_progress(value, message):
            progress(value, desc=message)

        segments = align_audio_text(
            audio_path,
            text_content,
            model_name=model_size.lower(),
            max_chars=int(max_chars),
            language=language_code,
            device=DEVICE_VALUES.get(device, device or "auto"),
            progress_callback=update_progress,
            diagnostics=diagnostics,
        )
        
        # 生成SRT文件
        output_dir = tempfile.mkdtemp(prefix="txt2srt-")
        srt_filename = os.path.splitext(os.path.basename(audio_path))[0] + ".srt"
        srt_path = os.path.join(output_dir, srt_filename)
        
        generate_srt(segments, srt_path)
        
        # 生成预览内容（前12个段落）
        preview = "字幕预览（前 12 条）\n\n"
        for i, seg in enumerate(segments[:12], 1):
            start = format_timestamp(seg['start'])
            end = format_timestamp(seg['end'])
            preview += f"{i}\n{start} --> {end}\n{seg['text']}\n\n"
        
        if len(segments) > 12:
            preview += f"... (共 {len(segments)} 个段落)\n"
        
        success_msg = "处理完成\n\n"
        success_msg += f"字幕：{len(segments)} 条\n"
        success_msg += f"时间轴：{segments[-1]['end']:.2f} 秒\n"
        success_msg += (
            f"运行：{diagnostics.get('backend', 'Whisper')} / "
            f"{str(diagnostics.get('device', device)).upper()}\n"
        )
        success_msg += f"对齐相似度：{diagnostics.get('similarity', 0):.0%}\n"
        success_msg += f"输出：{srt_filename}\n"
        warnings = diagnostics.get("warnings", [])
        if warnings:
            success_msg += "\n需要抽查\n" + "\n".join(f"- {item}" for item in warnings)
        else:
            success_msg += "\n质量检查：未发现明显的文稿偏差"
        
        return srt_path, preview, success_msg
        
    except Txt2SrtError as e:
        error_msg = f"处理失败\n\n{e}"
        return None, "", error_msg
    except Exception as e:
        error_msg = f"处理失败\n\n{e}\n\n请检查音频格式、FFmpeg 和可用磁盘空间。"
        return None, "", error_msg


def create_ui():
    """
    创建Gradio用户界面
    """
    
    custom_css = """
    :root {
        --studio-ink: #172033;
        --studio-muted: #667085;
        --studio-paper: #f3f7f9;
        --studio-panel: #ffffff;
        --studio-signal: #087f8c;
        --studio-marker: #6457d5;
    }
    .gradio-container {
        max-width: 1180px !important;
        color: var(--studio-ink);
        font-family: Inter, "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
    }
    .studio-hero {
        position: relative;
        overflow: hidden;
        margin: 4px 0 24px;
        padding: 30px 34px 26px;
        border: 1px solid #d7e2e8;
        border-radius: 18px;
        background: var(--studio-panel);
        box-shadow: 0 14px 42px rgba(23, 32, 51, .07);
    }
    .studio-kicker {
        margin-bottom: 10px;
        color: var(--studio-signal);
        font: 700 12px/1.2 "Cascadia Mono", Consolas, monospace;
        letter-spacing: .14em;
    }
    .studio-hero h1 {
        max-width: 720px;
        margin: 0;
        color: var(--studio-ink);
        font-family: Bahnschrift, "Microsoft YaHei UI", sans-serif;
        font-size: clamp(30px, 5vw, 54px);
        font-weight: 650;
        letter-spacing: -.04em;
        line-height: 1.05;
    }
    .studio-hero p {
        max-width: 720px;
        margin: 14px 0 22px;
        color: var(--studio-muted);
        font-size: 15px;
        line-height: 1.7;
    }
    .signal-rail {
        display: flex;
        height: 38px;
        align-items: center;
        gap: 4px;
        padding: 0 10px;
        border-left: 3px solid var(--studio-marker);
        background: #edf5f6;
    }
    .signal-rail i {
        display: block;
        width: 5px;
        height: var(--level);
        border-radius: 4px;
        background: var(--studio-signal);
        opacity: .82;
    }
    .workflow-label {
        margin: 0 0 10px;
        color: var(--studio-muted);
        font: 700 12px/1.2 "Cascadia Mono", Consolas, monospace;
        letter-spacing: .08em;
        text-transform: uppercase;
    }
    .studio-panel {
        border: 1px solid #dce5ea !important;
        border-radius: 16px !important;
        background: var(--studio-panel) !important;
        box-shadow: 0 8px 28px rgba(23, 32, 51, .05);
    }
    .output-box {
        font-family: "Cascadia Mono", Consolas, monospace !important;
    }
    .primary-action {
        min-height: 48px !important;
        font-weight: 700 !important;
        letter-spacing: .02em;
    }
    @media (prefers-reduced-motion: no-preference) {
        .signal-rail i { animation: signal-breathe 2.8s ease-in-out infinite alternate; }
        .signal-rail i:nth-child(3n) { animation-delay: -.9s; }
        @keyframes signal-breathe { to { opacity: .45; transform: scaleY(.72); } }
    }
    """
    
    # Gradio 6 将 theme/css 从 Blocks 移到了 launch；同时兼容 Gradio 4/5。
    gradio_major = int(gr.__version__.split(".", 1)[0])
    theme = gr.themes.Soft()
    blocks_kwargs = {"title": "音频文本对齐工具"}
    if gradio_major < 6:
        blocks_kwargs.update(css=custom_css, theme=theme)
    app = gr.Blocks(**blocks_kwargs)
    app._txt2srt_launch_kwargs = (
        {"css": custom_css, "theme": theme} if gradio_major >= 6 else {}
    )
    
    with app:
        
        gr.HTML(
            """
            <header class="studio-hero">
              <div class="studio-kicker">TXT → TIMELINE → SRT</div>
              <h1>把准确文稿，落在声音上。</h1>
              <p>上传已有音频与对应文稿，工具会识别人声时间轴，再用你的原文生成可下载字幕。</p>
              <div class="signal-rail" aria-hidden="true">
                <i style="--level:12px"></i><i style="--level:24px"></i>
                <i style="--level:34px"></i><i style="--level:18px"></i>
                <i style="--level:29px"></i><i style="--level:14px"></i>
                <i style="--level:36px"></i><i style="--level:22px"></i>
                <i style="--level:31px"></i><i style="--level:16px"></i>
                <i style="--level:27px"></i><i style="--level:10px"></i>
              </div>
            </header>
            """
        )
        
        with gr.Row():
            # 左侧：输入区域
            with gr.Column(scale=1, elem_classes="studio-panel"):
                gr.Markdown("<div class='workflow-label'>01 · 输入素材</div>")
                
                # 音频文件上传
                audio_input = gr.Audio(
                    label="音频文件",
                    type="filepath",
                    sources=["upload"],
                )
                
                gr.Markdown("<div class='workflow-label'>02 · 准确文稿</div>")
                
                with gr.Tab("直接输入"):
                    text_input = gr.Textbox(
                        label="在此输入文本",
                        placeholder="请输入需要对齐的文本内容...",
                        lines=8,
                    )
                
                with gr.Tab("上传 TXT"):
                    text_file_input = gr.File(
                        label="上传文本文件 (.txt)",
                        file_types=[".txt"],
                    )
                
                gr.Markdown("<div class='workflow-label'>03 · 对齐设置</div>")
                
                model_size = gr.Dropdown(
                    label="模型大小",
                    choices=["Tiny", "Base", "Small", "Medium", "Large", "Large-v3"],
                    value="Small",
                    info="Small 适合大多数中文字幕；模型越大，耗时与显存占用越高"
                )
                
                language = gr.Dropdown(
                    label="语言",
                    choices=["自动检测", "zh", "en", "ja", "ko", "es", "fr", "de"],
                    value="zh",
                    info="已知语言时直接选择，通常比自动检测稳定"
                )

                device = gr.Dropdown(
                    label="运行设备",
                    choices=list(DEVICE_VALUES),
                    value="自动选择",
                    info="自动选择会优先使用可用的 NVIDIA GPU"
                )
                
                max_chars = gr.Slider(
                    label="每行字数限制",
                    minimum=10,
                    maximum=80,
                    value=30,
                    step=5,
                    info="控制单条字幕长度，中文通常推荐 20–40 字"
                )
                
                # 处理按钮
                process_btn = gr.Button(
                    "开始生成字幕",
                    variant="primary",
                    size="lg",
                    elem_classes="primary-action",
                )
            
            # 右侧：输出区域
            with gr.Column(scale=1, elem_classes="studio-panel"):
                gr.Markdown("<div class='workflow-label'>04 · 质量检查与下载</div>")
                
                # 状态信息
                status_output = gr.Textbox(
                    label="处理结果",
                    lines=8,
                    interactive=False,
                    placeholder="完成后会显示运行设备、对齐相似度和需要抽查的风险。"
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
                    label="下载 SRT 文件"
                )
        
        # 底部：使用说明
        with gr.Accordion("使用说明与模型建议", open=False):
            gr.Markdown(
                """
                1. 上传音频，再直接粘贴文稿或上传 TXT；上传 TXT 时以文件内容为准。
                2. 日常中文字幕优先使用 **Small + 中文 + 自动选择**。
                3. 首次使用某个模型会下载权重；之后会优先使用本地缓存并复用内存中的模型。
                4. 完成后先看“对齐相似度”和风险提示。若文稿与音频有删改，请抽查对应时间轴。

                支持 MP3、WAV、M4A、FLAC、OGG 等 FFmpeg 可解码格式。CPU 也能运行，只是长音频耗时更久。
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
                max_chars,
                device,
            ],
            outputs=[
                download_output,
                preview_output,
                status_output
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
    launch_kwargs = {
        "server_name": "127.0.0.1",
        "share": False,
        "inbrowser": True,
        "show_error": True,
        "allowed_paths": None,
    }
    launch_kwargs.update(getattr(app, "_txt2srt_launch_kwargs", {}))
    app.launch(
        **launch_kwargs
    )


if __name__ == "__main__":
    main()

