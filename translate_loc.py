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
from loc_ast_parser import parse_loc_content, extract_translation_candidates, serialize_to_loc_format, LocASTParser

# ------------------- 加载 .env 配置 -------------------
load_dotenv()

class TranslationCache:
    def __init__(self, cache_file="cache_map.json"):
        self.cache_file = cache_file
        self.cache = {}
        self.lock = asyncio.Lock()
        self._load_cache()
    
    def _load_cache(self):
        """从缓存文件加载翻译对"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    loaded_cache = json.load(f)
                    if isinstance(loaded_cache, dict):
                        self.cache = loaded_cache
                        logging.info(f"已从 {self.cache_file} 加载 {len(self.cache)} 条翻译缓存")
                    else:
                        logging.warning(f"缓存文件格式无效，将创建新缓存")
                        self.cache = {}
            else:
                logging.info(f"缓存文件 {self.cache_file} 不存在，将创建新缓存")
        except json.JSONDecodeError as e:
            logging.error(f"缓存文件 JSON 格式错误: {e}，将创建新缓存")
            self.cache = {}
        except Exception as e:
            logging.error(f"加载缓存文件失败: {e}")
            self.cache = {}
    
    def get_name_map(self, keys):
        """获取指定键的翻译映射"""
        if not keys:
            return {}
        return {k: self.cache[k] for k in keys if k in self.cache}
    
    async def update(self, new_translations):
        """更新翻译缓存"""
        if not new_translations:
            return
            
        async with self.lock:
            # Filter out None values and empty strings
            valid_translations = {k: v for k, v in new_translations.items()
                                if v is not None and str(v).strip()}
            if valid_translations:
                self.cache.update(valid_translations)
                await self._save_unsafe()
    
    async def save(self):
        """保存缓存到文件（线程安全版本）"""
        async with self.lock:
            await self._save_unsafe()
    
    async def _save_unsafe(self):
        """保存缓存到文件（内部方法，不获取锁）"""
        try:
            # Create directory if it doesn't exist
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
                
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logging.info(f"已保存 {len(self.cache)} 条翻译缓存到 {self.cache_file}")
        except Exception as e:
            logging.error(f"保存缓存文件失败: {e}")
            # Don't re-raise to avoid breaking the translation process

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
        self.cache_file = args.cache_file or (os.getenv("CACHE_FILE", "cache_map.json"))
        self.translation_cache = TranslationCache(self.cache_file)
        self.system_prompt = system_prompt_create(self.source_locale, self.target_locale)
        self.loc_pattern = re.compile(r'.*\.loc$')
        self.localization_target_pattern = re.compile(r'(.+)_.+\.loc$')
        

# ------------------- 默认系统提示词 -------------------
def system_prompt_create(source_locale, target_locale):
    return f"""
    你是drova这款游戏的翻译编译器，请帮我将给定的{source_locale}文本翻译为{target_locale}输出。
    
    针对人名与地名，请通过 Function Call 调用get_name_map来获取；如果数据库中不存在该人名与地名，请翻译该人名与地名并在结果中返回出去。
    
    *** 输出格式
    你的输出内容必须为有效的JSON格式，包含两个字段：
    - content: 翻译后的完整文本内容
    - translated_name: 被翻译的人名与地名映射（可能为空对象）
    
    示例输入:
    Achievement_ImmersiveMod_name {{ Iron }}
    
    示例输出：
    {{"content": "Achievement_ImmersiveMod_name {{ 铁 }}", "translated_name": {{}}}}
    
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

# ------------------- 预处理函数 -------------------
def extract_pure_game_text(content: str) -> tuple[str, list[tuple[str, str]]]:
    """
    使用LocASTParser提取纯游戏文本内容，去除键值对结构
    返回纯文本内容和原始条目结构，便于后续重新组装
    
    Returns:
        tuple: (pure_text, original_entries)
    """
    parser = LocASTParser()
    entries = parser.parse_file(content)
    
    # 提取所有需要翻译的文本值
    pure_texts = []
    for key, value in entries:
        # 只提取需要翻译的文本（不包含非ASCII字符的文本）
        if not any(ord(c) > 127 for c in value):
            pure_texts.append(value)
    
    # 将文本合并为纯文本格式，便于LLM处理
    return "\n".join(pure_texts), entries

def reassemble_translated_content(translated_text: str, original_entries: list[tuple[str, str]]) -> str:
    """
    将翻译后的纯文本重新组装回原始序列化格式
    
    Args:
        translated_text: LLM返回的翻译后纯文本
        original_entries: 原始解析的条目列表
        
    Returns:
        重新组装后的.loc格式内容
    """
    parser = LocASTParser()
    
    # 分割翻译后的文本行
    translated_lines = translated_text.strip().split('\n')
    
    # 创建新的条目列表
    new_entries = []
    translated_index = 0
    
    for key, original_value in original_entries:
        # 检查原始值是否需要翻译
        if not any(ord(c) > 127 for c in original_value):
            # 需要翻译的条目，使用翻译后的文本
            if translated_index < len(translated_lines):
                new_value = translated_lines[translated_index].strip()
                translated_index += 1
            else:
                # 如果没有足够的翻译行，保留原始值
                new_value = original_value
        else:
            # 不需要翻译的条目（可能已经包含非ASCII字符），保留原始值
            new_value = original_value
        
        new_entries.append((key, new_value))
    
    # 序列化回.loc格式
    return parser.serialize_entries(new_entries)

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
        
        # 预处理：提取纯游戏文本内容和原始结构
        pure_game_text, original_entries = extract_pure_game_text(data)
        logging.info(f"预处理完成：提取到{len(pure_game_text)}字符的纯游戏文本，{len(original_entries)}个条目")
        
        # Use AST parser to analyze the content
        analysis = extract_translation_candidates(data)
        logging.info(f"AST分析结果：需要翻译{len(analysis['to_translate'])}条，发现{len(analysis['names'])}个潜在名称")
        
        # Prepare names for function call
        names_to_check = analysis['names']
        
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
        
        # Prepare the prompt with analyzed names and pure game text
        enhanced_prompt = f"{config.system_prompt}\n\n需要翻译的文本：\n{pure_game_text}"
        if names_to_check:
            enhanced_prompt += f"\n\n注意：文本中可能包含以下名称需要翻译：{', '.join(names_to_check)}"
        
        message = trim_messages([
                {"content": enhanced_prompt, "role": "system"},
                {"content": pure_game_text, "role": "user"}
            ])
        try:
            response = await acompletion(
                model=config.model,
                extra_body={ "enable_thinking": False },
                api_base=config.api_base,
                api_key=config.api_key,
                tools=tools,
                response_format={ "type": "json_object" },
                temperature=0,
                messages=message,
                max_tokens=8096,
            )

            # Debug: Log response structure
            # logging.info(f"Raw response: {response}")
            if not hasattr(response, "choices") or not response.choices:
                logging.error("Response has no 'choices' attribute or is empty.")
                return ""
            if not hasattr(response.choices[0], "message") or response.choices[0].message is None:
                logging.error("First choice has no 'message' attribute or is None.")
                return ""

            # check if model wanted to call a function
            response_message = response.choices[0].message
            
            content = response_message.content or ""
            logging.info(f"Received response: {content[:100]}...")
            logging.info(f"Finish Reason: {response.choices[0].finish_reason}")
            
            # Check for tool_calls in a safer way
            tool_calls = response_message.tool_calls or []
            logging.info(f"Received tool_calls: {tool_calls}...")
            if tool_calls:
                # Add the assistant's message to the conversation
                message.append(response_message)
                
                for tool_call in tool_calls:
                    try:
                        function_name = tool_call.get("function", {}).get("name", "")
                        function_args_str = tool_call.get("function", {}).get("arguments", "{}")
                        function_args = json.loads(function_args_str)
                        
                        function_response = config.translation_cache.get_name_map(function_args.get("keyword", []))
                        
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
                    extra_body={ "enable_thinking": False },
                    temperature=0,
                    messages=message,
                    max_tokens=8096,
                )
                
                second_content = second_response.choices[0].message.get("content", "")
                
                try:
                    second_res = json.loads(second_content)
                    logging.info(f"带有翻译,处理完成：{str(second_res)[:50]}...")
                    
                    if isinstance(second_res, dict):
                        translated_names = second_res.get("translated_name", {})
                        if translated_names:
                            await config.translation_cache.update(translated_names)
                        
                        # 后处理：重新组装翻译内容
                        translated_content = second_res["content"] or ""
                        reassembled_content = reassemble_translated_content(translated_content, original_entries)
                        return reassembled_content
                    return second_res["content"] or ""
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
                    
                    # 后处理：重新组装翻译内容
                    translated_content = res["content"] or ""
                    reassembled_content = reassemble_translated_content(translated_content, original_entries)
                    return reassembled_content
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
            with open(file.path,"r", encoding="utf-8") as f:
                file_cnt[0] += 1
                this_file_cnt = file_cnt[0]
                dst_file = get_targetpath(file.path, source_dir, config.target_path)
                dst_file = re.sub(config.localization_target_pattern,f"\\1_{config.target_locale}.loc",dst_file)
            
                logging.info(f"----- 开始处理第{this_file_cnt}个文件 {file.name} 路径为{dst_file} -----")                
                # 修正跳过文件逻辑：确保生成的目标文件名与实际输出文件名完全一致
                if os.path.exists(dst_file):
                    logging.info(f"文件 {file.name} 已存在，跳过")
                    return
                data = f.read()
                chunks = split_near_brace(data, config.chunk_size)
                tasks = [(task_progress(c, config, semaphore, rate_limiter)) for c in chunks if c.strip()]
                translated_chunks = await asyncio.gather(*tasks)
                translated_text = "\n\n".join(translated_chunks)
                # 修正文件写入逻辑：确保生成的目标文件名与跳过检查逻辑完全一致
                write_file_preserve_structure(translated_text, file.path, source_dir, config.target_path, config)
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
    parser.add_argument("--cache-file", help="翻译缓存文件路径")

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
    # Ensure cache is saved at the end
    await config.translation_cache.save()

if __name__ == "__main__":
    asyncio.run(main())
