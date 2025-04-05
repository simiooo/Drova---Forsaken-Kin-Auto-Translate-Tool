** LLM Model Endpoint should be openai-compatible api and model name should be started as"openai/". Example: openai/kimi-latest or openai/deepseek/deepseek-chat:free. **

---

# 🧩 Drova Toolkit: Font Replacement + Text Translation

This project provides two utility scripts to help you:

- 🧷 Replace fonts in Unity game asset files (`replace_fonts.py`)  
- 🌐 Automatically translate `.loc` text resource files (`translate_loc.py`)

Managed by [uv](https://github.com/astral-sh/uv) for dependency management and environment setup. Simple installation and fast execution, suitable for **users without programming experience**!

---

## 📦 Step-by-Step Guide

### ✅ Step 1: Install Python (if not installed)

Download from official website: [https://www.python.org/downloads/](https://www.python.org/downloads/)

📌 **Mandatory**: ✅ Check "Add Python to PATH" during installation

---

### ✅ Step 2: Install `uv`

```bash
pip install uv
```

---

### ✅ Step 3: Install Dependencies

Execute in project directory:

```bash
uv pip install -r pyproject.toml
```

---

## 📁 Project Structure

```
drova-tools/
├── pyproject.toml          # Project dependencies
├── uv.lock                 # Locked dependency versions (auto-generated)
├── README.md               # Documentation
├── replace_fonts.py        # Unity font replacement script
├── translate_loc.py        # Drova text translation script
├── srcAssets/              # Original Unity .assets directory
├── outputAssets/           # Processed output directory
```

---

## 🖋️ Font Replacement Tool (replace_fonts.py)

### 🎯 Features

Replace specified fonts (e.g., LiberationSans) in Unity game assets with your preferred fonts (e.g., Source Han Sans).

### ▶️ Usage Example

```bash
uv run python replace_fonts.py \
  --input srcAssets/sharedassets0.assets \
  --output outputAssets/modified.assets \
  --font ./myfont.ttf
```

### Optional Parameters

| Parameter      | Description                                   |
|----------------|-----------------------------------------------|
| `--input`      | Path to Unity `.assets` file to process      |
| `--output`     | Output path for modified file                |
| `--font`       | New font file (`.ttf` or `.otf`)             |
| `--name`       | (Optional) Font name to replace, default: LiberationSans |

---

## 🌍 Text Translation Tool (translate_loc.py)

### 🎯 Features

Automatically translate Drova's `.loc` files (EN → CN) while preserving original formatting. Supports concurrent processing.

### 🪧 Configure `.env` File (Recommended)

Create `.env` file in project root with:

```env
API_KEY=your_api_key
MODEL=openai/kimi-latest
API_BASE=https://api.moonshot.cn/v1
TARGET_PATH=./outputAssets
CHUNK_SIZE=2000
CONCURRENCY=10
LOG_FILE=execution.log
SOURCE_LOCALE=en_US
TARGET_LOCALE=zh_CN
```

---

### ▶️ Usage Example

```bash
uv run translate_loc.py srcAssets
```

Override `.env` parameters via command line:

```bash
uv run translate_loc.py \
  --target-path outputAssets \
  --api-key sk-xxx \
  --model openai/gpt-3.5-turbo \
  --chunk-size 2000 \
  --concurrency 10 \
    srcAssets
```

### Parameters

| Parameter            | Description                                         |
|----------------------|-----------------------------------------------------|
| `source_dir`         | Required. Path to `.loc` directory                 |
| `--target-path`      | Output directory, default: `./translated`          |
| `--api-key`          | API key for translation model                      |
| `--model`            | Model name (supports openai/kimi/etc), default: openai/kimi-latest |
| `--api-base`         | API endpoint (e.g., https://api.moonshot.cn/v1)               |
| `--source-locale`    | Source language locale, default: en_US             |
| `--target-locale`    | Target language locale, default: zh_CN            |
| `--chunk-size`       | Max characters per chunk, default: 2000           |
| `--concurrency`      | Concurrent translation tasks, default: 10         |
| `--log-file`         | Log file path, default: `execution.log`           |

---

## 💡 FAQ

### Q: How to identify the font name to replace?
A: Default is usually `LiberationSans`. The script can auto-detect and print found fonts.

### Q: What's the `.loc` format?
A: Game localization resource format example:
```
Quest_Intro { You have entered the forest }
```

### Q: Translation output is garbled?
A: The script preserves original structure. If issues persist, check if model responses deviate from system prompts.

---

## 🧠 Suggested Improvements

- ✅ Create GUI wrapper
- 🧪 Add `.loc` format validation and fallback
- 📁 Add batch processing for zip archives

---

## 🧊 Credits

- [LiteLLM](https://github.com/BerriAI/litellm) - Unified LLM API interface  
- [UnityPy](https://github.com/K0lb3/UnityPy) - Unity asset parsing library

---
If you want to translate to specific language , please add --target-local argument to ./translate_loc.py . Example: uv run translate_loc.py --target-locale ja /home/simooo/Documents/en.
LLM Model Endpoint should be openai-compatible api and model name should be started as"openai/". Example: openai/kimi-latest or openai/deepseek/deepseek-chat:free.