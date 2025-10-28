import os
import json

def load_memory(file_path="memory.json"):
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(memory, file_path="memory.json"):
    # 自动创建路径
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4, ensure_ascii=False)
