import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 统一放在项目根下的 data 目录，PyCharm 运行也能自动找到
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MEMORY_BASE = PROJECT_ROOT / "data" / "memory"


class JsonDirStore:
    """
    按 yyyy-mm-dd/主题.json 分目录存储
    支持同一主题多轮对话追加
    """

    def __init__(self):
        MEMORY_BASE.mkdir(parents=True, exist_ok=True)

    # ------- 内部工具 -------
    def _dir(self, date: str) -> Path:
        d = MEMORY_BASE / date
        d.mkdir(exist_ok=True)
        return d

    def _file(self, topic: str, date: str) -> Path:
        # 把 topic 中的特殊字符替换成安全文件名
        safe = "".join(c if c.isalnum() else "_" for c in topic)
        return self._dir(date) / f"{safe}.json"

    # ------- 对外 API -------
    def load(self, topic: str) -> Dict[str, Any]:
        """没文件返回空 dict"""
        date = datetime.now().strftime("%Y-%m-%d")
        f = self._file(topic, date)
        if not f.exists():
            return {}
        return json.loads(f.read_text(encoding="utf-8"))

    def save(self, topic: str, data: Dict[str, Any]) -> None:
        date = datetime.now().strftime("%Y-%m-%d")
        f = self._file(topic, date)
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def append_history(self, topic: str, role: str, content: str) -> None:
        """同一主题持续追加对话记录"""
        old = self.load(topic)
        if "history" not in old:
            old["history"] = []
        old["history"].append(
            {"time": datetime.now().isoformat(), "role": role, "content": content}
        )
        self.save(topic, old)


# 全局单例，其它模块直接 from json_store import store
store = JsonDirStore()