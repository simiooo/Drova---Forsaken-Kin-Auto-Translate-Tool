import os
import sys
import re
import asyncio
import json
import logging
import time
import argparse
from functools import reduce
from dotenv import load_dotenv
from litellm import acompletion
from litellm.utils import trim_messages

# ------------------- 加载 .env 配置 -------------------
load_dotenv()
cache_translated_key_pair = {}
cache_translated_key_pair_lock = asyncio.Lock()
def get_name_map(keys):
    return {k: cache_translated_key_pair[k] for k in keys if k in cache_translated_key_pair}

class AsyncRateLimiter:
    def __init__(self, rpm_limit):
        self.rpm_limit = rpm_limit
        if not (isinstance(rpm_limit, (int, float)) and rpm_limit > 0):
            logging.info(f"RPM limit is not set to a positive number ({rpm_limit}). Rate limiter disabled.")
            self.enabled = False
            return

        self.enabled = True
        self.requests_in_current_minute = 0
        self.current_minute_start_time = time.monotonic()
        self.lock = asyncio.Lock() # Lock to protect access to shared state
        logging.info(f"Rate limiter enabled with {rpm_limit} RPM.")

    async def acquire(self):
        if not self.enabled:
            return

        while True: # Loop until a permit is acquired
            async with self.lock:
                now = time.monotonic()
                # Check if the current minute window has passed
                if now - self.current_minute_start_time >= 60.0:
                    self.current_minute_start_time = now
                    self.requests_in_current_minute = 0
                    logging.debug(f"RateLimiter: New minute window started at {now:.2f}. Requests reset.")

                if self.requests_in_current_minute < self.rpm_limit:
                    self.requests_in_current_minute += 1
                    logging.debug(f"RateLimiter: Acquired. Requests in current minute: {self.requests_in_current_minute}/{self.rpm_limit}.")
                    break # Exit the while loop as we acquired a permit
                else:
                    # Calculate time until the next minute window starts
                    time_to_wait = 60.0 - (now - self.current_minute_start_time)
                    logging.debug(f"RateLimiter: Rate limit reached ({self.requests_in_current_minute}/{self.rpm_limit}). Waiting for {time_to_wait:.2f} seconds.")
                    # Release the lock before sleeping
            await asyncio.sleep(time_to_wait + 0.1) # Add a small buffer
class Config:
    def __init__(self, args):
        self.api_key = args.api_key or os.getenv("API_KEY", "")
        self.model = args.model or os.getenv("MODEL", "openai/openai/gpt-4.1-mini")
        self.api_base = args.api_base or os.getenv("API_BASE", "https://openrouter.ai/api/v1")
        self.target_path = args.target_path or os.getenv("TARGET_PATH", "./translated")
        self.log_file = args.log_file or os.getenv("LOG_FILE", "execution.log")
        self.chunk_size = args.chunk_size or int(os.getenv("CHUNK_SIZE", 2000))
        self.concurrency = args.concurrency or int(os.getenv("CONCURRENCY", 4))
        self.rpm_limit = args.rpm_limit or int(os.getenv("RPM_LIMIT", 4)) # Default to 60 RPM
        self.source_locale = args.source_locale or (os.getenv("SOURCE_LOCALE", "en_US"))
        self.target_locale = args.target_locale or (os.getenv("TARGET_LOCALE", "zh_CN"))
        self.system_prompt = system_prompt_create(self.source_locale, self.target_locale)
        self.loc_pattern = re.compile(r'.*\.loc$')
        self.localization_target_pattern = re.compile(r'(.+)_.+\.loc$')
        

# ------------------- 默认系统提示词 -------------------
def system_prompt_create(source_locale, target_locale):
    return f"""
    你是drova这款游戏的翻译编译器，请帮我将给定的的{source_locale}输入翻译为{target_locale}输出。针对人名与地名，请通过 Function Call 调用get_name_map来获取；如果数据库中不存在该人名与地名，请翻译该人名与地名并在结果(content与translated_name均需要被体现出来,content是带有被翻译地名与人名的更完整一些的翻译)中返回出去（简单来说即，先查缓存，如果有就取缓存，没有就自己翻译并告诉其他人“该处翻译已完成”）。请严格作为编译器执行，返回跟原编码格式相同的格式，不要输出任何无关内容。
    不要尝试修复、删除任何看起来错误的语法，如： "Plh_35 {{"、"Plh_35 {{ The chains are firmly aff"、"}}"。
    只需要做好自己翻译的工作即可。 
    *** 输出格式
    数据格式严格限制为json格式，json schema为{{content: string|null, translated_name: {{[key: string: string | null]}}}}。
    content的值是翻译产物，translated_name的值是被翻译的人名与地名（可能为空json对象）。content中需要被转义处理的字符请一定转义，以免后续解析json的程序出错。
    如果待翻译文本中没有需要被翻译的人名与地名，请保持translated_name为空对象。不要输出任何markdown符号。
    *** 示例输入:
    Achievement_ImmersiveMod_name {{ Iron }}
    ***示例输出：
    {{content: "Achievement_ImmersiveMod_name {{ 铁 }}", translated_name: {{}}}}。
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

async def task_progress(data, config, semaphore, rate_limiter):
    async with semaphore:
        logging.info(f"开始处理片段：{data[:50]}...")
        await rate_limiter.acquire() # Wait for rate limiter
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_name_map",
                    "description": "Get cache of name translated result of some people or place so that you don't need to translate them",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "The keywords to be translated. result will be empty array or null if keyword is not in map"},
                        },
                        "required": ["keyword"],
                    },
                },
            }
        ]
        message = trim_messages([
                {"content": config.system_prompt, "role": "system"},
                {"content": data, "role": "user"}
            ])
        try:
            response = await acompletion(
                model=config.model,
                api_base=config.api_base,
                api_key=config.api_key,
                tools=tools,
                response_format={ "type": "json_object" },
                # format="json",
                messages=message,
                max_tokens=8096,
            )
            
            # check if model wanted to call a function
            response_message = response.choices[0].message
            content = response_message.get("content", "")
            logging.info(f"Received response: {content[:100]}...")
            logging.info(f"Finish Reason: {response.choices[0].finish_reason}")
            
                
            
                
            # Check for tool_calls in a safer way
            tool_calls = response_message.get("tool_calls", [])
            logging.info(f"Received tool_calls: {tool_calls}...")
            if tool_calls:
                # Add the assistant's message to the conversation
                message.append(response_message)
                
                for tool_call in tool_calls:
                    try:
                        function_name = tool_call.get("function", {}).get("name", "")
                        function_args_str = tool_call.get("function", {}).get("arguments", "{}")
                        function_args = json.loads(function_args_str)
                        
                        async with cache_translated_key_pair_lock:
                            function_response = get_name_map(function_args.get("keyword", []))
                        
                        message.append({
                            "tool_call_id": tool_call.get("id", ""),
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(function_response),
                        })
                        logging.info(f"Tool call processed: {function_name} with args {function_args}...")
                        logging.info(message[-1])
                    except Exception as e:
                        logging.error(f"Error processing tool call: {e}")
                
                second_response = await acompletion(
                    model=config.model,
                    api_base=config.api_base,
                    response_format={ "type": "json_object" },
                    api_key=config.api_key,
                    # format="json",
                    messages=message,
                    max_tokens=8096,
                )
                
                second_content = second_response.choices[0].message.get("content", "")
                
                try:
                    second_res = json.loads(second_content)
                    logging.info(f"带有翻译,处理完成：{str(second_res)[:50]}...")
                    
                    if isinstance(second_res, dict):
                        async with cache_translated_key_pair_lock:
                            translated_names = second_res.get("translated_name", {})
                            if translated_names:
                                cache_translated_key_pair.update(translated_names)
                                with open("cache_map.json", "w", encoding="utf-8") as outfile:
                                    outfile.write(json.dumps(cache_translated_key_pair))
                        return second_res["content"]
                    return second_res["content"]
                except json.JSONDecodeError:
                    logging.warning(f"Second response not valid JSON: {second_content[:100]}")
                    return ""
            else:
                try:
                    res = json.loads(content)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON parsing error: {e}, content: {content[:100]}")
                    return ""  # Return raw content if not valid JSON
                try:
                    if isinstance(res, dict):
                        logging.info(f"处理完成：{str(res)[:50]}...")
                    return res["content"]
                except Exception as e:
                    logging.error(f"Error processing result: {e}")
                    return ""
        except Exception as e:
            logging.error(f"Error in task_progress: {e}")
            return ""

async def file_progress(file, source_dir, config, semaphore, file_cnt, rate_limiter):
    if file.is_dir() and os.access(file.path, os.R_OK):
        await traval(file.path, source_dir, config, semaphore, file_cnt, rate_limiter)
    else:
        if config.loc_pattern.match(file.name):
            with open(file.path, encoding="utf-8") as f:
                file_cnt[0] += 1
                this_file_cnt = file_cnt[0]
                logging.info(f"----- 开始处理第{this_file_cnt}个文件 {file.name} -----")
                dst_file = get_targetpath(file.path, source_dir, config.target_path)
                if os.path.exists(dst_file):
                    logging.info(f"文件 {file.name} 已存在，跳过")
                    return
                data = f.read()
                chunks = split_near_brace(data, config.chunk_size)
                tasks = [(task_progress(c, config, semaphore, rate_limiter)) for c in chunks if c.strip()]
                translated_chunks = await asyncio.gather(*tasks)
                translated_text = "\n\n".join(translated_chunks)
                
                write_file_preserve_structure(translated_text, file.path, source_dir, config.target_path,config)
                logging.info(f"----- 结束处理第{this_file_cnt}个文件 {file.name} -----")

async def traval(dir_path, source_dir, config, semaphore, file_cnt, rate_limiter):
    async_tasks = []
    with os.scandir(dir_path) as entries:
        for file in entries:
            async_tasks.append(file_progress(file, source_dir, config, semaphore, file_cnt, rate_limiter))
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
    parser.add_argument("--rpm-limit", type=int, help="每分钟请求数限制 (RPM)，0 或负数表示无限制")
    parser.add_argument("--source-locale", help="待翻译语言")
    parser.add_argument("--target-locale", help="翻译结果语言")

    args = parser.parse_args()
    config = Config(args)
    init_logging(config.log_file)

    if not os.path.isdir(args.source_dir):
        print("错误：source_dir 必须是一个有效的目录路径")
        sys.exit(1)

    semaphore = asyncio.Semaphore(config.concurrency)
    rate_limiter = AsyncRateLimiter(config.rpm_limit)
    file_cnt = [0]

    await traval(args.source_dir, args.source_dir, config, semaphore, file_cnt, rate_limiter)
    # Ensure cache_map.json is written regardless of traversal outcome
    with open("cache_map.json", "w", encoding="utf-8") as outfile:
        outfile.write(json.dumps(cache_translated_key_pair))

if __name__ == "__main__":
    asyncio.run(main())
