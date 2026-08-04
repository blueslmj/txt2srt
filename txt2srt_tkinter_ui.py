#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音频-文本对齐工具 - Tkinter UI界面
传统桌面应用界面，无需额外依赖
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from txt2srt import (
    Txt2SrtError,
    align_audio_text,
    format_timestamp,
    generate_srt,
    read_text_file,
)


class AudioTextAlignerUI:
    """音频文本对齐工具的GUI界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("音频-文本对齐工具")
        self.root.geometry("900x700")
        
        # 变量
        self.audio_path = tk.StringVar()
        self.text_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.model_size = tk.StringVar(value="small")
        self.language = tk.StringVar(value="zh")
        self.device = tk.StringVar(value="auto")
        self.max_chars = tk.IntVar(value=30)
        
        self.is_processing = False
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="🎵 音频-文本对齐工具",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        subtitle_label = ttk.Label(
            main_frame,
            text="自动将音频和文本对齐，生成SRT字幕文件",
            font=("Arial", 10)
        )
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10
        )
        
        # === 输入区域 ===
        input_frame = ttk.LabelFrame(main_frame, text="📥 输入文件", padding="10")
        input_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 音频文件
        ttk.Label(input_frame, text="音频文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.audio_path, width=50).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(input_frame, text="浏览...", command=self.browse_audio).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        # 文本文件
        ttk.Label(input_frame, text="文本文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.text_path, width=50).grid(
            row=1, column=1, padx=5, pady=5
        )
        ttk.Button(input_frame, text="浏览...", command=self.browse_text).grid(
            row=1, column=2, padx=5, pady=5
        )
        
        # 输出文件
        ttk.Label(input_frame, text="输出文件:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.output_path, width=50).grid(
            row=2, column=1, padx=5, pady=5
        )
        ttk.Button(input_frame, text="浏览...", command=self.browse_output).grid(
            row=2, column=2, padx=5, pady=5
        )
        
        # === 设置区域 ===
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ 设置", padding="10")
        settings_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 模型大小
        ttk.Label(settings_frame, text="模型大小:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        model_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.model_size,
            values=["tiny", "base", "small", "medium", "large"],
            state="readonly",
            width=15
        )
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(settings_frame, text="(small=推荐, medium=更准确)").grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        # 语言
        ttk.Label(settings_frame, text="语言:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        lang_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.language,
            values=["zh", "en", "ja", "ko", "auto"],
            state="readonly",
            width=15
        )
        lang_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(settings_frame, text="(zh=中文, en=英文, auto=自动)").grid(
            row=1, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        # 运行设备
        ttk.Label(settings_frame, text="运行设备:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        device_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.device,
            values=["auto", "cuda", "cpu"],
            state="readonly",
            width=15
        )
        device_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(settings_frame, text="(auto=自动选择, cuda=NVIDIA GPU)").grid(
            row=2, column=2, sticky=tk.W, padx=5, pady=5
        )

        # 每行字数限制
        ttk.Label(settings_frame, text="每行字数:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        chars_frame = ttk.Frame(settings_frame)
        chars_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        self.chars_scale = ttk.Scale(
            chars_frame,
            from_=10,
            to=80,
            variable=self.max_chars,
            orient=tk.HORIZONTAL,
            length=150,
            command=self.update_chars_label
        )
        self.chars_scale.pack(side=tk.LEFT)
        
        self.chars_label = ttk.Label(chars_frame, text="30 字", width=8)
        self.chars_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(chars_frame, text="(推荐20-40字)").pack(side=tk.LEFT)
        
        # === 处理按钮 ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=15)
        
        self.process_btn = ttk.Button(
            button_frame,
            text="🚀 开始处理",
            command=self.process,
            width=20
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(
            button_frame,
            text="🗑️ 清空",
            command=self.clear_all,
            width=15
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # === 进度条 ===
        self.progress = ttk.Progressbar(
            main_frame,
            mode='determinate',
            maximum=100,
            length=400
        )
        self.progress.grid(row=6, column=0, columnspan=3, pady=5)
        
        # === 日志区域 ===
        log_frame = ttk.LabelFrame(main_frame, text="📋 处理日志", padding="10")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            width=80,
            height=15,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置窗口权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
    def log(self, message):
        """添加日志消息"""
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, self.log, message)
            return
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_progress(self, value, message=None):
        """从工作线程安全地更新进度与阶段说明。"""
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, self.update_progress, value, message)
            return
        self.progress.configure(value=max(0, min(100, float(value) * 100)))
        if message:
            self.log(f"[{float(value):.0%}] {message}")

    def set_processing_state(self, processing):
        """在主线程切换按钮和进度条状态。"""
        self.process_btn.config(state=tk.DISABLED if processing else tk.NORMAL)
        if not processing:
            self.progress.configure(value=0)
        
    def browse_audio(self):
        """浏览音频文件"""
        filename = filedialog.askopenfilename(
            title="选择音频文件",
            filetypes=[
                ("音频文件", "*.mp3 *.wav *.m4a *.flac *.ogg"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.audio_path.set(filename)
            # 自动设置输出路径
            if not self.output_path.get():
                base_name = os.path.splitext(filename)[0]
                self.output_path.set(base_name + ".srt")
            
    def browse_text(self):
        """浏览文本文件"""
        filename = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.text_path.set(filename)
            
    def browse_output(self):
        """浏览输出文件"""
        filename = filedialog.asksaveasfilename(
            title="保存SRT文件",
            defaultextension=".srt",
            filetypes=[
                ("SRT字幕文件", "*.srt"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.output_path.set(filename)
            
    def update_chars_label(self, value):
        """更新字数标签"""
        self.chars_label.config(text=f"{int(float(value))} 字")
    
    def clear_all(self):
        """清空所有输入"""
        if self.is_processing:
            messagebox.showwarning("警告", "任务正在处理中，暂时不能清空")
            return
        self.audio_path.set("")
        self.text_path.set("")
        self.output_path.set("")
        self.log_text.delete(1.0, tk.END)
        
    def process(self):
        """处理音频和文本"""
        if self.is_processing:
            messagebox.showwarning("警告", "正在处理中，请稍候...")
            return
        
        # 验证输入
        if not self.audio_path.get():
            messagebox.showerror("错误", "请选择音频文件")
            return
        
        if not self.text_path.get():
            messagebox.showerror("错误", "请选择文本文件")
            return
        
        if not self.output_path.get():
            messagebox.showerror("错误", "请指定输出文件路径")
            return

        task = {
            "audio_path": self.audio_path.get(),
            "text_path": self.text_path.get(),
            "output_path": self.output_path.get(),
            "model": self.model_size.get(),
            "language": self.language.get(),
            "device": self.device.get(),
            "max_chars": self.max_chars.get(),
        }
        self.is_processing = True
        self.set_processing_state(True)

        # 在新线程中处理，避免阻塞UI
        thread = threading.Thread(
            target=self.process_thread,
            args=(task,),
            name="txt2srt-worker",
        )
        thread.daemon = True
        thread.start()
        
    def process_thread(self, task):
        """处理线程"""
        try:
            self.log("=" * 60)
            self.log("🚀 开始处理...")
            self.log(f"📁 音频文件: {os.path.basename(task['audio_path'])}")
            self.log(f"📝 文本文件: {os.path.basename(task['text_path'])}")
            self.log(f"🎯 模型大小: {task['model']}")
            self.log(f"🌏 语言: {task['language']}")
            self.log(f"🖥️ 运行设备: {task['device']}")
            self.log(f"📏 每行字数: {task['max_chars']} 字")
            self.log("")
            
            # 读取文本
            text_content = read_text_file(task["text_path"])
            
            self.log(f"📄 文本长度: {len(text_content)} 字符")
            self.log("")
            self.log("⏳ 正在使用Whisper模型进行语音识别...")
            self.log("   (首次运行会下载模型，请耐心等待)")
            self.log("")
            
            # 处理音频
            lang = None if task["language"] == "auto" else task["language"]
            diagnostics = {}
            segments = align_audio_text(
                task["audio_path"],
                text_content,
                model_name=task["model"],
                max_chars=task["max_chars"],
                language=lang,
                device=task["device"],
                progress_callback=self.update_progress,
                diagnostics=diagnostics,
            )
            
            self.log(f"✅ 语音识别完成！识别到 {len(segments)} 个段落")
            self.log("")
            
            # 生成SRT
            generate_srt(segments, task["output_path"])
            
            self.log(f"✅ SRT文件已生成: {task['output_path']}")
            self.log("")
            self.log("📊 统计信息:")
            self.log(f"   - 字幕段落数: {len(segments)}")
            self.log(f"   - 音频时长: {segments[-1]['end']:.2f} 秒")
            self.log(
                f"   - 识别后端: {diagnostics.get('backend', 'Whisper')} / "
                f"{str(diagnostics.get('device', task['device'])).upper()}"
            )
            self.log(f"   - 对齐相似度: {diagnostics.get('similarity', 0):.0%}")
            for warning in diagnostics.get("warnings", []):
                self.log(f"   - ⚠️ {warning}")
            self.log("")
            
            # 显示前3个段落预览
            self.log("📄 字幕预览 (前3个段落):")
            self.log("-" * 60)
            for i, seg in enumerate(segments[:3], 1):
                start = format_timestamp(seg['start'])
                end = format_timestamp(seg['end'])
                self.log(f"{i}")
                self.log(f"{start} --> {end}")
                self.log(f"{seg['text']}")
                self.log("")
            
            if len(segments) > 3:
                self.log(f"... (还有 {len(segments) - 3} 个段落)")
            
            self.log("=" * 60)
            self.log("✨ 全部完成！")
            self.log("")
            
            # 显示成功消息
            self.root.after(0, lambda: messagebox.showinfo(
                "处理完成",
                f"字幕文件已成功生成！\n\n"
                f"文件位置: {task['output_path']}\n"
                f"段落数量: {len(segments)}\n"
                f"音频时长: {segments[-1]['end']:.2f} 秒"
            ))
            
        except Txt2SrtError as e:
            self.log("")
            self.log(f"❌ 处理失败: {str(e)}")
            self.root.after(0, lambda error=str(e): messagebox.showerror(
                "处理失败", error
            ))
        except Exception as e:
            self.log("")
            self.log(f"❌ 处理出错: {str(e)}")
            self.log("")
            self.root.after(0, lambda error=str(e): messagebox.showerror(
                "处理错误",
                f"处理过程中出现错误:\n\n{error}"
            ))
            
        finally:
            self.is_processing = False
            self.root.after(0, self.set_processing_state, False)


def main():
    """启动Tkinter应用"""
    root = tk.Tk()
    app = AudioTextAlignerUI(root)
    
    # 设置图标和样式
    try:
        root.iconbitmap(default='')  # 可以添加图标
    except:
        pass
    
    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()

