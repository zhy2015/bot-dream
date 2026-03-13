import os
import json
import random
import glob
from pathlib import Path
import re

# 路径配置
WORKSPACE = "/root/.openclaw/workspace"
DISTILLED_DIR = os.path.join(WORKSPACE, "memory/distilled")
AHA_FILE = os.path.join(WORKSPACE, "memory/AHA_MOMENTS.md")
BOREDOM_FILE = os.path.join(WORKSPACE, "memory/boredom_index.json")

def load_boredom():
    if not os.path.exists(BOREDOM_FILE):
        return 0
    try:
        with open(BOREDOM_FILE, "r") as f:
            data = json.load(f)
            return data.get("boredom_index", 0)
    except:
        return 0

def save_boredom(index):
    os.makedirs(os.path.dirname(BOREDOM_FILE), exist_ok=True)
    with open(BOREDOM_FILE, "w") as f:
        json.dump({"boredom_index": index}, f)

def extract_random_fragments():
    """从已归档的冷记忆中随机抽取 2 个不相干的文本片段"""
    files = glob.glob(f"{DISTILLED_DIR}/*.md")
    if len(files) < 2:
        return None
    
    # 随机选两个文件
    selected_files = random.sample(files, 2)
    fragments = []
    
    for file in selected_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 简单按段落分割，过滤空行和过短的行
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if len(p.strip()) > 30]
            if paragraphs:
                fragments.append(random.choice(paragraphs))
            else:
                # 兜底：如果文件没有空行分隔的段落，按行抽取
                lines = [l.strip() for l in content.split('\n') if len(l.strip()) > 30]
                if lines:
                    fragments.append(random.choice(lines))
                    
    if len(fragments) == 2:
        return fragments
    return None

def generate_dream_prompt(frag1, frag2):
    """构造用于发散思考的极简 Prompt"""
    return f"""
    [任务：潜意识造梦与关联]
    你现在处于极度无聊的“走神”状态。你的脑海中突然浮现出两段毫无关联的旧记忆残骸：
    
    碎片A: "{frag1}"
    碎片B: "{frag2}"
    
    请放飞你的想象力（Temperature=1.2），用一个极度荒谬但逻辑上能自圆其说的隐喻，强行将这两者联系起来，并由此推导出一个针对 Agent 自动化或个人效率的“全新奇怪工具”或“反直觉洞察”。
    输出要求：
    1. 不超过 150 字。
    2. 不要解释你的思考过程，直接输出顿悟内容。
    3. 风格：像是一个喝醉了的赛博朋克哲学家。
    """

def record_aha_moment(frag1, frag2, prompt):
    """将造梦日志及 prompt 写入 AHA_MOMENTS，供外部 LLM 调用生成"""
    # 注意：为了极致轻量，本 Python 脚本不直接调用 LLM API，而是生成造梦任务单。
    # 真正的 LLM 消耗将由主节点在决定要执行梦境时（通过 sessions_spawn）完成。
    os.makedirs(os.path.dirname(AHA_FILE), exist_ok=True)
    with open(AHA_FILE, "a", encoding='utf-8') as f:
        f.write("\n## 🌌 潜意识梦境片段 (待演算)\n")
        f.write(f"- **来源 A**: {frag1[:50]}...\n")
        f.write(f"- **来源 B**: {frag2[:50]}...\n")
        f.write(f"```prompt\n{prompt}\n```\n")

def tick_boredom_and_maybe_dream():
    current_boredom = load_boredom()
    # 模拟一次 Heartbeat 无事可做
    current_boredom += 1
    
    if current_boredom >= 20:
        print("Boredom threshold reached. Initiating dream sequence...")
        fragments = extract_random_fragments()
        if fragments:
            prompt = generate_dream_prompt(fragments[0], fragments[1])
            record_aha_moment(fragments[0], fragments[1], prompt)
            print("Dream material collected and logged to AHA_MOMENTS.md.")
        else:
            print("Not enough cold memory to dream. Sleep deeper.")
        
        # 造梦后重置无聊度
        save_boredom(0)
    else:
        save_boredom(current_boredom)
        print(f"Boredom index increased to {current_boredom}/20.")

if __name__ == "__main__":
    tick_boredom_and_maybe_dream()
