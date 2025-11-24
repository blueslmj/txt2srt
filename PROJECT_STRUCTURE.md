# 📁 项目结构说明

## 完整文件列表

```
txt2srt/
├── 🚀 核心程序文件
│   ├── txt2srt.py              # 命令行主程序
│   ├── txt2srt_ui.py           # Gradio Web界面
│   └── txt2srt_tkinter_ui.py   # Tkinter桌面界面
│
├── 🎬 快捷启动脚本
│   ├── setup.bat               # 一键安装环境
│   ├── start_ui.bat            # 启动Web界面
│   ├── start_tkinter_ui.bat    # 启动桌面界面
│   └── run_example.bat         # 运行命令行示例
│
├── 📚 文档文件
│   ├── START_HERE.txt          # 👈 从这里开始！
│   ├── QUICKSTART.md           # 快速开始指南
│   ├── UI_GUIDE.md             # UI界面详细说明
│   ├── UI_SCREENSHOTS.md       # 界面预览和对比
│   ├── SUPPORTED_FORMATS.md    # 支持的音频格式详解
│   ├── README.md               # 完整项目文档
│   └── PROJECT_STRUCTURE.md    # 本文件
│
├── 💻 示例和配置
│   ├── example.py              # Python API使用示例
│   ├── sample_text.txt         # 示例文本文件
│   ├── requirements.txt        # Python依赖包列表
│   └── .gitignore              # Git忽略文件配置
│
└── 📦 运行时文件（自动生成）
    └── venv/                   # Python虚拟环境（运行setup.bat后创建）
```

---

## 📄 文件详细说明

### 🚀 核心程序文件

#### `txt2srt.py`
- **用途**：命令行版本的主程序
- **功能**：
  - 接收音频和文本文件
  - 使用Whisper进行语音识别
  - 生成SRT字幕文件
- **适合**：批量处理、脚本自动化
- **使用**：
  ```bash
  venv\Scripts\python txt2srt.py audio.mp3 text.txt
  ```

#### `txt2srt_ui.py`
- **用途**：Gradio Web界面
- **特点**：
  - 现代化美观界面
  - 支持拖拽上传
  - 实时预览
  - 在浏览器中运行
- **适合**：日常使用、演示展示
- **启动**：
  ```bash
  start_ui.bat
  ```

#### `txt2srt_tkinter_ui.py`
- **用途**：Tkinter桌面界面
- **特点**：
  - 传统桌面应用
  - 无需浏览器
  - 详细日志输出
  - 无额外依赖
- **适合**：快速简单使用
- **启动**：
  ```bash
  start_tkinter_ui.bat
  ```

---

### 🎬 快捷启动脚本

#### `setup.bat`
- **用途**：自动化安装脚本
- **功能**：
  1. 创建Python虚拟环境
  2. 安装所有依赖包
  3. 配置运行环境
- **使用时机**：第一次使用项目时
- **运行**：双击文件

#### `start_ui.bat`
- **用途**：启动Gradio Web界面
- **功能**：
  - 激活虚拟环境
  - 启动Web服务器
  - 自动打开浏览器
- **运行**：双击文件

#### `start_tkinter_ui.bat`
- **用途**：启动Tkinter桌面界面
- **功能**：
  - 激活虚拟环境
  - 启动桌面应用
- **运行**：双击文件

#### `run_example.bat`
- **用途**：命令行使用帮助
- **功能**：显示命令行使用示例
- **运行**：双击文件查看示例

---

### 📚 文档文件

#### `START_HERE.txt`
- **用途**：新手入门文档
- **内容**：3步快速开始指南
- **推荐**：第一次使用必读！

#### `QUICKSTART.md`
- **用途**：详细快速开始指南
- **内容**：
  - 安装步骤
  - 使用示例
  - 处理时间参考
  - 常见问题解答
- **推荐**：了解完整使用流程

#### `UI_GUIDE.md`
- **用途**：UI界面使用说明
- **内容**：
  - 两种UI界面对比
  - 详细使用步骤
  - 界面截图说明
  - 故障排除
- **推荐**：使用UI界面前阅读

#### `README.md`
- **用途**：完整项目文档
- **内容**：
  - 项目介绍
  - 所有功能说明
  - 技术实现细节
  - API参数说明
- **推荐**：深入了解项目

#### `PROJECT_STRUCTURE.md`
- **用途**：项目结构说明（本文件）
- **内容**：所有文件的详细说明

---

### 💻 示例和配置

#### `example.py`
- **用途**：Python API使用示例
- **内容**：
  - 基本使用示例
  - 批量处理示例
  - 高级自定义示例
- **适合**：
  - 在代码中集成本工具
  - 批量处理多个文件
  - 自定义处理流程

#### `sample_text.txt`
- **用途**：示例文本文件
- **内容**：测试用的示例文本
- **使用**：快速测试工具功能

#### `requirements.txt`
- **用途**：Python依赖包清单
- **内容**：
  - openai-whisper（语音识别）
  - gradio（Web界面）
  - torch（深度学习框架）
  - 其他必要依赖
- **使用**：`pip install -r requirements.txt`

#### `.gitignore`
- **用途**：Git版本控制忽略配置
- **内容**：
  - 虚拟环境目录
  - 临时文件
  - 测试音频文件
  - Python缓存

---

### 📦 运行时文件

#### `venv/`
- **用途**：Python虚拟环境目录
- **创建**：运行 `setup.bat` 时自动创建
- **内容**：
  - Python解释器副本
  - 所有已安装的依赖包
  - 激活脚本
- **大小**：约500MB-2GB（取决于依赖）

---

## 🔄 典型工作流程

### 流程1：新手入门
```
1. 阅读 START_HERE.txt
2. 运行 setup.bat
3. 双击 start_ui.bat
4. 开始使用Web界面
```

### 流程2：日常使用
```
1. 准备音频和文本文件
2. 双击 start_ui.bat
3. 上传文件并处理
4. 下载生成的SRT文件
```

### 流程3：批量处理
```
1. 参考 example.py
2. 编写Python脚本
3. 在venv环境中运行
4. 自动化处理多个文件
```

### 流程4：命令行使用
```
1. 激活虚拟环境
2. 运行 txt2srt.py
3. 传递命令行参数
4. 获得输出文件
```

---

## 💡 文件选择建议

### 我该从哪里开始？

| 你的情况 | 推荐阅读 | 推荐使用 |
|---------|---------|---------|
| 完全新手 | `START_HERE.txt` | `start_ui.bat` |
| 想了解详情 | `QUICKSTART.md` | `start_ui.bat` |
| 需要批量处理 | `example.py` | 命令行 + Python API |
| 喜欢桌面应用 | `UI_GUIDE.md` | `start_tkinter_ui.bat` |
| 想深入定制 | `README.md` + `example.py` | Python API |

### 我需要修改哪个文件？

| 需求 | 修改文件 |
|------|---------|
| 改变Web界面外观 | `txt2srt_ui.py` |
| 修改桌面界面 | `txt2srt_tkinter_ui.py` |
| 调整核心算法 | `txt2srt.py` |
| 添加新功能 | 根据需要修改对应文件 |
| 批量处理脚本 | 创建新的.py文件，参考 `example.py` |

---

## 📊 文件依赖关系

```
setup.bat
    └─> 创建 venv/
        └─> 安装 requirements.txt 中的包

start_ui.bat
    └─> 激活 venv/
        └─> 运行 txt2srt_ui.py
            └─> 调用 txt2srt.py 中的函数

start_tkinter_ui.bat
    └─> 激活 venv/
        └─> 运行 txt2srt_tkinter_ui.py
            └─> 调用 txt2srt.py 中的函数

example.py
    └─> 导入 txt2srt.py
        └─> 使用其中的函数
```

---

## 🛡️ 安全说明

### 可以删除的文件
- `sample_text.txt` - 示例文件，可以删除
- `example.py` - 示例代码，不影响主程序
- 所有 `.md` 文档 - 删除后不影响功能

### 不要删除的文件
- `txt2srt.py` - 核心程序
- `txt2srt_ui.py` - Web界面
- `txt2srt_tkinter_ui.py` - 桌面界面
- `requirements.txt` - 依赖列表
- `venv/` - 虚拟环境
- 所有 `.bat` 脚本

### 可以修改的文件
- 所有文档（`.md`, `.txt`）
- `example.py` - 用于学习和参考
- `.gitignore` - 根据需要调整

---

## 🎓 学习路径

### Level 1 - 新手
1. 阅读 `START_HERE.txt`
2. 运行 `setup.bat`
3. 使用 `start_ui.bat`
4. 处理第一个文件

### Level 2 - 熟练
1. 阅读 `QUICKSTART.md`
2. 了解不同模型的区别
3. 尝试命令行版本
4. 调整参数优化结果

### Level 3 - 高级
1. 阅读 `README.md`
2. 研究 `example.py`
3. 编写批量处理脚本
4. 自定义后处理逻辑

### Level 4 - 专家
1. 研究源代码 `txt2srt.py`
2. 修改和扩展功能
3. 集成到自己的项目
4. 优化性能和准确度

---

## 📞 获取帮助

- **快速问题**：查看 `QUICKSTART.md` 的"常见问题"部分
- **UI使用**：参考 `UI_GUIDE.md`
- **代码问题**：研究 `example.py` 和 `txt2srt.py`
- **完整文档**：阅读 `README.md`

---

**更新日期**：2025年11月
**项目版本**：1.0.0

