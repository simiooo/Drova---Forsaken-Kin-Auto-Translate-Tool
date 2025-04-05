

# 🧩 Drova 工具集：字体替换 + 文本翻译

本项目提供两个实用脚本，帮助你：

- 🧷 替换 Unity 游戏资源文件中的字体（`replace_fonts.py`）  
- 🌐 自动翻译 `.loc` 文本资源文件（`translate_loc.py`）

使用 [uv](https://github.com/astral-sh/uv) 管理依赖和运行环境，安装简单、运行迅速，适合 **无编程基础用户** 使用！

---

## 📦 一步步开始

### ✅ 第一步：安装 Python（如果尚未安装）

从官网下载安装：[https://www.python.org/downloads/](https://www.python.org/downloads/)

📌 **务必勾选** ✅ Add Python to PATH

---

### ✅ 第二步：安装 `uv`

```bash
pip install uv
```

---

### ✅ 第三步：安装依赖

在项目目录下执行：

```bash
uv pip install -r pyproject.toml
```

---

## 📁 项目结构说明

```
drova-tools/
├── pyproject.toml          # 项目依赖定义
├── uv.lock                 # 锁定的依赖版本（自动生成）
├── README.md               # 项目说明文档
├── replace_fonts.py        # Unity 字体替换脚本
├── translate_loc.py        # Drova 文本翻译脚本
├── srcAssets/              # 原始 Unity .assets 文件目录
├── outputAssets/           # 处理后输出目录
```

---

## 🖋️ 字体替换工具（replace_fonts.py）

### 🎯 功能

将 Unity 游戏资源中的指定字体（如 LiberationSans）替换为你喜欢的字体（如 思源黑体）。

### ▶️ 使用示例

```bash
uv run python replace_fonts.py \
  --input srcAssets/sharedassets0.assets \
  --output outputAssets/modified.assets \
  --font ./myfont.ttf
```

### 可选参数说明

| 参数         | 说明                                   |
|--------------|----------------------------------------|
| `--input`    | 要处理的 Unity `.assets` 文件路径     |
| `--output`   | 替换后的输出文件路径                  |
| `--font`     | 你要替换的新字体 `.ttf` 或 `.otf` 文件 |
| `--name`     | （可选）要替换的字体名，默认：LiberationSans |

---

## 🌍 文本翻译工具（translate_loc.py）

### 🎯 功能

自动翻译 Drova 的 `.loc` 文件内容（英文 → 中文），保留原格式，支持并发处理。

### 🪧 先配置 `.env` 文件（推荐）

在项目根目录下新建 `.env` 文件，内容如下：

```env
API_KEY=你的API密钥
MODEL=openai/gpt-3.5-turbo
API_BASE=https://api.openai.com/v1
TARGET_PATH=./outputAssets
CHUNK_SIZE=2000
CONCURRENCY=10
LOG_FILE=execution.log
SOURCE_LOCALE=en_US
TARGET_LOCALE=zh_CN
```

---

### ▶️ 使用示例

```bash
uv run translate_loc.py srcAssets
```

也可以用命令行参数覆盖 `.env`：

```bash
uv run translate_loc.py srcAssets \
  --target-path outputAssets \
  --api-key sk-xxx \
  --model openai/gpt-3.5-turbo \
  --chunk-size 2000 \
  --concurrency 10
```

### 参数说明

| 参数             | 说明                                         |
|------------------|----------------------------------------------|
| `source_dir`     | 必填，要翻译的 `.loc` 文件夹路径            |
| `--target-path`  | 可选，翻译结果保存目录，默认：`./translated`|
| `--api-key`      | 可选，语言模型的 API 密钥                    |
| `--model`        | 可选，模型名称（支持 openai/kimi 等）       |
| `--api-base`     | 可选，API 地址（如 Moonshot 或 OpenAI）    |
| `--source-locale`| 可选，待翻译语言locale,默认:en_US            |
| `--target-locale`| 可选，结果翻译语言locale,默认:zh_CN         |
| `--chunk-size`   | 可选，单段最大字符数，默认 2000              |
| `--concurrency`  | 可选，同时翻译的任务数量，默认 10           |
| `--log-file`     | 可选，日志输出路径，默认 `execution.log`    |

---

## 💡 常见问题

### Q: 如何知道我要替换的字体名？
A: 通常默认字体是 `LiberationSans`，你可以用脚本自动查找并输出。

### Q: `.loc` 是什么格式？
A: 游戏中的翻译资源文本，例如：
```
Quest_Intro { You have entered the forest }
```

### Q: 翻译结果错乱？
A: 脚本已尽量保留原结构。如仍有错乱，请检查模型响应是否偏离系统提示。

---

## 🧠 建议拓展

- ✅ 使用 GUI 界面封装功能
- 🧪 增加 `.loc` 格式检查与回退机制
- 📁 增加批量处理压缩包支持

---

## 🧊 鸣谢

- [LiteLLM](https://github.com/BerriAI/litellm) - 通用大模型请求工具  
- [UnityPy](https://github.com/K0lb3/UnityPy) - Unity 资源解析库  
