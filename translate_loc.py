import os
import sys
import re
import asyncio
import logging
import argparse
from dotenv import load_dotenv
from litellm import acompletion
from litellm.utils import trim_messages

# ------------------- 加载 .env 配置 -------------------
load_dotenv()

# ------------------- 配置类 -------------------
class Config:
    def __init__(self, args):
        self.api_key = args.api_key or os.getenv("API_KEY", "")
        self.model = args.model or os.getenv("MODEL", "openai/kimi-latest")
        self.api_base = args.api_base or os.getenv("API_BASE", "https://api.moonshot.cn/v1")
        self.target_path = args.target_path or os.getenv("TARGET_PATH", "./translated")
        self.log_file = args.log_file or os.getenv("LOG_FILE", "execution.log")
        self.chunk_size = args.chunk_size or int(os.getenv("CHUNK_SIZE", 2000))
        self.concurrency = args.concurrency or int(os.getenv("CONCURRENCY", 10))
        self.source_locale = args.source_locale or (os.getenv("SOURCE_LOCALE", "en_US"))
        self.target_locale = args.target_locale or (os.getenv("TARGET_LOCALE", "zh_CN"))
        self.system_prompt = system_prompt_create(self.source_locale, self.target_locale)
        self.loc_pattern = re.compile(r'.*\.loc$')
        self.localization_target_pattern = re.compile(r'(.+)_.+\.loc$')
        

# ------------------- 默认系统提示词 -------------------
def system_prompt_create(source_locale, target_locale):
    return f"""
    你是drova这款游戏的翻译编译器，请帮我将给定的的{source_locale}输入翻译为{target_locale}输出。人名与地名不需要被翻译。请严格作为编译器执行，返回跟原编码格式相同的格式，不要输出任何无关内容。
    不要尝试修复、删除任何看起来错误的语法，如： "Plh_35 {{"、"Plh_35 {{ The chains are firmly aff"、"}}" 
    只需要做好自己翻译的工作即可。 
    *** 示例输入:
    Achievement_ImmersiveMod_name {{ Iron }}
    ***示例输出：
    Achievement_ImmersiveMod_name {{ 铁 }}。
    请结合这款游戏的背景进行翻译，这款游戏的背景如下：
    "Drova - Forsaken Kin" 是一款受经典黑暗风格和凯尔特神话神秘魅力启发的像素风格动作角色扮演游戏。进入一个精心制作的开放世界，你的选择和行动将影响环境。一个社会发现了已经灭亡帝国的力量：捕捉并支配掌管自然的灵魂。然而，余下的灵魂因为愤怒而分裂。你将站在哪一边？入两个阵营之一，每个阵营都有其自己的价值观并追求各自的目标。你的选择将对整个游戏产生影响，并改变整个故事。所有的决定都伴随着代价。遇见导师并学习各种技能，但也要小心敌人和背叛。危险的景观中开辟自己的道路，完成任务、进行交易、收集和制作装备。你将从无到有，从无名之辈成长起来。研究周围的环境，利用周围的线索揭示谜团并变得更强。只有你的战斗技能才能将你与必然的死亡隔开。索自然，封印掌控它的灵魂力量。学会如何将它们为你所用，但也要准备好迎接这些灵魂的愤怒，它们的愤怒将在你周围的世界中显现。
    """.strip()

# ------------------- 日志初始化 -------------------
def init_logging(log_file):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

# ------------------- 翻译任务 -------------------
def get_targetpath(src_file, src_root, dst_root):
    rel_path = os.path.relpath(src_file, src_root)
    return os.path.join(dst_root, rel_path)

def write_file_preserve_structure(data, src_file, src_root, dst_root,config):
    dst_file = get_targetpath(src_file, src_root, dst_root)
    dst_file = re.sub(config.localization_target_pattern,f"\\1_{config.target_locale}.loc",dst_file)
    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    with open(dst_file, "w", encoding="utf-8") as f:
        f.write(data)

def split_near_brace(text, step=300):
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end_candidate = min(start + step, n)
        if end_candidate == n:
            chunks.append(text[start:])
            break
        split_pos = text.rfind('}', start, end_candidate + 1)
        if split_pos == -1:
            split_pos = end_candidate
        chunks.append(text[start:split_pos + 1])
        start = split_pos + 1
    return chunks

async def task_progress(data, config, semaphore):
    async with semaphore:
        logging.info(f"开始处理片段：{data[:50]}...")
        response = await acompletion(
            model=config.model,
            api_base=config.api_base,
            api_key=config.api_key,
            messages=trim_messages([
                {"content": config.system_prompt, "role": "system"},
                {"content": data, "role": "user"}
            ], max_tokens=8096)
        )
        res = response["choices"][0]["message"]["content"]
        logging.info(f"处理完成：{res[:50]}...")
        return res

async def file_progress(file, source_dir, config, semaphore, file_cnt):
    if file.is_dir() and os.access(file.path, os.R_OK):
        await traval(file.path, source_dir, config, semaphore, file_cnt)
    else:
        if config.loc_pattern.match(file.name):
            with open(file.path, encoding="utf-8") as f:
                file_cnt[0] += 1
                logging.info(f"----- 开始处理第{file_cnt[0]}个文件 {file.name} -----")
                dst_file = get_targetpath(file.path, source_dir, config.target_path)
                if os.path.exists(dst_file):
                    logging.info(f"文件 {file.name} 已存在，跳过")
                    return
                data = f.read()
                chunks = split_near_brace(data, config.chunk_size)
                tasks = [task_progress(c, config, semaphore) for c in chunks if c.strip()]
                translated_chunks = await asyncio.gather(*tasks)
                translated_text = "\n\n".join(translated_chunks)
                write_file_preserve_structure(translated_text, file.path, source_dir, config.target_path,config)
                logging.info(f"----- 结束处理第{file_cnt[0]}个文件 {file.name} -----")

async def traval(dir_path, source_dir, config, semaphore, file_cnt):
    async_tasks = []
    with os.scandir(dir_path) as entries:
        for file in entries:
            async_tasks.append(file_progress(file, source_dir, config, semaphore, file_cnt))
    if async_tasks:
        await asyncio.gather(*async_tasks)

# ------------------- 主函数 -------------------
async def main():
    parser = argparse.ArgumentParser(description="Drova 翻译脚本")
    parser.add_argument("source_dir", help="源文件夹路径")
    parser.add_argument("--target-path", help="输出目录")
    parser.add_argument("--api-key", help="API 密钥")
    parser.add_argument("--model", help="模型名称")
    parser.add_argument("--api-base", help="API 基础地址")
    parser.add_argument("--log-file", help="日志文件路径")
    parser.add_argument("--chunk-size", type=int, help="单段最大字符数")
    parser.add_argument("--concurrency", type=int, help="最大并发数")
    parser.add_argument("--source-locale", help="待翻译语言")
    parser.add_argument("--target-locale", help="翻译结果语言")

    args = parser.parse_args()
    config = Config(args)
    init_logging(config.log_file)

    if not os.path.isdir(args.source_dir):
        print("错误：source_dir 必须是一个有效的目录路径")
        sys.exit(1)

    semaphore = asyncio.Semaphore(config.concurrency)
    file_cnt = [0]

    await traval(args.source_dir, args.source_dir, config, semaphore, file_cnt)

if __name__ == "__main__":
    asyncio.run(main())
