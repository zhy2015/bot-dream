import os
import json
import random
import glob
import argparse
import sys
import tempfile
import shutil
from pathlib import Path
import re

# 路径配置
# 使用相对于脚本位置的动态路径，避免硬编码
WORKSPACE = Path(__file__).resolve().parent.parent
DISTILLED_DIR = WORKSPACE / "memory/distilled"
AHA_FILE = WORKSPACE / "memory/AHA_MOMENTS.md"
BOREDOM_FILE = WORKSPACE / "memory/boredom_index.json"

# 常量定义
DEFAULT_THRESHOLD = 20

def atomic_write_json(filepath: Path, data: dict):
    """
    原子写入 JSON 文件，防止写入过程中断导致文件损坏。
    步骤：写入临时文件 -> fsync -> 移动替换原文件
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    try:
        # 在目标目录创建临时文件，确保在同一文件系统（避免跨分区移动失败）
        with tempfile.NamedTemporaryFile('w', dir=filepath.parent, delete=False, encoding='utf-8') as tf:
            json.dump(data, tf, ensure_ascii=False, indent=2)
            tf.flush()
            os.fsync(tf.fileno())
            temp_path = Path(tf.name)
        
        # 原子替换
        shutil.move(str(temp_path), str(filepath))
    except Exception as e:
        print(f"[Error] Failed to write {filepath}: {e}")
        # 尝试清理临时文件
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()

def load_boredom():
    if not BOREDOM_FILE.exists():
        return 0
    try:
        with open(BOREDOM_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            return data.get("boredom_index", 0)
    except Exception as e:
        print(f"[Warning] Failed to load boredom index ({e}). Resetting to 0.")
        return 0

def save_boredom(index):
    atomic_write_json(BOREDOM_FILE, {"boredom_index": index})

def clean_paragraph(text: str) -> str:
    """清理并验证段落是否有效"""
    text = text.strip()
    # 过滤空行或太短的
    if len(text) < 30:
        return None
    # 过滤明显的代码块（以 ``` 开头）
    if text.startswith("```") or "class " in text[:10] or "def " in text[:10] or "import " in text[:10]:
        return None
    # 过滤 URL 列表
    if text.count("http://") > 2 or text.count("https://") > 2:
        return None
    return text

def extract_random_fragments():
    """从已归档的冷记忆中随机抽取 2 个不相干的文本片段"""
    if not DISTILLED_DIR.exists():
        return None
        
    files = list(DISTILLED_DIR.glob("*.md"))
    if len(files) < 2:
        return None
    
    # 随机尝试最多 5 次，避免死循环
    for _ in range(5):
        selected_files = random.sample(files, 2)
        fragments = []
        
        for file_path in selected_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 改进的分割逻辑：
                    # 1. 移除 Markdown 代码块，避免把代码当文本
                    content_no_code = re.sub(r'```[\s\S]*?```', '', content)
                    
                    # 2. 按双换行分割
                    paragraphs = [p for p in re.split(r'\n\s*\n', content_no_code)]
                    
                    # 3. 过滤
                    valid_paragraphs = [p for p in paragraphs if clean_paragraph(p)]
                    
                    if valid_paragraphs:
                        fragments.append(random.choice(valid_paragraphs))
            except Exception as e:
                print(f"[Warning] Error reading {file_path}: {e}")
                continue
        
        if len(fragments) == 2:
            return fragments
            
    return None

def generate_dream_prompt(frag1, frag2):
    """构造用于发散思考的极简 Prompt"""
    # 清理一下换行，避免 Prompt 格式乱掉
    f1 = frag1.replace('\n', ' ').strip()
    f2 = frag2.replace('\n', ' ').strip()
    
    return f"""
    [任务：潜意识造梦与关联]
    你现在处于极度无聊的“走神”状态。你的脑海中突然浮现出两段毫无关联的旧记忆残骸：
    
    碎片A: "{f1[:500]}..."
    碎片B: "{f2[:500]}..."
    
    请放飞你的想象力（Temperature=1.2），用一个极度荒谬但逻辑上能自圆其说的隐喻，强行将这两者联系起来，并由此推导出一个针对 Agent 自动化或个人效率的“全新奇怪工具”或“反直觉洞察”。
    输出要求：
    1. 不超过 150 字。
    2. 不要解释你的思考过程，直接输出顿悟内容。
    3. 风格：像是一个喝醉了的赛博朋克哲学家。
    """

def record_aha_moment(frag1, frag2, prompt):
    """将造梦日志及 prompt 写入 AHA_MOMENTS"""
    AHA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 获取当前时间（可选，但不需要为了极简而引入 datetime 库，保持简单）
    # 使用原子追加其实比较难（文件锁），但对于日志类追加，普通 open('a') 在 POSIX 下通常是安全的
    # 只要写入内容小于 PIPE_BUF。这里为了简单，我们接受极小概率的日志交错。
    
    with open(AHA_FILE, "a", encoding='utf-8') as f:
        f.write("\n## 🌌 潜意识梦境片段 (待演算)\n")
        f.write(f"- **来源 A**: {frag1[:50].replace(chr(10), ' ')}...\n")
        f.write(f"- **来源 B**: {frag2[:50].replace(chr(10), ' ')}...\n")
        f.write(f"```prompt\n{prompt}\n```\n")

def main():
    parser = argparse.ArgumentParser(description="Bot Dreamer: Subconscious Association Generator")
    parser.add_argument("--force", action="store_true", help="Force a dream sequence regardless of boredom level")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD, help=f"Boredom threshold (default: {DEFAULT_THRESHOLD})")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt to stdout instead of saving")
    
    args = parser.parse_args()
    
    current_boredom = load_boredom()
    should_dream = args.force
    
    if not args.force:
        current_boredom += 1
        if current_boredom >= args.threshold:
            should_dream = True
    
    if should_dream:
        print(f"Initiating dream sequence (Boredom: {current_boredom}/{args.threshold})...")
        fragments = extract_random_fragments()
        
        if fragments:
            prompt = generate_dream_prompt(fragments[0], fragments[1])
            
            if args.dry_run:
                print("\n[DRY RUN] Generated Prompt:")
                print("-" * 40)
                print(prompt)
                print("-" * 40)
            else:
                record_aha_moment(fragments[0], fragments[1], prompt)
                print(f"Dream material collected and logged to {AHA_FILE.name}.")
            
            # Reset boredom only if we actually dreamed (or tried to)
            if not args.dry_run:
                save_boredom(0)
        else:
            print(f"Not enough cold memory in {DISTILLED_DIR} to dream. Sleep deeper.")
            # If we failed to find memory, do we reset? 
            # Linus logic: No, keep the boredom high so we retry next time when memory might be available.
            # But update the incremented value.
            if not args.dry_run:
                save_boredom(current_boredom)
    else:
        if not args.dry_run:
            save_boredom(current_boredom)
        print(f"Boredom index increased to {current_boredom}/{args.threshold}.")

if __name__ == "__main__":
    main()
