# txt2srt 性能与体验优化技术方案

本方案基于在 `IndexTTS` 项目中的成功实践，旨在将两项核心改进（Faster-Whisper 高速推理、字幕观感优化）迁移至 `txt2srt` 项目。

## 1. 性能优化：集成 Faster-Whisper

### 1.1 背景与收益
原版 `openai-whisper` 虽然精度高，但推理速度较慢，显存占用较高。
`faster-whisper` 是基于 **CTranslate2**（C++ 实现的高效推理引擎）的重构版本。

*   **速度提升**：在 GPU 上通常有 **4~10 倍** 的提速（使用 int8 量化）。
*   **显存优化**：大幅降低显存占用，允许在小显存显卡上运行更大的模型。
*   **精度保持**：使用原有模型权重转换，精度几乎无损。

### 1.2 实施步骤

#### A. 环境依赖
确保安装了 `faster-whisper` 以及 `stable-ts`（推荐使用 `stable-ts` 作为上层封装，它对 `faster-whisper` 提供了良好的兼容性）。
```bash
pip install faster-whisper stable-ts
```
*注：Windows 用户需要确保已安装 CUDA Toolkit (推荐 11.8 或 12.x) 和 cuDNN。*

#### B. 代码改造
在加载模型只需要更改一行代码。

**原有代码 (OpenAI Whisper):**
```python
import stable_whisper
model = stable_whisper.load_model("small", device="cuda")
result = model.transcribe("audio.wav")
```

**优化后代码 (Faster-Whisper):**
```python
import stable_whisper

# 使用 load_faster_whisper 加载
# device="cuda" 默认会使用 float16，如需 int8 可添加 compute_type="int8"
model = stable_whisper.load_faster_whisper("small", device="cuda", compute_type="float16")

result = model.transcribe(
    "audio.wav",
    beam_size=1,      # 强制使用 Greedy Loading，大幅进一步提速 (对齐任务精度损失极小)
    temperature=0,
    word_timestamps=True
)
```

---

## 2. 体验优化：字幕微调 (消除闪烁感)

### 2.1 问题痛点
Whisper 生成的时间戳是基于音频 VAD (语音活动检测) 的，非常精准地卡在说话结束的那一毫秒。
**后果**：
- 说话人A说完，字幕立即消失。
- 此时到说话人B开始说话之间可能有 0.5秒~1.0秒 的停顿。
- 这段时间屏幕上**没有字幕**，导致字幕频繁“闪烁”，观感非常累。

### 2.2 优化算法
在获取到对齐后的字幕片段（Segments）后，执行一遍**“间隙填补” (Gap Filling)** 算法。

**逻辑规则**：
1.  **遍历所有段落**：检查 `当前句.end` 和 `下一句.start` 之间的时间差 (`gap`).
2.  **填补策略**：
    - 如果 `gap > 0`，说明有空隙。
    - 延长 `当前句.end`，使其接近 `下一句.start`。
    - **保留呼吸空间**：保留 0.1秒 的微小间隙（`gap - 0.1`），避免字幕连成一片分不清换句。
    - **设置上限**：限制最大延长时间（建议 **0.5秒**）。如果空隙是 2秒（长停顿），只延长 0.5秒，避免人都不说话了字幕还挂着。
3.  **末句处理**：强制延长最后一句字幕 0.5~1.0秒，防止音频未完全淡出字幕就消失。

### 2.3 代码实现 (Python)
此函数可直接插入到 SRT 生成管线中，在生成 SRT 文本之前调用。

```python
from typing import List, Dict

def optimize_subtitle_duration(segments: List[Dict], max_extension: float = 0.5) -> List[Dict]:
    """
    优化字幕持续时间：填补句间空隙，提升观感
    args:
        segments: 包含 {"start": float, "end": float, "text": str} 的列表
        max_extension: 最大自动延长时间（秒），建议 0.5
    """
    if not segments:
        return segments

    # 遍历（除了最后一句）
    for i in range(len(segments) - 1):
        curr_seg = segments[i]
        next_seg = segments[i+1]
        
        # 计算两句之间的空隙
        gap = next_seg["start"] - curr_seg["end"]
        
        if gap > 0:
            # 策略：填补空隙，但保留 0.1s 间隔，且不超过最大延长阈值
            extend_by = min(max_extension, gap - 0.1)
            
            # 只有当确实能延长时才操作 (extend_by可能为负，如果gap<0.1)
            if extend_by > 0:
                curr_seg["end"] += extend_by
                
    # 特殊处理最后一句：总是延长 0.5s，防止结束太快
    segments[-1]["end"] += 0.5
    
    return segments
```

## 3. 落地建议
1.  **渐进式升级**：先在 `txt2srt` 中引入上述 `optimize_subtitle_duration` 函数，这是一个无风险的纯后处理逻辑，立竿见影提升效果。
2.  **引擎替换**：安装 `faster-whisper` 并测试。注意第一次运行时会自动从 HuggingFace 下载转换后的模型（目录结构不同于原版 Whisper），需确保网络通畅。
