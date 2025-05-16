** LLM Model Endpoint should be openai-compatible api and model name should be started as"openai/". Example: openai/kimi-latest or openai/deepseek/deepseek-chat:free. **

---

# 🧩 Drova Toolkit: Font Replacement + Text Translation

This project provides two utility scripts to help you:

- 🧷 Replace fonts in Unity game asset files (`replace_fonts.py`)  
- 🌐 Automatically translate `.loc` text resource files (`translate_loc.py`)

Managed by [uv](https://github.com/astral-sh/uv) for dependency management and environment setup. Simple installation and fast execution, suitable for **users without programming experience**!

---

## 📦 Step-by-Step Guide

### ✅ Step 1: Install `uv`

#### Windows
Use irm to download the script and execute it with iex:

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Changing the execution policy allows running a script from the internet.

#### macOs and Linux:
Use curl to download the script and execute it with sh:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
If your system doesn't have curl, you can use wget:

```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```
Request a specific version by including it in the URL:

```bash
curl -LsSf https://astral.sh/uv/0.7.4/install.sh | sh
```
---

### ✅ Step 2: Install Dependencies and Python

Execute in project directory:

```bash
uv sync
```

### ✅ Step 3: Translate
```bash
uv run translate_loc.py \
  --api-key "sk-xxx" \
  --api-base "https://openrouter.ai/api/v1" \
  --model openai/openai/gpt-4.1-mini \
    "D:\steam\steamapps\common\Drova - Forsaken Kin\Drova_Data\StreamingAssets\Localization\en"
```
### Step 4: Inject Your language's font file
```bash
uv run python replace_fonts.py \
  --input "D:\steam\steamapps\common\Drova - Forsaken Kin\Drova_Data\resources.assets" \
  --output outputAssets/resources.assets \
  --font ./myfont.ttf
```

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
  --api-key "sk-xxx" \
  --model openai/gpt-3.5-turbo \
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