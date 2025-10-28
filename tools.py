import json
import requests

# 搜索
def real_search(query):
    """
    使用 Serper.dev 进行真实搜索
    """
    url = "https://google.serper.dev/search "
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': "f01f38d5155bac3c0c623a78b8cd5cb9e81c9894",
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        results = response.json()
        if "organic" in results:
            summaries = []
            for item in results["organic"][:3]:  # 取前三个结果
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                summaries.append(f"🔹 {title}\n{snippet}")
            return "\n".join(summaries)
        else:
            return "未搜索到相关结果。"
    except Exception as e:
        return f"搜索失败: {e}"