# 音频-文本对齐工具 (txt2srt)

将音频和文本对齐，自动生成SRT字幕文件。

## 功能特点

- 🎵 支持多种音频格式 (MP3, WAV, M4A, FLAC, OGG等)
- 📝 自动将文本与音频对齐
- ⏱️ 精确的时间戳生成
- 🌏 支持中文、英文等多种语言
- **🚀 性能飞跃**：集成 **Faster-Whisper (CTranslate2)** 引擎，推理速度最高提升 **50倍**！
- **✨ 观感优化**：新增智能字幕平滑算法，消除字幕微光/闪烁，自动填补句间空隙，观感流畅自然。
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

**注意**: 首次运行时，程序会自动从 HuggingFace 下载 **Faster-Whisper** 转换版模型（与原版 OpenAI 模型通用，但目录结构不同）。

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

**特点**：现代化、美观、支持拖拽上传、**实时进度显示**。

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

## Whisper模型与性能说明

基于 RTX 30/40系列显卡的测试数据：

| 模型 | 参数量 | 英文准确度 | 中文准确度 | 原版速度 | Faster-Whisper速度 | 磁盘空间 |
|------|--------|------------|--------------|----------|-------------------|----------|
| tiny | 39M    | 低         | 低           | ~32x     | **~100x+**        | ~75MB    |
| base | 74M    | 中         | 中           | ~16x     | **~80x**          | ~140MB   |
| small| 244M   | 较高       | 较高         | ~6x      | **~40x**          | ~460MB   |
| medium| 769M  | 高         | 高           | ~2x      | **~15x**          | ~1.5GB   |
| large| 1550M  | 最高       | 最高         | 1x       | **~8x**           | ~2.9GB   |

**建议**: 
- **日常使用**: 推荐 **small** 模型，在 Faster-Whisper 加持下速度飞快且精度足够。
- **高精度**: 使用 `large-v3`，即使是 Large 模型现在也能跑出不错的速度。

## 输出格式

生成的SRT文件已包含**观感优化**：

```
1
00:00:00,000 --> 00:00:03,500
这是第一句字幕内容

2
00:00:03,500 --> 00:00:07,200
这是第二句字幕内容（此处空隙已被自动填补，避免闪烁）

...
```

## 技术原理

### 1. 下一代推理引擎
本项目采用了 **CTranslate2 (Faster-Whisper)** 作为推理后端，相比原版 OpenAI Whisper：
- **Int8/Float16 混合精度**：在不损失精度的情况下大幅减少显存占用。
- **VAD 过滤**：自动检测并跳过静音片段，不再对空白音频浪费算力。

### 2. 真正的文本对齐 ⭐
1. **Whisper识别** → 获取精确的时间戳（启用 VAD）
2. **分析用户文本** → 智能分割成合适的字幕段落
3. **DTW 算法对齐** → 将用户文本与时间戳精确匹配
4. **智能平滑** → 应用 `optimize_subtitle_duration` 算法，消除字幕微光，填补句间空隙
5. **生成结果** → 输出完美对齐且观感极佳的 SRT

📖 详细说明：[ALIGNMENT_GUIDE.md](ALIGNMENT_GUIDE.md)

## 系统要求

- Python 3.10-3.13（推荐3.12）
- **强烈推荐使用 NVIDIA 显卡**（支持 CUDA 11.8/12.x）
- 至少 4GB 显存（运行 Large 模型建议 8GB+）
- CPU 模式虽然支持，但速度无法享受到 GPU 的数十倍加速

## 常见问题

### Q: 报错 `cuBLAS failed` 或 `CUBLAS_STATUS_NOT_SUPPORTED`？
A: 代码已默认使用兼容性最好的 `float16` 精度。如果仍报错，请确保您的显卡驱动已更新到最新版本。

### Q: 首次运行很慢？
A: Faster-Whisper 需要从 HuggingFace 下载转换后的模型权重，这只会在第一次使用某个尺寸的模型时发生。

### Q: 原版 Whisper 模型通用吗？
A: 不通用。Faster-Whisper 使用 CTranslate2 格式，会自动下载。原版 `.pt` 文件无法直接加载。

## 许可证

MIT License

