# 🎵 支持的音频格式

## 完整格式列表

本工具基于 **OpenAI Whisper** 和 **FFmpeg**，支持几乎所有常见的音频格式。

### ✅ 主要支持的格式

| 格式 | 扩展名 | 特点 | 推荐使用场景 |
|------|--------|------|-------------|
| **MP3** | `.mp3` | 常见、压缩、小文件 | 日常音频、播客 |
| **WAV** | `.wav` | 无损、大文件 | 高质量录音、专业制作 |
| **M4A** | `.m4a` | 压缩、Apple设备 | iPhone录音、Apple生态 |
| **FLAC** | `.flac` | 🆕 **无损压缩** | 高质量音频、音乐 |
| **OGG** | `.ogg` | 开源、压缩 | 开源项目、游戏音频 |

### ✅ 其他支持的格式

- **AAC** (`.aac`) - 高质量压缩
- **WMA** (`.wma`) - Windows Media
- **OPUS** (`.opus`) - 新一代编码
- **AMR** (`.amr`) - 移动设备录音
- **AIFF** (`.aiff`, `.aif`) - Apple无损格式

### 🎬 视频格式支持

工具也可以直接从视频文件中提取音频：

- **MP4** (`.mp4`)
- **AVI** (`.avi`)
- **MKV** (`.mkv`)
- **MOV** (`.mov`)
- **FLV** (`.flv`)
- **WEBM** (`.webm`)

**注意**：处理视频文件时，只会提取音频轨道进行识别。

---

## 🌟 FLAC 格式详解

### 什么是 FLAC？

**FLAC** (Free Lossless Audio Codec) 是一种**无损音频压缩格式**：

- ✅ **无损压缩**：音质与原始 WAV 完全相同
- ✅ **文件更小**：比 WAV 小 30-50%
- ✅ **开源免费**：无专利限制
- ✅ **广泛支持**：主流播放器都支持

### FLAC vs 其他格式

| 特性 | FLAC | WAV | MP3 |
|------|------|-----|-----|
| 音质 | 🟢 无损 | 🟢 无损 | 🟡 有损 |
| 文件大小 | 🟢 中等 | 🔴 大 | 🟢 小 |
| 兼容性 | 🟢 好 | 🟢 极好 | 🟢 极好 |
| 速度 | 🟢 快 | 🟢 快 | 🟢 快 |

### 使用建议

**推荐使用 FLAC 如果：**
- 🎵 需要高质量音频对齐
- 💾 希望节省存储空间（相比 WAV）
- 🎙️ 处理音乐、高质量录音
- 📚 长期存档音频文件

**使用 MP3 如果：**
- ⚡ 追求最小文件大小
- 🌐 需要最广泛的兼容性
- 📱 移动设备录音

---

## 💡 使用示例

### 处理 FLAC 文件（Web界面）

1. **启动界面**：
   ```bash
   start_ui.bat
   ```

2. **上传 FLAC 文件**：
   - 拖拽 `.flac` 文件到上传区
   - 或点击选择 FLAC 文件

3. **正常处理**：
   - 输入或上传文本
   - 点击"开始处理"
   - 下载生成的 SRT 文件

### 处理 FLAC 文件（命令行）

```bash
# 基本用法
venv\Scripts\python txt2srt.py audio.flac transcript.txt

# 指定输出文件
venv\Scripts\python txt2srt.py music.flac lyrics.txt -o music.srt

# 使用高质量模型
venv\Scripts\python txt2srt.py concert.flac script.txt -m medium
```

### 批量处理 FLAC 文件

创建 Python 脚本 `batch_process_flac.py`：

```python
from txt2srt import align_audio_text, generate_srt
import os

# FLAC 文件目录
flac_dir = "flac_files/"
text_dir = "transcripts/"
output_dir = "subtitles/"

# 获取所有 FLAC 文件
flac_files = [f for f in os.listdir(flac_dir) if f.endswith('.flac')]

for flac_file in flac_files:
    print(f"处理: {flac_file}")
    
    # 构建路径
    audio_path = os.path.join(flac_dir, flac_file)
    text_file = flac_file.replace('.flac', '.txt')
    text_path = os.path.join(text_dir, text_file)
    output_path = os.path.join(output_dir, flac_file.replace('.flac', '.srt'))
    
    # 读取文本
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 处理并生成SRT
    segments = align_audio_text(audio_path, text, model_name="base")
    generate_srt(segments, output_path)
    
    print(f"✅ 完成: {output_path}\n")
```

---

## 🔧 格式转换

### 转换其他格式为 FLAC

如果你有其他格式的音频，可以先转换为 FLAC：

#### 使用 FFmpeg（推荐）

```bash
# WAV → FLAC
ffmpeg -i input.wav output.flac

# MP3 → FLAC
ffmpeg -i input.mp3 output.flac

# M4A → FLAC
ffmpeg -i input.m4a output.flac

# 批量转换当前目录所有 WAV 文件
for %f in (*.wav) do ffmpeg -i "%f" "%~nf.flac"
```

#### 使用 Python (pydub)

```python
from pydub import AudioSegment

# 加载音频
audio = AudioSegment.from_file("input.mp3")

# 导出为 FLAC
audio.export("output.flac", format="flac")
```

---

## ❓ 常见问题

### Q1: FLAC 文件处理速度会更慢吗？
**A**: 不会。FLAC 是无损压缩，解码速度与 WAV 相当，比 MP3 还要快。

### Q2: FLAC 文件能提高识别准确度吗？
**A**: 理论上会更好，因为无损音质保留了更多细节。实际使用中：
- 对于高质量录音：FLAC ≈ WAV > MP3
- 对于普通录音：差异不明显

### Q3: 是否需要特殊设置来处理 FLAC？
**A**: 不需要！直接上传或选择 FLAC 文件即可，工具会自动识别和处理。

### Q4: 可以直接从 CD 抓取 FLAC 并处理吗？
**A**: 可以！
1. 使用 CD 抓取工具（如 EAC、dBpoweramp）抓取为 FLAC
2. 准备对应的文本
3. 使用本工具生成字幕

### Q5: 所有设备都支持 FLAC 吗？
**A**: 大部分现代设备都支持：
- ✅ Windows、macOS、Linux
- ✅ Android 4.1+
- ✅ iOS 11+ (需要第三方播放器)
- ✅ 主流媒体播放器

---

## 📊 格式选择建议

### 根据来源选择：

| 音频来源 | 推荐格式 | 原因 |
|---------|---------|------|
| CD 抓取 | FLAC | 保持无损品质 |
| 录音笔/话筒 | FLAC/WAV | 高质量原始录音 |
| 手机录音 | M4A/MP3 | 设备默认格式 |
| 在线下载 | MP3 | 常见格式 |
| 视频提取 | 直接用视频 | 无需转换 |

### 根据用途选择：

| 使用场景 | 推荐格式 | 原因 |
|---------|---------|------|
| 音乐字幕 | FLAC | 高音质要求 |
| 播客字幕 | MP3 | 平衡质量和大小 |
| 讲座/课程 | MP3/M4A | 语音为主 |
| 专业制作 | WAV/FLAC | 最高质量 |

---

## 🎯 最佳实践

1. **高质量源音频**
   - 优先使用 FLAC 或 WAV
   - 避免多次转码的音频
   - 确保采样率至少 16kHz

2. **文件准备**
   - 清除背景噪音
   - 标准化音量
   - 切分过长的音频（建议 < 30分钟）

3. **模型选择**
   - FLAC 高质量音频 → 使用 Small 或 Medium 模型
   - 普通 MP3 → 使用 Base 模型即可

---

## 📞 技术支持

如果遇到特定格式的问题：

1. 确认 FFmpeg 已正确安装（随 Whisper 自动安装）
2. 尝试先用 FFmpeg 测试文件：
   ```bash
   ffmpeg -i your_audio.flac -f null -
   ```
3. 如果格式不支持，可以先转换为 WAV 或 FLAC

---

**更新日期**：2025年11月  
**支持的格式**：50+ 种音频/视频格式

