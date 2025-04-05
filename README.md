# 🧩 Drova 工具集：字体替换 + 文本翻译

本项目提供两个实用工具，用于对 **Drova - Forsaken Kin** 游戏资源文件进行修改和翻译：

- 🎮 `replace_font.py`：替换 Unity 游戏中的字体文件  
- 🌍 `translate.py`：自动翻译游戏 `.loc` 文本资源文件（英文 → 中文）

支持 `uv` 环境管理，安装快，使用简单，零基础友好！

---

## 📦 使用前准备

### 1️⃣ 安装 Python（如果尚未安装）

- 下载地址：[https://www.python.org/downloads/](https://www.python.org/downloads/)
- **安装时务必勾选**：✅ Add Python to PATH

---

### 2️⃣ 安装 uv（推荐）

`uv` 是一个比 pip 更快、更简单的 Python 包管理工具。

```bash
pip install uv
```

或者使用 pipx（推荐方式）：

```bash
pip install pipx
pipx install uv
```

---

### 3️⃣ 克隆项目并安装依赖

```bash
git clone https://github.com/yourname/drova-tools.git
cd drova-tools
uv pip install -r requirements.txt
```

📄 `requirements.txt` 内容如下：

```txt
UnityPy
litellm
python-dotenv
```

---

## 🛠️ 脚本 1：Unity 字体替换工具（`replace_font.py`）

### ✅ 功能

将 Unity 游戏资源文件中的字体（如 LiberationSans）替换成你喜欢的字体（如 思源黑体）。

### ▶️ 使用方法

```bash
uv pip install UnityPy  # 如果只需要用这个脚本可单独装
uv python replace_font.py --input 输入.assets路径 --output 输出.assets路径 --font 新字体.ttf路径
```

### 🧪 示例

```bash
uv python replace_font.py -i sharedassets0.assets -o modified.assets -f myfont.ttf
```

参数说明：

| 参数       | 说明                             |
|------------|----------------------------------|
| `--input`  | 原始 `.assets` 文件路径          |
| `--output` | 输出修改后的 `.assets` 文件路径  |
| `--font`   | 要替换的新字体（`.ttf` 或 `.otf`）|
| `--name`   | 可选，要替换的字体名（默认：LiberationSans）|

---

## 🌍 脚本 2：Drova 文本翻译工具（`translate.py`）

### ✅ 功能

- 自动遍历 `.loc` 文件，使用大语言模型进行翻译
- 支持 OpenAI / Moonshot / Kimi 等模型
- 并发处理、智能切块、保留格式、人名地名保护

### ▶️ 快速开始

#### 第一步：创建 `.env` 文件（推荐）

在项目根目录创建 `.env` 文件，内容如下：

```env
API_KEY=你的API密钥
MODEL=openai/gpt-3.5-turbo
API_BASE=https://api.openai.com/v1
TARGET_PATH=./translated
CHUNK_SIZE=2000
CONCURRENCY=10
LOG_FILE=execution.log
```

#### 第二步：运行翻译脚本

```bash
uv python translate.py ./loc原始文件夹
```

也可以通过命令行传参（覆盖 `.env`）：

```bash
uv python translate.py ./loc原始文件夹 --api-key sk-xxx --model openai/gpt-3.5-turbo --target-path ./output
```

参数说明：

| 参数             | 说明                                           |
|------------------|------------------------------------------------|
| `source_dir`     | 必填，源 `.loc` 文件所在的文件夹              |
| `--target-path`  | 可选，翻译后文件输出路径（默认 `./translated`）|
| `--api-key`      | 可选，API 密钥（也可通过 `.env` 设置）        |
| `--model`        | 可选，模型名称（默认 `openai/kimi-latest`）   |
| `--api-base`     | 可选，API 地址（默认 `https://api.moonshot.cn/v1`） |
| `--chunk-size`   | 可选，每段最大字符数（默认 2000）             |
| `--concurrency`  | 可选，同时翻译任务数（默认 10）               |
| `--log-file`     | 可选，日志记录文件路径                         |

---

## 📁 项目结构说明

```
drova-tools/
├── replace_font.py       # Unity 字体替换工具
├── translate.py          # Drova 文本翻译工具
├── requirements.txt      # 所需依赖列表
├── .env                  # 环境变量配置（可选）
├── translated/           # 翻译结果保存目录（可自动创建）
```

---

## 🧠 常见问题

### Q: `.loc` 是什么格式？
A: 是 Drova 游戏使用的本地化资源文本格式，形如：
```
Achievement_Name { The Brave One }
```

### Q: `.env` 是必须的吗？
A: 非必需，所有配置都可以通过命令行参数设置。

### Q: 字体替换不生效怎么办？
A: 请确认目标字体名称正确（如 `LiberationSans`），字体文件是否能被正常打开。

### Q: 翻译中断怎么办？
A: 支持断点续传，已处理的文件不会再次处理。

---

## 🧊 进阶建议

- 💡 可以将两个脚本打包为 `.exe` 供非开发用户使用（可选）
- 🖼️ 可加入图形界面（如 tkinter、textual 等）

---

## ❤️ 鸣谢

- [LiteLLM](https://github.com/BerriAI/litellm) - 统一语言模型调用接口  
- [UnityPy](https://github.com/K0lb3/UnityPy) - Unity 资源读取神器  
