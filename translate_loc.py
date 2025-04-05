import asyncio
import re
import sys
import logging
from litellm import acompletion
from litellm.utils import trim_messages
import os

# 设置日志配置：同时输出到控制台和当前目录下的 execution.log 文件
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# 文件处理器（日志文件在当前执行目录下）
log_file = os.path.join(os.getcwd(), "execution.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

key = "sk-"
model = "openai/kimi-latest"
# model = "openai/kimi-latest"
api_base = "https://api.moonshot.cn/v1"
# api_base = "https://api.deepseek.com"
system_prompt = "你是drova这款游戏的翻译编译器，请帮我将给定的的英文输入翻译为中文输出。人名与地名不需要被翻译。请严格作为编译器执行，返回跟原编码格式相同的格式，不要输出任何无关内容。\n不要尝试修复、删除任何看起来错误的语法，如： \"Plh_35 {\"、\"Plh_35 { The chains are firmly aff\"、\"}\" \n  \n只需要做好自己翻译的工作即可。 \n *** 示例输入:\nAchievement_ImmersiveMod_name { Iron }\n ***示例输出：\nAchievement_ImmersiveMod_name { 铁 }。\n请结合这款游戏的背景进行翻译，这款游戏的背景如下：\"Drova - Forsaken Kin\" 是一款受经典黑暗风格和凯尔特神话神秘魅力启发的像素风格动作角色扮演游戏。进入一个精心制作的开放世界，你的选择和行动将影响环境。一个社会发现了已经灭亡帝国的力量：捕捉并支配掌管自然的灵魂。然而，余下的灵魂因为愤怒而分裂。你将站在哪一边？入两个阵营之一，每个阵营都有其自己的价值观并追求各自的目标。你的选择将对整个游戏产生影响，并改变整个故事。所有的决定都伴随着代价。遇见导师并学习各种技能，但也要小心敌人和背叛。危险的景观中开辟自己的道路，完成任务、进行交易、收集和制作装备。你将从无到有，从无名之辈成长起来。研究周围的环境，利用周围的线索揭示谜团并变得更强。只有你的战斗技能才能将你与必然的死亡隔开。索自然，封印掌控它的灵魂力量。学会如何将它们为你所用，但也要准备好迎接这些灵魂的愤怒，它们的愤怒将在你周围的世界中显现。"
# key= is optional, you can configure the key in other ways
loc_pattern = re.compile(r'.*\.loc$')
target_path = "/home/simooo/work/zh"
file_cnt = 0
background_tasks = set()

semaphore = asyncio.Semaphore(10)

async def task_progress(data):
    async with semaphore:
        logging.info(f"开始处理：{data}")
        response = await acompletion(
            model=model,
            api_base=api_base,
            api_key=key,
            messages=trim_messages([
                {"content": system_prompt, "role": "system"},
                { "content": data,"role": "user"}], max_tokens=8096)
        )
        res = response["choices"][0]["message"]["content"]
        logging.info(f"处理完毕结果为：{res}")
        return res

def get_targetpath(src_file, src_root, dst_root):
    rel_path = os.path.relpath(src_file, src_root)
    return os.path.join(dst_root, rel_path)

def write_file_preserve_structure(data,src_file, src_root, dst_root):
    dst_file = get_targetpath(src_file, src_root, dst_root)
    # 确保目标目录存在
    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    
    with open(dst_file, "w") as f:
        f.write(data)
def split_near_brace(text, step=300):
    chunks = []
    start = 0
    n = len(text)
    
    while start < n:
        # 候选结束位置（start + step 或字符串末尾）
        end_candidate = min(start + step, n)
        
        # 如果已经是最后一段，直接添加剩余部分
        if end_candidate == n:
            chunks.append(text[start:])
            break
        
        # 从候选位置向前查找最近的 '{'
        split_pos = text.rfind('}', start, end_candidate + 1)
        
        # 如果没找到 '{'，则直接按 step 分割
        if split_pos == -1:
            split_pos = end_candidate
        
        chunks.append(text[start:split_pos + 1])  # 包含 '{'
        start = split_pos + 1  # 下一段从 '{' 之后开始
    
    return chunks

async def main():
    if len(sys.argv) <= 1:
        raise "You should pass directory path as option"
    global source_dir
    source_dir = sys.argv[1]
    source_dir = os.path.join(source_dir)
    await traval(source_dir)

async def file_progress(file,):
    global source_dir
    global target_path
    global file_cnt
    if file.is_dir() and os.access(file.path, os.R_OK):
        await traval(file.path)
    else:
        if loc_pattern.match(file.name) is not None:
            with open(file) as f:
                file_cnt+=1
                logging.info(f"--------------开始处理第{file_cnt}个文件 {file.name} ---------------")
                dst_file = get_targetpath(file.path, source_dir, target_path)
                if os.path.exists(dst_file):
                    logging.info(f"文件 {file.name} 已存在，跳过")
                    print(f"第一个文件{file.name}已存在，跳过")
                    return
                data = f.read()
                chunk_size = 2000
                split_file = split_near_brace(data, chunk_size)
                # 过滤空行并生成协程列表
                coroutines = [task_progress(line) for line in split_file if line.strip()]
                # 并发执行所有任务
                done_txt_arr = await asyncio.gather(*coroutines)
                done_text = "\n\n".join(done_txt_arr)
                write_file_preserve_structure(done_text, file.path, source_dir, target_path)
                logging.info(f"-----------结束处理第{file_cnt}个文件 {file.name}，写入到 target_path ----------")
            
async def traval(dir):
    files = os.scandir(dir)
    tasks = []
    for file in files:
        tasks.append(file_progress(file))  # 收集所有任务
    if tasks:  # 如果有任务再执行
        await asyncio.gather(*tasks)  # 一次性并发所有任务

if __name__ == "__main__":
    asyncio.run(main()) 
