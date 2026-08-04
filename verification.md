# Verification

验证日期：2026-08-04

## 已通过

- `python -m unittest discover -s tests -v`
  - 12 个测试全部通过。
  - 覆盖文本切分、Unicode 归一化、时间轴映射、差异告警、重叠修正、SRT 写入、项目内下载路径、本地模型定位、GB18030 文本读取和主对齐管线。
- `python -m py_compile project_paths.py txt2srt.py txt2srt_ui.py txt2srt_tkinter_ui.py txt2srt_whisperx.py scripts/validate_runtime.py tests/test_txt2srt.py`
  - 核心、Web UI、Tkinter UI 和测试文件均通过语法编译。
- `python txt2srt.py missing.wav "测试文稿" --device cpu`
  - 返回退出码 `1`，并输出明确的“音频文件不存在”错误；验证 CLI 错误路径不会进入模型加载。
- Tkinter 控件冒烟
  - 成功创建窗口和全部控件；默认值为 `small / auto / 30`。
- Gradio 浏览器冒烟（Playwright）
  - 在 1440px 桌面视口与 390px 移动视口完成实际渲染检查。
  - 输入、文稿、模型、语言、设备、字数限制、结果和下载控件均可访问。
  - 空输入点击“开始生成字幕”后，结果区正确显示操作指引。
- 硬件感知安装器
  - `install.ps1` 通过 PowerShell 7 与 Windows PowerShell 5 语法解析；脚本保持 UTF-8 无 BOM，并使用 ASCII 运行时文本兼容旧版 PowerShell。
  - `auto / cpu / nvidia-legacy` 三种选择路径通过 `-DryRun`，未修改虚拟环境。
  - 在 RTX 5070 Ti 上完整执行 `auto -NonInteractive`：识别计算能力 12.0，选择 cu130，复用匹配的 Torch，安装通用依赖并通过运行时检查。
  - 安装记录成功写入 `venv/hardware-profile.json`。
- 项目本地存储
  - 安装器和全部运行入口将 Hugging Face、Whisper、Torch、Gradio、Numba、CUDA 与系统临时路径固定到项目 `models/.runtime`。
  - `venv/pip.ini` 与安装命令均启用 `no-cache-dir`，pip 不再保留用户级下载缓存。
  - `tempfile.gettempdir()` 实测为 `G:\code\cursor\txt2srt\.runtime\temp`，全部受控路径均通过项目根目录范围断言。
  - 既有 Faster-Whisper `tiny` 与 `small` 模型已复制到项目 `models/faster-whisper`，设置 `HF_HUB_OFFLINE=1` 后均能成功加载；`small` 的四个文件已逐一通过 SHA-256 校验。
  - 完整重新执行 `install.ps1 -Profile auto -NonInteractive`，依赖、CUDA FP16、CTranslate2 与核心导入验证通过。

## 未覆盖与风险

- 已于 2026-08-04 重建 `venv`：Python 3.12.10、PyTorch/Torchaudio 2.11.0 + CUDA 13.0，其余依赖来自 `requirements.txt`；`pip check` 无依赖冲突。
- RTX 5070 Ti CUDA 可用，计算能力 12.0；FP16 矩阵计算通过，CTranslate2 能识别 CUDA 设备并支持 FP16。
- Faster-Whisper `tiny` 与 `small` 模型当前位于项目 `models`；此前使用 `tiny` 对 `test.flac` 前 10 秒执行真实 GPU 转写，成功生成 4 个识别段落。
- 旧的用户级 Hugging Face 共享缓存没有自动删除，避免影响其他项目；本项目后续不会再读取或写入该位置。
- 尚未用默认 `small` 模型跑完整 `test.flac + test.txt` 长音频对齐。正式使用时仍建议抽查长音频时间轴和显存占用。
- CPU 与 CUDA 12.6 profile 已验证选择逻辑和官方包索引，但没有在无 NVIDIA/旧 NVIDIA 实机上执行完整安装；这些机器仍需发布前补充硬件回归。
