# 音频-文本对齐工具 (txt2srt)

将音频和文本对齐，自动生成SRT字幕文件。

## 功能特点

- 🎵 支持多种音频格式 (MP3, WAV, M4A, FLAC, OGG等)
- 📝 自动将文本与音频对齐
- ⏱️ 精确的时间戳生成
- 🌏 支持中文、英文等多种语言
- 🚀 基于OpenAI Whisper模型，准确度高
- 🖥️ **提供两种UI界面：Web界面（Gradio）和桌面界面（Tkinter）**

## 安装步骤

### 1. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
venv\Scripts\pip install -r requirements.txt
```

**注意**: 首次运行时，Whisper会自动下载模型文件（约140MB-2.9GB，取决于模型大小）

## 使用方法

### 🎨 方式1：图形界面（推荐新手）

#### Gradio Web界面（推荐）
```bash
# 启动Web界面
start_ui.bat

# 或手动启动
venv\Scripts\python txt2srt_ui.py
```

浏览器会自动打开 http://127.0.0.1:7860

**特点**：现代化、美观、支持拖拽上传

#### Tkinter桌面界面
```bash
# 启动桌面界面
start_tkinter_ui.bat

# 或手动启动
venv\Scripts\python txt2srt_tkinter_ui.py
```

**特点**：传统桌面应用、无需额外依赖

📖 **详细UI使用说明请查看：[UI_GUIDE.md](UI_GUIDE.md)**

---

### 💻 方式2：命令行（适合批量处理）

#### 基本用法

```bash
# Windows (在venv环境中)
venv\Scripts\python txt2srt.py audio.mp3 text.txt

# Linux/Mac (在venv环境中)
python txt2srt.py audio.mp3 text.txt
```

### 参数说明

```
txt2srt.py [-h] [-o OUTPUT] [-m MODEL] [-l LANGUAGE] audio text

位置参数:
  audio                 输入音频文件路径
  text                  输入文本文件路径（或直接输入文本）

可选参数:
  -h, --help            显示帮助信息
  -o OUTPUT, --output   输出SRT文件路径（默认: audio_name.srt）
  -m MODEL, --model     Whisper模型大小（默认: base）
                        可选: tiny, base, small, medium, large
  -l LANGUAGE           语言代码（默认: zh）
                        zh=中文, en=英文, None=自动检测
```

### 使用示例

#### 示例1: 基本使用（中文音频）

```bash
venv\Scripts\python txt2srt.py speech.mp3 transcript.txt
```

#### 示例2: 指定输出文件

```bash
venv\Scripts\python txt2srt.py speech.mp3 transcript.txt -o output.srt
```

#### 示例3: 使用更大的模型（更准确但更慢）

```bash
venv\Scripts\python txt2srt.py speech.mp3 transcript.txt -m medium
```

#### 示例4: 英文音频

```bash
venv\Scripts\python txt2srt.py english.mp3 transcript.txt -l en
```

#### 示例5: 直接输入文本（不使用文件）

```bash
venv\Scripts\python txt2srt.py audio.mp3 "这是要对齐的文本内容"
```

## Whisper模型说明

| 模型 | 参数量 | 英文准确度 | 多语言准确度 | 相对速度 | 磁盘空间 |
|------|--------|------------|--------------|----------|----------|
| tiny | 39M    | 低         | 低           | ~32x     | ~75MB    |
| base | 74M    | 中         | 中           | ~16x     | ~140MB   |
| small| 244M   | 较高       | 较高         | ~6x      | ~460MB   |
| medium| 769M  | 高         | 高           | ~2x      | ~1.5GB   |
| large| 1550M  | 最高       | 最高         | 1x       | ~2.9GB   |

**建议**: 
- 快速测试: 使用 `tiny` 或 `base`
- 生产环境: 使用 `small` 或 `medium`
- 最高质量: 使用 `large`

## 输出格式

生成的SRT文件格式示例：

```
1
00:00:00,000 --> 00:00:03,500
这是第一句字幕内容

2
00:00:03,500 --> 00:00:07,200
这是第二句字幕内容

3
00:00:07,200 --> 00:00:10,800
这是第三句字幕内容
```

## 技术原理

### 真正的文本对齐 ⭐

本工具实现了**真正的音频-文本对齐**，而不只是语音识别：

1. **Whisper识别音频** → 获取精确的时间戳（词级/段落级）
2. **分析用户文本** → 智能分割成合适的字幕段落
3. **智能对齐算法** → 将用户文本与时间戳精确匹配
4. **生成SRT字幕** → 使用**用户的准确文本** + **Whisper的精确时间**

**优势**：
- ✅ 字幕内容使用用户提供的准确文本（无识别错误）
- ✅ 时间戳来自Whisper的精确识别
- ✅ 支持GPU加速，处理速度提升10-50倍

📖 详细说明：[ALIGNMENT_GUIDE.md](ALIGNMENT_GUIDE.md)

## 系统要求

- Python 3.10-3.13（推荐3.12或3.13）
- **推荐使用GPU加速**（速度提升10-50倍）
  - NVIDIA GPU（支持CUDA）
  - 📖 GPU配置指南：[GPU_SETUP.md](GPU_SETUP.md)
- 至少4GB可用内存（取决于模型大小）
- 🔍 检查GPU：运行 `check_gpu.bat`

## 支持的音频格式

本工具支持 **50+ 种音频格式**，包括：
- 常见格式：MP3, WAV, M4A, FLAC, OGG
- 无损格式：FLAC, WAV, AIFF
- 视频格式：MP4, AVI, MKV（直接提取音频）

📖 **详细格式说明**: [SUPPORTED_FORMATS.md](SUPPORTED_FORMATS.md)

## 常见问题

### Q: 首次运行很慢？
A: Whisper会在首次运行时下载模型文件，这是正常现象。

### Q: 如何提高准确度？
A: 使用更大的模型（如 medium 或 large），并确保音频质量清晰。

### Q: 支持哪些语言？
A: Whisper支持99种语言，包括中文、英文、日语、韩语等。

### Q: 可以处理多长的音频？
A: 理论上没有限制，但处理时间与音频长度成正比。

## 许可证

MIT License

