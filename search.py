import http.client
import json
import webbrowser
from tts import realtime_tts_speak
import os
from dotenv import load_dotenv

load_dotenv()  # 默认会加载根目录下的.env文件

def search_chat2(content: str):
    """

    :param content:
    :return:
    """
    conn = http.client.HTTPSConnection("metaso.cn")
    payload = json.dumps(
        {"q": content, "scope": "webpage", "includeSummary": False, "size": "10", "includeRawContent": True,
         "conciseSnippet": False})
    headers = {
        'Authorization': 'Bearer '+os.getenv("METASO_API_KEY"),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/v1/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    #print(data.decode("utf-8"))
    return data.decode("utf-8")

def search_chat(content: str) -> str:
    """
    搜索内容并返回答案，用来搜索

    :param content: 搜索的查询内容
    :return: 搜索结果的答案内容，已清理引用标记
    """
    realtime_tts_speak("正在搜索中", rate=27000)
    conn = http.client.HTTPSConnection("metaso.cn")
    payload = json.dumps({"q": content, "model": "fast", "format": "simple"})
    headers = {
      'Authorization': 'Bearer '+os.getenv("METASO_API_KEY"),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/v1/chat/completions", payload, headers)
    res = conn.getresponse()
    data = res.read()

    # 解析JSON响应
    json_data = json.loads(data.decode("utf-8"))

    # 提取answer内容
    if 'answer' in json_data:
        answer_content = json_data['answer']
        # 删除所有类似[[1]]的引用标记
        import re
        cleaned_answer = re.sub(r'\[\[\d+\]\]', '', answer_content)
        # 去除所有换行符
        cleaned_answer = cleaned_answer.replace('\n', '').replace('\r', '')
        # 清理多余的空格
        cleaned_answer = re.sub(r'\s+', ' ', cleaned_answer).strip()
        return cleaned_answer

    else:
        return "没有搜索到相关内容"

def open_webpage(content: str) -> (list, str):
    """
    打开相关网页，用来打开网页

    :param content: 搜索的查询内容
    :return: 包含网页标题和链接的列表
    """
    #realtime_tts_speak("好的，马上打开", rate=25000)
    conn = http.client.HTTPSConnection("metaso.cn")
    payload = json.dumps({"q": content, "scope": "webpage", "includeSummary": True, "size": "5", "includeRawContent": False, "conciseSnippet": False})
    headers = {
      'Authorization': 'Bearer '+os.getenv("METASO_API_KEY"),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/v1/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    # 解析JSON响应
    json_data = json.loads(data.decode("utf-8"))
    # 提取webpages中的title和link
    titles_and_links = []
    if 'webpages' in json_data and isinstance(json_data['webpages'], list):
        for webpage in json_data['webpages']:
            if 'title' in webpage and 'link' in webpage:
                titles_and_links.append({
                    'title': webpage['title'],
                    'link': webpage['link']
                })
    # 打开网页链接
    for i, item in enumerate(titles_and_links):
        if i < 5:  # 限制打开前5个链接，避免打开过多网页
            webbrowser.open_new(item['link'])
    return titles_and_links, "已打开相关网页"


if __name__ == "__main__":
    # results = open_webpage("如何使用python")
    # for item in results:
    #     print(item)
    #     print("-" * 50)
    print(search_chat2("超兽武装"))
    #print(search_chat("如何使用python"))


