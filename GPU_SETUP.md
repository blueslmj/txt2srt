# GPU 与硬件安装指南

本项目在 Windows 上使用 `setup.bat` 调用 `install.ps1`，根据硬件选择匹配的运行环境。不要把一台电脑生成的 `venv` 复制到另一台电脑。

安装器禁用用户级 pip 缓存，Python 依赖安装在 `venv`；模型固定下载到 `models`；安装及运行临时文件写入 `.runtime`。关闭程序后可直接删除这三个项目内目录进行彻底清理。Python、NVIDIA 驱动和 CUDA Toolkit 是系统组件，不包含在其中。

## 推荐用法

```powershell
setup.bat
```

自动检测只负责选择安装 profile；程序运行时的“自动选择”还会再次调用 `torch.cuda.is_available()`。如果 CUDA 不可用，应用会回退到 CPU。

## Profile 对照

| Profile | 适用硬件 | PyTorch 构建 |
| --- | --- | --- |
| `auto` | 所有用户 | 自动选择下列模式 |
| `nvidia-modern` | RTX 50 / Blackwell，计算能力 12.x | Torch 2.11.0 + cu130 |
| `nvidia-legacy` | Maxwell、Pascal、Volta、Turing、Ampere、Ada 等计算能力 5.x–11.x | Torch 2.11.0 + cu126 |
| `cpu` | AMD/Intel 显卡、无独显、CUDA 排障 | Torch 2.11.0 CPU |

手动指定示例：

```powershell
setup.bat nvidia-modern
setup.bat nvidia-legacy
setup.bat cpu
```

## RTX 50 / Blackwell 特别说明

RTX 50 使用 CUDA 13 PyTorch，但 Faster-Whisper 的 CTranslate2 Windows wheel 仍需要 CUDA 12.x 的 cuBLAS。安装器会检查 `cublas64_12.dll`：

- 已安装 CUDA Toolkit 12.x：直接复用。
- 未安装：交互模式会询问是否通过 winget 安装 CUDA Toolkit 12.8。
- 拒绝安装或非交互模式未授权：自动回退 CPU。

非交互安装并允许安装 Toolkit：

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 `
  -Profile auto -NonInteractive -InstallCudaToolkit
```

## AMD 与 Intel 显卡

当前 Windows 版本的 Faster-Whisper/CTranslate2 预编译 GPU 后端面向 NVIDIA CUDA：

- AMD/Intel Windows 用户使用 CPU profile。
- AMD Linux ROCm、Intel XPU 需要额外后端适配，当前项目没有开箱即用支持。
- CPU 模式推荐 `tiny`、`base` 或 `small` 模型。

## 检测与验证

只查看将要选择的 profile：

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -DryRun -NonInteractive
```

查看安装记录：

```powershell
Get-Content venv\hardware-profile.json
```

手动验证：

```powershell
venv\Scripts\python -m pip check
venv\Scripts\python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

## 常见问题

### 安装了 NVIDIA profile，但 CUDA 不可用

1. 更新 NVIDIA 驱动。
2. 重新运行 `setup.bat`。
3. 仍失败时运行 `setup.bat cpu`，先保证工具可用。

### 显存不足

从 `small/medium` 降到 `base/tiny`，或在界面中把设备改为 CPU。

### 强制重新创建环境

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1 -ForceRecreate
```

相关官方资料：

- [PyTorch 本地安装](https://docs.pytorch.org/get-started/locally/)
- [CTranslate2 安装要求](https://opennmt.net/CTranslate2/installation.html)
- [CTranslate2 硬件支持](https://opennmt.net/CTranslate2/hardware_support.html)
