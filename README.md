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
- 🧭 **设备可控**：支持 `auto / cpu / cuda`，无 CUDA 时可自动回退 CPU
- 💾 **本地存储**：模型固定下载到项目 `models`，不写入用户级 Hugging Face/Whisper 缓存
- 🩺 **质量诊断**：输出文稿/识别文本相似度、字符差异和需要抽查的风险提示
- 📚 **长文本保护**：长文稿自动切换低内存对齐模式，避免 DTW 距离矩阵耗尽内存

## 安装步骤

### Windows 一键安装（推荐）

双击 `setup.bat`，或在终端执行：

```powershell
setup.bat
```

安装器会自动完成：

1. 定位或安装用户级 Python 3.12。
2. 检测 NVIDIA 显卡名称、计算能力和驱动。
3. 在 CUDA 13、CUDA 12.6、CPU 三种 PyTorch profile 中自动选择。
4. 创建或修复项目本地 `venv`，安装通用依赖；pip 下载过程禁用用户级缓存。
5. 执行 `pip check`、CUDA FP16 和关键运行库验证。

| 检测结果 | 自动安装模式 |
| --- | --- |
| RTX 50 / Blackwell（计算能力 12.x） | PyTorch CUDA 13.0；缺少 CUDA 12 运行库时询问安装 Toolkit 12.8 |
| 其他受支持的 NVIDIA 显卡（计算能力 5.x–11.x） | PyTorch CUDA 12.6 兼容模式 |
| AMD / Intel 显卡、无独显或无法识别 NVIDIA | CPU 通用模式 |

需要覆盖自动判断时，可以指定 profile：

```powershell
setup.bat cpu
setup.bat nvidia-modern
setup.bat nvidia-legacy
```

只查看检测结果、不修改环境：

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -DryRun -NonInteractive
```

### 手动安装（Linux/macOS/高级用户）

先根据 [PyTorch 官方安装选择器](https://docs.pytorch.org/get-started/locally/)安装适合硬件的 `torch/torchaudio`，再安装通用依赖：

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
python -m pip install --no-cache-dir -r requirements-common.txt
```

首次运行某个 Whisper 模型时，会自动下载模型，所有运行数据均位于项目下面：

| 目录 | 内容 | 可以删除吗 |
| --- | --- | --- |
| `venv` | Python、PyTorch 和项目依赖 | 可以；删除后需重新运行 `setup.bat` |
| `models` | Faster-Whisper、OpenAI Whisper、Hugging Face 和 Torch 模型 | 可以；删除后会按需重新下载 |
| `.runtime` | Gradio 上传副本、临时文件、Numba/CUDA 运行缓存 | 可以；关闭程序后可随时删除 |

程序会覆盖外部 `HF_HOME`、`TORCH_HOME`、`TEMP` 等缓存变量，保证本项目不会把新增文件写进用户缓存目录。需要彻底清理时，关闭程序后直接删除上述三个目录即可。Python、显卡驱动和 CUDA Toolkit 属于系统组件，不在项目清理范围内。

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
txt2srt.py [-h] [-o OUTPUT] [-m MODEL] [-l LANGUAGE]
           [-c MAX_CHARS] [--device {auto,cpu,cuda}] audio text

位置参数:
  audio                 输入音频文件路径
  text                  输入文本文件路径（或直接输入文本）

可选参数:
  -h, --help            显示帮助信息
  -o OUTPUT, --output   输出SRT文件路径（默认: audio_name.srt）
  -m MODEL, --model     Whisper模型大小（默认: small）
                        可选: tiny, base, small, medium, large, large-v2, large-v3
  -l LANGUAGE           语言代码（默认: zh）
                        zh=中文, en=英文, auto=自动检测
  -c MAX_CHARS, --max-chars MAX_CHARS
                        每条字幕最大字数（默认: 30）
  --device {auto,cpu,cuda}
                        运行设备（默认: auto）
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

#### 示例4: 强制使用CPU并自动检测语言

```bash
venv\Scripts\python txt2srt.py speech.mp3 transcript.txt --device cpu -l auto
```

### Python接口

```python
from txt2srt import generate_srt_from_audio

result = generate_srt_from_audio(
    "speech.mp3",
    "这里是准确文稿。",
    model_name="small",
    language="zh",
    device="auto",
    max_chars=30,
)

print(result["srt_path"])
print(result["meta"]["similarity"])
print(result["warnings"])
```

返回值包含 SRT 路径、字幕段落、模型/设备/对齐质量元数据，以及需要人工抽查的告警。

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
3. **自适应文本对齐** → 常规文本使用 DTW；长文本自动使用低内存序列对齐
4. **质量诊断** → 计算文本相似度和字符差异，提示可能不匹配的文稿
5. **智能平滑** → 修复重叠并适度填补句间空隙
6. **生成结果** → 使用用户原文输出标准 SRT

📖 详细说明：[ALIGNMENT_GUIDE.md](ALIGNMENT_GUIDE.md)

## 系统要求

- Python 3.10-3.13（推荐3.12）
- **强烈推荐使用 NVIDIA 显卡**（支持 CUDA 11.8/12.x）
- 至少 4GB 显存（运行 Large 模型建议 8GB+）
- CPU 模式虽然支持，但速度无法享受到 GPU 的数十倍加速

## 常见问题

### Q: 为什么完成后提示“需要抽查”？
A: Whisper 识别文本与上传文稿的字符数或内容差异较大。工具仍会生成 SRT，但建议抽查删句、增句附近的时间轴。

### Q: 没有 NVIDIA 显卡能运行吗？
A: 可以。Web/桌面界面选择“自动选择”，命令行使用 `--device auto`；CUDA 不可用时会走 CPU。

### Q: 报错 `cuBLAS failed` 或 `CUBLAS_STATUS_NOT_SUPPORTED`？
A: 代码已默认使用兼容性最好的 `float16` 精度。如果仍报错，请确保您的显卡驱动已更新到最新版本。

### Q: 首次运行很慢？
A: Faster-Whisper 需要从 HuggingFace 下载转换后的模型权重，这只会在第一次使用某个尺寸的模型时发生。

### Q: 原版 Whisper 模型通用吗？
A: 不通用。Faster-Whisper 使用 CTranslate2 格式，会自动下载。原版 `.pt` 文件无法直接加载。

## 许可证

MIT License

