# 🔧 安装问题解决方案

## ❌ 错误：Python 3.14 不支持

### 问题描述
```
RuntimeError: Cannot install on Python version 3.14.0; 
only versions >=3.10,<3.14 are supported.
```

**原因**：PyTorch 等依赖包目前只支持 Python 3.10-3.13，不支持 Python 3.14。

---

## ✅ 解决方案

### 方案1：安装 Python 3.12 或 3.13（推荐）⭐

#### 步骤1：下载 Python 3.12

1. **访问 Python 官网**：
   - https://www.python.org/downloads/
   
2. **下载 Python 3.12.x**：
   - 选择 "Python 3.12.x" 版本
   - 下载 Windows installer (64-bit)

3. **安装时注意**：
   - ✅ 勾选 "Add Python 3.12 to PATH"
   - ✅ 选择 "Install for all users"（可选）
   - ✅ 确保安装 pip 和 IDLE

#### 步骤2：删除旧的虚拟环境

```bash
# 删除现有的 venv 文件夹
rmdir /s /q venv
```

或者在文件管理器中直接删除 `venv` 文件夹。

#### 步骤3：使用 Python 3.12 创建新环境

```bash
# 方式A：使用 py launcher（推荐）
py -3.12 -m venv venv

# 方式B：直接指定 Python 3.12 路径
C:\Python312\python.exe -m venv venv

# 方式C：如果添加了 PATH，直接使用
python -m venv venv
```

#### 步骤4：重新运行安装脚本

```bash
setup.bat
```

---

### 方案2：使用 pyenv-win 管理多个 Python 版本

#### 安装 pyenv-win

```powershell
# 使用 PowerShell 安装
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

#### 安装并使用 Python 3.12

```bash
# 查看可用版本
pyenv install --list

# 安装 Python 3.12
pyenv install 3.12.7

# 在项目中使用 3.12
pyenv local 3.12.7

# 创建虚拟环境
python -m venv venv

# 运行安装
setup.bat
```

---

### 方案3：手动指定 Python 版本创建虚拟环境

#### 1. 找到 Python 3.12/3.13 的安装路径

```bash
# 列出所有 Python 版本
py --list

# 或者检查路径
where python
```

输出示例：
```
-V:3.14          C:\Users\...\Python314\python.exe
-V:3.12          C:\Users\...\Python312\python.exe
-V:3.11          C:\Users\...\Python311\python.exe
```

#### 2. 删除旧环境并创建新环境

```bash
# 删除旧环境
rmdir /s /q venv

# 使用 Python 3.12 创建
py -3.12 -m venv venv

# 激活环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

---

### 方案4：修改 requirements.txt（临时方案，不推荐）

如果必须使用 Python 3.14，可以尝试安装预发布版本：

```bash
# 修改 requirements.txt，在每个包后添加 --pre 标志
# 或者手动安装：

venv\Scripts\pip install --pre torch torchvision torchaudio
venv\Scripts\pip install openai-whisper
venv\Scripts\pip install gradio pydub numpy
```

**⚠️ 警告**：预发布版本可能不稳定，不推荐用于生产环境。

---

## 🎯 推荐配置

### 最佳 Python 版本

| Python 版本 | 兼容性 | 稳定性 | 推荐度 |
|------------|--------|--------|--------|
| 3.14.x | ❌ 不支持 | - | ⛔ 不推荐 |
| 3.13.x | ✅ 支持 | 🟢 稳定 | ⭐⭐⭐ 推荐 |
| 3.12.x | ✅ 支持 | 🟢 稳定 | ⭐⭐⭐ 推荐 |
| 3.11.x | ✅ 支持 | 🟢 稳定 | ⭐⭐ 可用 |
| 3.10.x | ✅ 支持 | 🟢 稳定 | ⭐ 可用 |

**建议**：安装 **Python 3.12** 或 **Python 3.13**

---

## 📋 完整安装流程（Python 3.12）

### 1. 下载并安装 Python 3.12

访问：https://www.python.org/downloads/release/python-3127/

下载：**Windows installer (64-bit)**

安装时勾选：
- ✅ Add Python 3.12 to PATH
- ✅ Install pip
- ✅ Install for all users（可选）

### 2. 验证安装

```bash
# 打开新的命令行窗口
python --version
# 应该显示：Python 3.12.x

# 或使用 py launcher
py -3.12 --version
```

### 3. 清理旧环境

```bash
# 在项目目录中
cd G:\code\cursor\txt2srt

# 删除旧的 venv
rmdir /s /q venv
```

### 4. 创建新环境

```bash
# 方式1：如果 Python 3.12 已添加到 PATH
python -m venv venv

# 方式2：使用 py launcher
py -3.12 -m venv venv
```

### 5. 运行安装脚本

```bash
setup.bat
```

应该会成功安装所有依赖！

---

## 🔍 验证安装

安装完成后，验证环境：

```bash
# 激活虚拟环境
venv\Scripts\activate

# 检查 Python 版本
python --version
# 应该显示 3.12.x 或 3.13.x

# 检查已安装的包
pip list

# 测试导入
python -c "import torch; print(f'PyTorch {torch.__version__}')"
python -c "import whisper; print('Whisper OK')"
python -c "import gradio; print('Gradio OK')"
```

如果都成功，说明环境配置正确！

---

## ❓ 常见问题

### Q: 我有多个 Python 版本，如何选择？

**A**: 使用 `py` launcher：
```bash
# 查看所有版本
py --list

# 使用特定版本
py -3.12 -m venv venv
```

### Q: 删除 venv 后重新安装很慢？

**A**: 第一次安装 PyTorch 会比较慢（约1-2GB），这是正常的。后续重新创建环境时会快很多（使用缓存）。

### Q: 能否同时保留 Python 3.14？

**A**: 可以！安装 Python 3.12 不会影响 3.14。使用 `py -3.12` 或 `py -3.14` 来选择版本。

### Q: PyTorch 何时支持 Python 3.14？

**A**: 通常新 Python 版本发布后的几个月内，主流包会更新支持。建议关注 PyTorch 官方公告。

### Q: 使用 Conda/Anaconda 可以吗？

**A**: 可以！
```bash
# 创建 Python 3.12 环境
conda create -n txt2srt python=3.12
conda activate txt2srt
pip install -r requirements.txt
```

---

## 🆘 仍然遇到问题？

### 检查清单

- [ ] Python 版本是 3.10-3.13 之间
- [ ] 已删除旧的 venv 文件夹
- [ ] 使用正确的 Python 版本创建虚拟环境
- [ ] 网络连接正常（需要下载包）
- [ ] 有足够的磁盘空间（至少 5GB）

### 获取详细错误信息

```bash
# 激活环境
venv\Scripts\activate

# 手动安装查看详细错误
pip install --verbose torch
```

### 清理 pip 缓存

```bash
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

---

## 📝 总结

**最简单的解决方案**：

1. ⬇️ 下载安装 **Python 3.12**
2. 🗑️ 删除 `venv` 文件夹
3. 🔄 重新运行 `setup.bat`

这样就能顺利完成安装了！🎉

