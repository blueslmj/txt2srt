# 🚀 GPU 加速设置指南

## 为什么需要 GPU？

使用 **GPU 加速**可以让 Whisper 模型运行速度提升 **10-50倍**！

| 处理方式 | 5分钟音频 | 30分钟音频 |
|---------|----------|-----------|
| CPU | 5-10分钟 | 30-60分钟 |
| GPU | 10-30秒 | 2-5分钟 |

---

## ✅ 检查 GPU 是否可用

运行这个命令检查：

```bash
# 激活虚拟环境
venv\Scripts\activate

# 检查GPU
python -c "import torch; print(f'GPU可用: {torch.cuda.is_available()}'); print(f'GPU名称: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"无\"}'); print(f'CUDA版本: {torch.version.cuda}')"
```

**输出示例**：
```
GPU可用: True
GPU名称: NVIDIA GeForce RTX 3060
CUDA版本: 11.8
```

如果显示 `GPU可用: False`，说明需要安装 GPU 支持。

---

## 🔧 安装 GPU 支持（Windows + NVIDIA 显卡）

### 第1步：检查显卡

**支持的显卡**：NVIDIA GPU（需要支持CUDA）
- ✅ GeForce 系列（GTX 1000+, RTX 系列）
- ✅ Quadro 系列
- ✅ Tesla 系列

**不支持**：
- ❌ AMD GPU（目前PyTorch主要支持NVIDIA CUDA）
- ❌ Intel 集成显卡

### 第2步：安装 NVIDIA 驱动

1. 访问 NVIDIA 官网：https://www.nvidia.com/Download/index.aspx
2. 下载并安装最新驱动
3. 重启电脑

### 第3步：检查 CUDA 版本

```bash
# 运行命令
nvidia-smi
```

查看 "CUDA Version" 一栏，记住版本号（如 12.1, 11.8 等）

### 第4步：安装 PyTorch GPU 版本

#### 方式A：自动安装（推荐）

访问 PyTorch 官网选择器：https://pytorch.org/get-started/locally/

选择：
- PyTorch Build: Stable
- Your OS: Windows
- Package: Pip
- Language: Python
- Compute Platform: CUDA 11.8 或 12.1（根据你的版本）

会得到安装命令，例如：

```bash
# 激活虚拟环境
venv\Scripts\activate

# 卸载CPU版本
pip uninstall torch torchvision torchaudio

# 安装GPU版本（CUDA 11.8）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 或安装GPU版本（CUDA 12.1）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### 方式B：手动安装

```bash
# 激活虚拟环境
venv\Scripts\activate

# 卸载现有版本
pip uninstall torch torchvision torchaudio -y

# 安装 CUDA 11.8 版本
pip install torch==2.1.0+cu118 torchvision==0.16.0+cu118 torchaudio==2.1.0+cu118 --index-url https://download.pytorch.org/whl/cu118

# 或安装 CUDA 12.1 版本
pip install torch==2.1.0+cu121 torchvision==0.16.0+cu121 torchaudio==2.1.0+cu121 --index-url https://download.pytorch.org/whl/cu121
```

### 第5步：验证安装

```bash
# 测试GPU
python -c "import torch; print(f'✅ GPU可用!' if torch.cuda.is_available() else '❌ GPU不可用'); print(f'GPU: {torch.cuda.get_device_name(0)}' if torch.cuda.is_available() else 'CPU模式')"
```

---

## 🎯 使用 GPU 加速

安装完成后，程序会**自动使用GPU**！

启动UI时会看到：
```
✅ 使用设备: GPU
GPU名称: NVIDIA GeForce RTX 3060
```

如果看到：
```
⚠️ 警告: GPU不可用，使用CPU处理（速度较慢）
```

说明GPU配置有问题，请重新检查上述步骤。

---

## 🐛 常见问题

### Q1: 安装后仍然提示GPU不可用？

**A**: 检查以下几点：

1. **验证CUDA安装**
   ```bash
   nvidia-smi
   ```
   应该能看到GPU信息

2. **检查PyTorch版本**
   ```bash
   pip show torch
   ```
   版本名应该包含 `+cu118` 或 `+cu121`，如果只有版本号说明是CPU版本

3. **重新安装PyTorch GPU版本**
   ```bash
   pip uninstall torch torchvision torchaudio -y
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

### Q2: 提示 "CUDA out of memory"？

**A**: GPU显存不足，尝试：

1. 使用更小的模型（tiny, base）
2. 关闭其他占用GPU的程序
3. 降低音频质量或分段处理

### Q3: 我有AMD显卡怎么办？

**A**: 目前AMD显卡支持有限：

1. **Windows**: 暂无简单方案，建议使用CPU
2. **Linux**: 可以尝试 ROCm 版本的 PyTorch（复杂）

### Q4: 没有NVIDIA显卡，有其他加速方式吗？

**A**: 可以尝试：

1. **使用更小的模型**（tiny比base快3-4倍）
2. **减少音频采样率**
3. **使用在线API服务**（OpenAI Whisper API）

### Q5: 安装GPU版本会占用很多空间吗？

**A**: 是的，GPU版本比CPU版本大约多占用 1-2GB 空间。

---

## 📊 性能对比

实际测试结果（10分钟音频，使用 base 模型）：

| 设备 | 处理时间 | 加速比 |
|------|---------|--------|
| Intel i7-12700 (CPU) | 8分30秒 | 1x |
| NVIDIA RTX 3060 (GPU) | 25秒 | 20x |
| NVIDIA RTX 4090 (GPU) | 12秒 | 42x |

---

## 🎓 推荐配置

### 最低配置（CPU模式）
- CPU: Intel i5 或 AMD Ryzen 5
- 内存: 8GB
- 模型: tiny, base

### 推荐配置（GPU模式）
- GPU: NVIDIA GTX 1060 6GB+
- 内存: 8GB
- 模型: base, small

### 高性能配置（GPU模式）
- GPU: NVIDIA RTX 3060+ (12GB+)
- 内存: 16GB+
- 模型: medium, large

---

## 📝 总结

**快速步骤**：

1. ✅ 检查是否有 NVIDIA 显卡
2. ✅ 安装最新 NVIDIA 驱动
3. ✅ 运行 `nvidia-smi` 查看 CUDA 版本
4. ✅ 安装对应版本的 PyTorch GPU
5. ✅ 验证 GPU 可用
6. ✅ 重新运行程序，享受加速！

**如果配置成功**，处理速度会提升 **10-50倍**！🚀

