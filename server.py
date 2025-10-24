#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
1. 初始化fastmcp
2. 创建一个函数，文档，功能描述、参数描述、返回值描述
3. 使用@tool 注解
3. 启动 mcp 服务器
"""
import time
from datetime import datetime
import pyautogui
from tts import realtime_tts_speak
import webbrowser
from fastmcp import FastMCP
import http.client
import json
from Weather_data_get import get_weather
import sys
from read_webpage import read_webpage, extract_current_webpage_url, convert_document_to_txt
from agent_vision import get_image_response
from screen_shot_opencv import capture_screen_opencv_only
from get_active_window import get_activate_path, get_active_window_info, activate_window_by_pid
from open_app import create_and_open_word_doc, open_netease_music
from write_file import ai_write_and_open_txt, ai_write_code_and_open_txt
from summarize_write_ai import code_ai_explain_model, get_file_summary
import pyperclip
from write_file import write_and_open_txt
from control_iflow import use_iflow_in_cmd
from markdown_to_mord_fun import md_to_word, create_file_path, open_word_doc
import subprocess
import os
from dotenv import load_dotenv
from gesture_main_use import main_gesture
from markdown_to_excel import markdown_to_excel_main

load_dotenv()  # 默认会加载根目录下的.env文件

mcp = FastMCP()

@mcp.tool()
def get_city_weather(city: str = None) -> str:
    """
    获取城市天气情况，查询指定城市的当前天气信息
    
    该函数通过和风天气API获取指定城市的当前天气状况，包括温度、湿度、风力等信息。
    如果未指定城市，则默认查询电脑IP所在城市的天气情况。
    
    Args:
        city (str, optional): 城市名称，支持中文城市名，如"北京"、"上海"等。
            默认值为None，此时查询电脑IP所在城市的天气情况。
            
    Returns:
        str: 城市天气情况的详细描述。包含温度、湿度、风力等信息。
            
    Example:
        >>> get_city_weather()
        '当前天气情况: 降水量: 0.0, 温度: 11.9°C, 体感温度: 7.2°C, 降水量: 0.0mm, 湿度: 43.0%, 风向: 西北风, 风力等级: 4级'
        
        >>> get_city_weather("北京")
        '当前天气情况: 降水量: 0.0, 温度: 12.9°C, 体感温度: 8.2°C, 降水量: 0.0mm, 湿度: 43.0%, 风向: 西北风, 风力等级: 4级'
        
        >>> get_city_weather("上海")
        '当前天气情况: 降水量: 0.0, 温度: 16.0°C, 体感温度: 10.0°C, 降水量: 0.0mm, 湿度: 85.0%, 风向: 北风, 风力等级: 4级'
        
    Note:
        需要配置正确的和风天气API密钥才能正常使用此功能。
        如果API调用失败，会返回相应的错误提示信息。
    """
    try:
        if city:
            return get_weather(city)
        else:
            return get_weather()
    except Exception as e:
        return f"获取天气信息失败，请检查是否使用正确的和风天气API"


@mcp.tool()
def search_chat(content: str) -> str:
    """
    搜索相关内容并返回答案，在未指定具体网站时用于搜索相关信息，不用于打开网页。
    用AI搜索引擎搜索相关内容。
    
    该函数通过调用 metaso 搜索引擎 API 来搜索指定内容，并返回搜索结果的 JSON 字符串。
    搜索范围为网页内容，返回结果包含网页标题、链接和摘要等信息。
    
    Args:
        content (str): 要搜索的查询内容，可以是问题、关键词或短语
        
    Returns:
        str: 搜索结果的 JSON 字符串，包含以下字段：
            - webpages: 网页搜索结果列表
              - title: 网页标题
              - link: 网页链接
              - snippet: 网页内容摘要
            - total: 搜索结果总数
            - 其他相关搜索信息
            
    Example:
        >>> search_chat("人工智能发展现状")
        '{"webpages": [{"title": "人工智能发展报告2023", "link": "https://example.com/ai-report", "snippet": "人工智能技术近年来发展迅速..."}, ...], "total": 20}'
        
        >>> search_chat("Python编程教程")
        '{"webpages": [{"title": "Python基础教程", "link": "https://example.com/python-tutorial", "snippet": "Python是一种高级编程语言..."}, ...], "total": 15}'
        
        >>> search_chat("不存在的内容")
        '没有搜索到相关内容'
        
    Note:
        需要配置正确的 METASO_API_KEY 环境变量才能正常使用此功能。
        搜索结果最多返回20条相关网页信息。
    """
    realtime_tts_speak("正在搜索中", rate=27000)
    try:
        conn = http.client.HTTPSConnection("metaso.cn")
        payload = json.dumps({"q": content, "scope": "webpage", "includeSummary": True, "size": "30",
                              "includeRawContent": False, "conciseSnippet": False})
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
        #return cleaned_answer
    except Exception as e:
        return "没有搜索到相关内容"

@mcp.tool()
def search_in_websites(website_names: list, search_contents: list) -> str:
    """
    在指定的多个网站中同时搜索多个内容，支持在常用网站内搜索相关内容
    
    该函数可以根据用户指定的网站列表和搜索内容列表，构建相应的搜索URL并在浏览器中打开搜索结果页面。
    支持多种类型的网站，包括社交媒体、购物、视频、新闻、开发技术等网站。

    Args:
        website_names (list): 要进行搜索的网站名称列表，支持以下网站：
            社交媒体类: 微博、微信网页版、QQ空间、Facebook、Twitter、Instagram、LinkedIn
            视频娱乐类: 哔哩哔哩网页、抖音网页、快手网页、YouTube、爱奇艺网页、腾讯视频网页、优酷网页
            购物类: 淘宝、天猫、京东、拼多多、亚马逊、 eBay
            新闻资讯类: 新浪新闻、腾讯新闻、网易新闻、今日头条、知乎、澎湃新闻
            搜索引擎类: 百度、必应、搜狗
            开发技术类: GitHub、CSDN、博客园、StackOverflow、掘金
            学习教育类: 学习通、智慧树、中国大学MOOC、网易云课堂、哔哩哔哩网页、抖音网页、小红书网页
            办公工具类: 腾讯文档、石墨文档
            邮箱类: QQ邮箱、网易邮箱、Gmail、Outlook
            其他: 小红书、美团、携程、58同城
        search_contents (list): 要搜索的内容关键词或短语列表

    Returns:
        str: 操作结果描述，包括：
            - 成功打开搜索页面时返回确认信息
            - 不支持的网站返回提示信息
            - 出现错误时返回错误描述

    Example:
        >>> search_in_websites(["知乎", "GitHub"], ["人工智能发展现状", "python tutorial"])
        '已在以下网站中搜索相关内容：知乎(人工智能发展现状), GitHub(python tutorial)，请查看浏览器结果。'

        >>> search_in_websites(["知乎", "GitHub"], ["人工智能发展现状"])
        '已在以下网站中搜索相关内容：知乎(人工智能发展现状), GitHub(人工智能发展现状)，请查看浏览器结果。'

        >>> search_in_websites(["未知网站"], ["搜索内容"])
        '部分网站不支持搜索：未知网站'
    """
    # 网站搜索URL映射字典
    website_search_urls = {
        # 社交媒体类
        '微博': 'https://s.weibo.com/weibo?q={}',
        '微信网页版': 'https://weixin.sogou.com/weixin?type=2&query={}',
        'facebook': 'https://www.facebook.com/search/posts/?q={}',
        'twitter': 'https://twitter.com/search?q={}',
        'instagram': 'https://www.instagram.com/explore/tags/{}/',
        'linkedin': 'https://www.linkedin.com/search/results/all/?keywords={}',

        # 视频娱乐类
        '哔哩哔哩网页': 'https://search.bilibili.com/all?keyword={}',
        '抖音网页': 'https://www.douyin.com/search/{}',
        '快手网页': 'https://www.kuaishou.com/search/video?searchKey={}',
        'youtube': 'https://www.youtube.com/results?search_query={}',
        '爱奇艺网页': 'https://so.iqiyi.com/so/q_{}',
        '腾讯视频网页': 'https://v.qq.com/x/search/?q={}',
        '优酷网页': 'https://so.youku.com/search_video/q_{}',

        # 购物类
        '淘宝': 'https://s.taobao.com/search?q={}',
        '天猫': 'https://list.tmall.com/search_product.htm?q={}',
        '京东': 'https://search.jd.com/Search?keyword={}',
        '拼多多': 'https://search.pinduoduo.com/search_result.html?search_key={}',
        '亚马逊': 'https://www.amazon.com/s?k={}',
        'eBay': 'https://www.ebay.com/sch/i.html?_nkw={}',

        # 新闻资讯类
        '新浪新闻': 'https://search.sina.com.cn/?q={}',
        '腾讯新闻': 'https://new.qq.com/search?query={}',
        '网易新闻': 'https://www.163.com/news/search?keyword={}',
        '今日头条': 'https://so.toutiao.com/search?keyword={}',
        '知乎': 'https://www.zhihu.com/search?type=content&q={}',
        '澎湃新闻': 'https://www.thepaper.cn/searchResult.jsp?searchword={}',

        # 搜索引擎类
        '百度': 'https://www.baidu.com/s?wd={}',
        '谷歌': 'https://www.google.com/search?q={}',
        '必应': 'https://www.bing.com/search?q={}',
        '搜狗': 'https://www.sogou.com/web?query={}',

        # 开发技术类
        'github': 'https://github.com/search?q={}',
        'csdn': 'https://so.csdn.net/so/search?q={}',
        '博客园': 'https://zzk.cnblogs.com/s/blogpost?Keywords={}',
        'stackoverflow': 'https://stackoverflow.com/search?q={}',
        '掘金': 'https://juejin.cn/search?query={}',

        # 学习教育类
        '学习通': 'https://passport2.chaoxing.com/search?keyword={}',
        '智慧树': 'https://www.zhihuishu.com/search?keyword={}',

        '中国大学mooc': 'https://www.icourse163.org/search.htm?search={}#/sm',
        '网易云课堂': 'https://study.163.com/search/search.htm?keyword={}',

        # 办公工具类
        '腾讯文档': 'https://docs.qq.com/desktop/search?keyword={}',
        '石墨文档': 'https://shimo.im/search/all?query={}',
        '阿里云盘网页': 'https://www.aliyundrive.com/search?query={}',
        '百度网盘网页': 'https://pan.baidu.com/disk/main?from=homeSearch#search/key={}',

        # 邮箱类
        'qq邮箱': 'https://mail.qq.com/cgi-bin/mail_list?searchword={}',
        '网易邮箱': 'https://mail.163.com/js6/search/main.jsp?keyword={}',
        'gmail': 'https://mail.google.com/mail/u/0/#search/{}',
        'outlook': 'https://outlook.live.com/mail/0/search/{}',

        # 其他
        '小红书': 'https://www.xiaohongshu.com/search_result?keyword={}',
        '美团': 'https://www.meituan.com/search/{}',
        '携程': 'https://www.ctrip.com/search/?query={}',
        '58同城': 'https://bj.58.com/sou/?key={}'
    }

    try:
        # 检查输入参数是否为列表
        if not isinstance(website_names, list) or not isinstance(search_contents, list):
            return "参数错误：website_names 和 search_contents 必须是列表"
        
        # 如果搜索内容列表为空，返回错误
        if not search_contents:
            return "搜索内容列表不能为空"
        
        # 如果网站列表为空，返回错误
        if not website_names:
            return "网站名称列表不能为空"
        
        # 存储成功和失败的操作
        successful_searches = []
        failed_sites = []
        
        # 遍历所有网站和搜索内容的组合
        for website_name in website_names:
            # 检查网站是否支持
            if website_name in website_search_urls:
                # 对每个搜索内容在该网站中搜索
                for search_content in search_contents:
                    try:
                        # 构建搜索URL
                        search_url = website_search_urls[website_name].format(search_content)
                        # 在浏览器中打开搜索结果页面
                        webbrowser.open_new(search_url)
                        successful_searches.append(f"{website_name}({search_content})")
                    except Exception as e:
                        failed_sites.append(f"{website_name}({search_content})(打开失败: {str(e)})")
            else:
                # 尝试模糊匹配（不区分大小写）
                matched_sites = [name for name in website_search_urls.keys()
                               if website_name.lower() in name.lower() or
                               name.lower() in website_name.lower()]

                if matched_sites:
                    site_name = matched_sites[0]
                    # 对每个搜索内容在该网站中搜索
                    for search_content in search_contents:
                        try:
                            search_url = website_search_urls[site_name].format(search_content)
                            webbrowser.open_new(search_url)
                            successful_searches.append(f"{site_name}({search_content})")
                        except Exception as e:
                            failed_sites.append(f"{site_name}({search_content})(打开失败: {str(e)})")
                else:
                    # 对于不支持的网站，为每个搜索内容添加失败记录
                    for search_content in search_contents:
                        failed_sites.append(f"{website_name}({search_content})(不支持的网站)")

        # 构造返回信息
        result_message = ""
        if successful_searches:
            result_message += f"已在以下网站中搜索相关内容：{', '.join(successful_searches)}，请查看浏览器结果。"
        if failed_sites:
            if successful_searches:
                result_message += f" 部分搜索失败：{', '.join(failed_sites)}。"
            else:
                result_message += f"搜索失败：{', '.join(failed_sites)}。"

        if not successful_searches and not failed_sites:
            result_message = "没有指定要搜索的网站或内容。"

        return result_message

    except Exception as e:
        return f"在网站中搜索时出错: {str(e)}"


# @mcp.tool()
# def open_webpage(content: str, scope: str = 'document', size: int = 5) -> str:
#     """
#     打开一些关于某些内容相关的文档、学术、图片、视频和博客等。

#     该函数通过调用 metaso 搜索引擎 API 来搜索指定内容，并根据指定范围打开相关链接。
#     支持搜索范围包括文档、学术、图片、视频和博客等，不支持网页搜索。

#     Args:
#         content (str): 搜索内容，要查找的关键词或短语
#         scope (str, optional): 搜索范围，决定搜索内容的类型。默认为 'document'。
#             支持的范围包括：
#             - 'document': 文档搜索（文库）
#             - 'scholar': 学术搜索
#             - 'image': 图片搜索
#             - 'video': 视频搜索
#             - 'podcast': 博客搜索
#         size (int, optional): 打开的网站数量，控制打开链接的数量。默认为 5，最大不超过 20。

#     Returns:
#         str: 操作结果描述，包含以下情况：
#             - 成功时返回已打开网页的标题和链接列表
#             - 未找到相关网页时返回提示信息
#             - 出现错误时返回错误描述

#     Example:
#         >>> open_webpage("人工智能发展", "document")
#         '已打开以下文档:
#         人工智能发展现状 - https://example.com/ai1
#         人工智能技术趋势 - https://example.com/ai2
#         AI发展报告 - https://example.com/ai3'
#         >>> open_webpage("人工智能发展", "scholar")
#         '已打开以下学术论文:
#         人工智能发展现状 - https://scholar.example.com/ai1
#         人工智能技术趋势 - https://scholar.example.com/ai2
#         AI发展报告 - https://scholar.example.com/ai3'
#     """
#     realtime_tts_speak("好的，马上打开", rate=25000)
#     try:
#         conn = http.client.HTTPSConnection("metaso.cn")
#         if scope == 'webpage':
#             payload = json.dumps({"q": content, "scope": scope, "includeSummary": True, "size": str(size),
#                                   "includeRawContent": False, "conciseSnippet": False})
#         else:
#             payload = json.dumps({"q": content, "scope": scope, "includeSummary": True, "size": str(size),
#                                   "conciseSnippet": False})
#         headers = {
#             'Authorization': 'Bearer ' + os.getenv("METASO_API_KEY"),
#             'Accept': 'application/json',
#             'Content-Type': 'application/json'
#         }
#         conn.request("POST", "/api/v1/search", payload, headers)
#         res = conn.getresponse()
#         data = res.read()
#         # 解析JSON响应
#         json_data = json.loads(data.decode("utf-8"))
#         # 提取webpages中的title和link
#         titles_and_links = []
#         i_scope = scope + "s"
#         if i_scope in json_data and isinstance(json_data[i_scope], list):
#             for webpage in json_data[i_scope]:
#                 if 'title' in webpage and 'link' in webpage:
#                     titles_and_links.append({
#                         'title': webpage['title'],
#                         'link': webpage['link']
#                     })
#                 elif 'title' in webpage and 'imageUrl' in webpage:
#                     titles_and_links.append({
#                         'title': webpage['title'],
#                         'link': webpage['imageUrl']
#                     })

#         # 打开网页链接
#         opened_links = []
#         for i, item in enumerate(titles_and_links):
#             if i < min(size, 20):  # 限制打开链接数量，不超过size和20的最小值
#                 webbrowser.open_new(item['link'])
#                 opened_links.append(f"{item['title']}: {item['link']}")
#         if opened_links:
#             return f"已打开以下网页:\n" + "\n".join(opened_links)
#         else:
#             return "未找到相关网页"

#     except Exception as e:
#         return f"打开网页时出错: {str(e)}"

@mcp.tool()
def open_urls(urls: list) -> str:
    """
    打开指定的网址URL列表，支持同时打开多个网址。
    该函数可以根据用户提供的要求和AI搜索到的相关信息，打开一些相关的网址。
    
    该函数会使用系统默认浏览器依次打开用户提供的网址链接列表。
    
    Args:
        urls (list): 要打开的网址URL列表，每个URL需要包含完整的协议头（如http://或https://）
        
    Returns:
        str: 操作结果描述，包括：
            - 成功打开网址时返回确认信息和成功打开的网址列表
            - 部分URL格式错误时返回错误信息和正确的网址列表
            - 出现异常时返回错误描述
            
    Example:
        >>> open_urls(["https://www.baidu.com", "https://github.com"])
        '已成功打开以下网址: https://www.baidu.com, https://github.com'
        
        >>> open_urls(["https://www.baidu.com", "www.github.com"])
        '已成功打开以下网址: https://www.baidu.com。以下网址格式错误: www.github.com'
        
        >>> open_urls(["www.baidu.com", "www.github.com"])
        '所有网址格式都错误，请确保包含协议头（如http://或https://）'
    """
    try:
        # 检查输入是否为列表
        if not isinstance(urls, list):
            return "参数错误：urls 必须是一个网址列表"
        
        # 分别存储有效的和无效的URL
        valid_urls = []
        invalid_urls = []
        
        # 检查每个URL的格式
        for url in urls:
            if url.startswith("http://") or url.startswith("https://"):
                valid_urls.append(url)
            else:
                invalid_urls.append(url)
        
        # 打开有效的URL
        opened_urls = []
        for url in valid_urls:
            try:
                webbrowser.open_new(url)
                opened_urls.append(url)
            except Exception as e:
                invalid_urls.append(f"{url}(打开失败: {str(e)})")
        
        # 构造返回信息
        result_message = ""
        if opened_urls:
            result_message += f"已成功打开以下网址: {', '.join(opened_urls)}。"
        if invalid_urls:
            if opened_urls:
                result_message += f" 以下网址格式错误或打开失败: {', '.join(invalid_urls)}。"
            else:
                result_message += f"所有网址格式都错误或打开失败: {', '.join(invalid_urls)}。"
        
        if not opened_urls and not invalid_urls:
            result_message = "没有指定要打开的网址。"
        
        print("---------"+result_message)
            
        return result_message
    except Exception as e:
        return f"打开网址时出错: {str(e)}"

@mcp.tool()
def open_popular_websites(website_names: list) -> str:
    """
    打开常用网站网页，支持同时打开多个流行网站

    该函数可以打开用户指定的常用网站列表，包括社交媒体、购物、视频、新闻、开发等各类网站。
    如果未找到对应网站，会尝试通过搜索引擎查找相关内容。

    Args:
        website_names (list): 网站名称或关键词列表，支持以下常用网站：
            社交媒体类: 微博、微信、QQ、Facebook、Twitter、Instagram、LinkedIn
            视频娱乐类: 哔哩哔哩、抖音、快手、YouTube、爱奇艺、腾讯视频、优酷
            购物类: 淘宝、天猫、京东、拼多多、亚马逊、 eBay
            新闻资讯类: 新浪新闻、腾讯新闻、网易新闻、今日头条、知乎、澎湃新闻
            搜索引擎类: 必应、百度、搜狗
            开发技术类: GitHub、CSDN、博客园、StackOverflow、掘金
            学习教育类: 学习通、智慧树、中国大学MOOC、网易云课堂
            办公工具类: 腾讯文档、石墨文档、阿里云盘、百度网盘
            邮箱类: QQ邮箱、网易邮箱、Gmail、Outlook
            其他: 小红书、美团、携程、58同城
            还可以有一些官网，比如北京大学官网

    Returns:
        str: 操作结果描述，包括：
            - 成功打开网站时返回确认信息
            - 未找到对应网站时返回提示信息
            - 出现错误时返回错误描述

    Example:
        >>> open_popular_websites(["哔哩哔哩", "GitHub"])
        '已成功打开以下网站: 哔哩哔哩, GitHub'

        >>> open_popular_websites(["未知网站", "知乎"])
        '已成功打开以下网站: 知乎。未找到以下网站，已通过搜索引擎查找: 未知网站'
    """
    # 常用网站URL映射字典
    websites = {
        # 社交媒体类
        '微博': 'https://weibo.com',
        '微信': 'https://wx.qq.com',
        'qq': 'https://qzone.qq.com',
        'facebook': 'https://www.facebook.com',
        'twitter': 'https://twitter.com',
        'instagram': 'https://www.instagram.com',
        'linkedin': 'https://www.linkedin.com',

        # 视频娱乐类
        '哔哩哔哩': 'https://www.bilibili.com',
        '抖音': 'https://www.douyin.com',
        '快手': 'https://www.kuaishou.com',
        'youtube': 'https://www.youtube.com',
        '爱奇艺': 'https://www.iqiyi.com',
        '腾讯视频': 'https://v.qq.com',
        '优酷': 'https://www.youku.com',

        # 购物类
        '淘宝': 'https://www.taobao.com',
        '天猫': 'https://www.tmall.com',
        '京东': 'https://www.jd.com',
        '拼多多': 'https://www.pinduoduo.com',
        '亚马逊': 'https://www.amazon.com',
        'eBay': 'https://www.ebay.com',

        # 新闻资讯类
        '新浪新闻': 'https://news.sina.com.cn',
        '腾讯新闻': 'https://news.qq.com',
        '网易新闻': 'https://news.163.com',
        '今日头条': 'https://www.toutiao.com',
        '知乎': 'https://www.zhihu.com',
        '澎湃新闻': 'https://www.thepaper.cn',

        # 搜索引擎类
        '百度': 'https://www.baidu.com',
        '谷歌': 'https://www.google.com',
        '必应': 'https://www.bing.com',
        '搜狗': 'https://www.sogou.com',

        # 开发技术类
        'github': 'https://github.com',
        'csdn': 'https://www.csdn.net',
        '博客园': 'https://www.cnblogs.com',
        'stackoverflow': 'https://stackoverflow.com',
        '掘金': 'https://juejin.cn',

        # 学习教育类
        '学习通': 'https://i.chaoxing.com',
        '智慧树': 'https://www.zhihuishu.com',
        '中国大学mooc': 'https://www.icourse163.org',
        '网易云课堂': 'https://study.163.com',

        # 办公工具类
        '腾讯文档': 'https://docs.qq.com',
        '石墨文档': 'https://shimo.im',
        '阿里云盘': 'https://www.aliyundrive.com',
        '百度网盘': 'https://pan.baidu.com',

        # 邮箱类
        'qq邮箱': 'https://mail.qq.com',
        '网易邮箱': 'https://mail.163.com',
        'gmail': 'https://mail.google.com',
        'outlook': 'https://outlook.live.com',

        # 其他
        '小红书': 'https://www.xiaohongshu.com',
        '美团': 'https://www.meituan.com',
        '携程': 'https://www.ctrip.com',
        '58同城': 'https://www.58.com'
    }

    # 确保输入是列表格式
    if not isinstance(website_names, list):
        return "参数错误：website_names 必须是一个网站名称列表"

    # 分别存储成功和失败的网站
    successful_sites = []
    failed_sites = []

    try:
        # 遍历所有请求的网站
        for website_name in website_names:
            # 尝试直接匹配网站
            if website_name in websites:
                url = websites[website_name]
                webbrowser.open_new(url)
                successful_sites.append(website_name)
            else:
                # 尝试模糊匹配（不区分大小写）
                matched_sites = [name for name in websites.keys()
                               if website_name.lower() in name.lower() or
                               name.lower() in website_name.lower()]

                if matched_sites:
                    site_name = matched_sites[0]
                    url = websites[site_name]
                    webbrowser.open_new(url)
                    successful_sites.append(site_name)
                else:
                    # 未找到对应网站，通过搜索引擎搜索
                    search_url = f"https://www.bing.com/search?q={website_name}"
                    #search_url = f"https://www.baidu.com/s?wd={website_name}"
                    webbrowser.open_new(search_url)
                    failed_sites.append(website_name)

        # 构造返回信息
        result_message = ""
        if successful_sites:
            result_message += f"已成功打开以下网站: {', '.join(successful_sites)}。"
            #print(result_message+"----------------")
        if failed_sites:
            if successful_sites:
                result_message += f" 未找到以下网站，已通过搜索引擎查找: {', '.join(failed_sites)}并已经打开。"
            else:
                result_message += f"未找到以下网站，已通过搜索引擎查找: {', '.join(failed_sites)}并已经打开。"
            #print(result_message+"----------------")

        if not successful_sites and not failed_sites:
            result_message = "没有指定要打开的网站。"

        return result_message

    except Exception as e:
        return f"打开网站时出错: {str(e)}"

@mcp.tool()
def read_and_summary_webpage() -> str:
    """
    总结当前网页内容（除PPT），收到读取网页内容或总结网页内容的指令就执行该命令，不管是否有已打开的网页

    :return: 网页内容摘要
    """
    realtime_tts_speak("好的，马上。", rate=25000)
    try:
        summary = read_webpage()
        return_content = get_file_summary(summary)
        # 将return_content写到剪切板
        pyperclip.copy(return_content)
        write_and_open_txt(return_content, file_path="file_summary\\summary.txt")
        return f"已生成总结，文件已保存到：file_summary\\summary.txt 并打开，请查看。"
    except Exception as e:
        return f"读取网页内容时出错: {str(e)}"

# @mcp.tool()
# def identify_image_and_get_response(user_content: str) -> str:
#     """
#     识别图像，识别图片，讲解图片，并根据用户问题返回响应

#     :param user_content: 用户关于图像的问题
#     :return: 图像识别结果和问题回答
#     """
#     try:
#         realtime_tts_speak("正在识别图片", rate=28000)
#         return get_image_response(user_content)
#     except Exception as e:
#         return f"识别图像时出错: {str(e)}"

@mcp.tool()
def identify_current_screen_save_img_and_get_response(user_content: str) -> str:
    """
    识别当前屏幕内容，然后返回识别结果

    :param user_content: 用户关于屏幕内容的问题
    :return: 屏幕识别结果
    """
    try:
        realtime_tts_speak("正在识别屏幕", rate=28000)
        # 截取当前屏幕并保存为图片
        capture_screen_opencv_only("imgs/screen_opencv.png")
        # 使用图像识别功能分析屏幕内容
        return get_image_response(user_content, "imgs/screen_opencv.png")
    except Exception as e:
        return f"识别当前屏幕时出错: {str(e)}"


# @mcp.tool()
# def create_and_open_word() -> str:
#     """
#     创建并打开Word文档，创建并打开一个Word文档，并返回文件路径。

#     :param file_name: 文档的文件名，如果不指定则使用默认的文件名
#     :return: 创建并打开的Word文档的路径
#     """
#     try:
#         return_content = create_and_open_word_doc()
#         time.sleep(0.5)
#         return return_content
#     except Exception as e:
#         return f"创建Word文档时出错: {str(e)}"


@mcp.tool()
def write_code_and_reports(user_content: str) -> str:
    """
    写代码。
    :param user_content:
    :return:
    """
    try:
        realtime_tts_speak("好的，正在写代码", rate=27000)
        return_content = ai_write_code_and_open_txt(user_content)
        return f"已生成代码，文件已保存到：file_summary\\code.txt 并打开，请查看。"
    except Exception as e:
        return f"写文章时出错: {str(e)}"

@mcp.tool()
def explain_code(user_content: str, code_content: str = None) -> str:
    """
    获取当前代码内容并讲解，解释代码，讲解代码。

    该函数可以通过两种方式获取代码内容：
    1. 直接传入code_content参数
    2. 参数为空时自动全选并复制当前活动窗口中的代码内容
    然后使用AI模型对代码进行解释，并将解释结果保存到文件中。

    Args:
        user_content (str): 用户对代码的特定问题或要求
        code_content (str, optional): 代码内容，如果提供则直接使用，否则从当前活动窗口获取。默认为None。

    Returns:
        str: 代码解释内容

    Example:
        >>> explain_code("请解释这段代码的作用")
        '这是代码的解释内容...'
        
        >>> explain_code("请分析这个函数", "def hello(): print('Hello World')")
        '这是代码的解释内容...'
    """
    try:
        # 短暂延迟确保焦点稳定
        time.sleep(0.1)
        realtime_tts_speak("好的，马上讲解代码。", rate=27000)
        
        # 如果没有提供代码内容，则从当前活动窗口获取
        if not code_content:
            # 执行 ctrl+a 全选
            pyautogui.hotkey('ctrl', 'a')
            # 执行 Ctrl+c 复制到剪切板
            pyautogui.hotkey('ctrl', 'c')
            code_content = pyperclip.paste()
        
        return_content = code_ai_explain_model(code_content + "\n" + user_content)
        write_and_open_txt(return_content, file_path="file_summary\\explain.txt")
        return f"已生成代码解释，文件已保存到：file_summary\\explain.txt 并打开，请查看。"
    except Exception as e:
        return f"读取代码失败: {str(e)}"

# @mcp.tool()
# def explain_file_content(user_content: str) -> str:
#     """
#     总结当前文本内容（除PPT），提取文本中的内容（除PPT），讲解文本内容，解释当前文件内容，分析当前文本内容，整理文本内容。

#     该函数会自动全选并复制当前活动窗口中的文本内容，
#     然后生成内容摘要，并将摘要结果保存到文件中。

#     :param user_content: 用户对文件内容的特定需求或问题
#     :return: 文件内容摘要
#     """
#     try:
#         # 短暂延迟确保焦点稳定
#         time.sleep(0.1)
#         realtime_tts_speak("好的，马上讲解。", rate=27000)
#         # 执行 ctrl+a 全选
#         pyautogui.hotkey('ctrl', 'a')
#         # 执行 Ctrl+c 复制到剪切板
#         pyautogui.hotkey('ctrl', 'c')
#         file_content = pyperclip.paste()
#         return_content = get_file_summary(file_content+"/n"+user_content)
#         # 将return_content写到剪切板
#         pyperclip.copy(return_content)
#         write_and_open_txt(return_content, file_path="file_summary\\summary.txt")
#         return return_content
#     except Exception as e:
#         return f"读取文件失败: {str(e)}"

@mcp.tool()
def get_text_content(return_content: bool = False) -> str:
    """
    获取当前文本内容（除PPT），获取当前文本内容，获取当前文本内容。

    该函数会自动全选并复制当前活动窗口中的文本内容，
    然后返回文本内容。

    Args:
        return_content (bool, optional): 是否返回文本内容。默认为False。
        
    Returns:
        str: 根据return_content参数决定返回内容：
            - False: 只返回保存文件的路径信息
            - True: 返回保存文件的路径信息和文本内容

    Returns:
        str: 根据return_content参数决定返回内容：
            - return_content为False时：文件保存路径信息
            - return_content为True时：文件保存路径信息和文本内容

    Example:
        >>> get_text_content()
        '获取的文本已保存到C:\\\\projects\\\\file_summary\\\\tempt.txt文件中。'
        
        >>> get_text_content(return_content=True)
        '获取的文本已保存到C:\\\\projects\\\\file_summary\\\\tempt.txt文件中，文件内容为：这是文档的内容...'
        
        >>> get_text_content(return_content=False)
        '读取文本内容失败: 具体错误信息'
    """
    try:
        # 短暂延迟确保焦点稳定
        time.sleep(0.1)
        # 执行 ctrl+a 全选
        pyautogui.hotkey('ctrl', 'a')
        # 执行 Ctrl+c 复制到剪切板
        pyautogui.hotkey('ctrl', 'c')
        text_content = pyperclip.paste()
        print(f"获取文本内容成功")
        txt_file_path = "file_summary\\tempt.txt"
        # txt_file_path绝对路径
        txt_file_path = os.path.abspath(txt_file_path)
        # 保存文本内容
        with open(txt_file_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"保存文本内容到{txt_file_path}文件中")
        
        # 根据return_content参数决定返回内容
        if return_content:
            print("返回文本内容")
            return f"获取的文本已保存到{txt_file_path}文件中，文件内容为：{text_content}"
        else:
            return f"获取的文本已保存到{txt_file_path}文件中。"
    except Exception as e:
        return f"读取文本内容失败: {str(e)}"

@mcp.tool()
def explain_file_content(text_content: str, user_content: str) -> str:
    """
    负责文件内容，使用文本模型生成内容摘要，总结内容，提取内容重点信息，讲解文本内容，分析文本内容等操作。
    可以传入文本内容，也可以传入文本路径。
    文本内容的来源一般是：1.用户直接提供，2.从读取剪切板函数中获取，3.从前面的获取文本内容函数获取，4.从上下文获取。

    Args:
        text_content (str): 需要处理的文本内容或路径，路径可以是相对路径或绝对路径，文件内容可以来自用户直接提供、剪切板、文件读取等途径
        user_content (str): 用户对文本内容的具体要求或问题，如总结、提取要点、分析等指令

    Returns:
        str: 文本处理结果，包括摘要、要点或分析内容，并将结果保存到文件和剪切板中

    Example:
        >>> explain_file_content("这是一段需要总结的文本内容...", "请总结这段文本的主要内容")
        '已生成文本摘要，文件已保存并打开。'

        >>> explain_file_content("技术文档内容...", "提取该文档中的关键要点")
        '已提取关键要点，文件已保存并打开。'

        >>> explain_file_content("file_summary\\tempt.txt", "请分析这段文本的内容")
        '已生成文本分析，文件已保存并打开。'
    """
    try:
        # 短暂延迟确保焦点稳定
        time.sleep(0.1)
        realtime_tts_speak("马上讲解。", rate=27000)
        # 检查text_content是否是文件路径
        if os.path.isfile(text_content):
            # 是文件路径，读取文件内容
            # 判断是否为txt文件
            if text_content.endswith('.txt'):
                with open(text_content, 'r', encoding='utf-8') as file:
                    text_content = file.read()
            else:
                return f"请提供正确的txt文件路径。"
        # 将文本内容传给大模型
        return_content = get_file_summary(text_content+"/n"+user_content)
        # 将return_content写到剪切板
        pyperclip.copy(return_content)
        write_and_open_txt(return_content, file_path="file_summary\\summary.txt")
        return f"已生成文本摘要，文件路径为：file_summary\\summary.txt 已保存并打开。"
    except Exception as e:
        return f"总结文件内容失败: {str(e)}"

@mcp.tool()
def write_articles_and_reports(user_content: str, ai_content: str = '') -> str:
    """
    写文章，写报告，写论文，写说明，写文本。如果之前有进行过搜索或获取文本内容操作，要结合搜索或获取文本内的内容写文稿。

    该函数可以根据用户提供的内容要求和AI搜索或从文本中获取到的相关信息，自动生成相应的文章、报告、论文或其他文本内容，并将生成的内容保存到文件中并打开供用户查看。

    Args:
        user_content (str): 用户对文章内容的具体要求，包括主题、格式、长度等要求。
            可以包含以下信息：
            - 文章主题和内容要点
            - 文章类型（如报告、论文、说明文档等）
            - 特殊格式要求
            - 字数要求
        ai_content (str, optional): AI搜索或从文本中获取到的相关信息，用于丰富文章内容。
            默认为空字符串，当有搜索结果时会自动将搜索内容整合到文章中。

    Returns:
        str: 操作结果描述，包括：
            - 成功时返回生成的文章内容
            - 出现错误时返回错误描述

    Example:
        >>> write_articles_and_reports("写一篇关于人工智能发展现状的报告，1000字左右")
        '已生成关于人工智能发展现状的报告，文件已保存并打开。'

        >>> write_articles_and_reports("帮我写一个项目总结", "项目背景：数字化转型项目；实施过程：分三个阶段...")
        '已生成项目总结文档，文件已保存并打开。'
    """
    try:
        realtime_tts_speak("好的，正在写", rate=27000)
        if ai_content != '':
            user_content = user_content + "搜索到的相关信息有： " + ai_content
        return_content = ai_write_and_open_txt(user_content)
        return f"已生成文章，文件已保存到：.file_summary\\write.md 并打开，请查看。"
    except Exception as e:
        return f"写文章时出错: {str(e)}"

@mcp.tool()
def control_iflow_agent(user_content: str):
    """
    直接调用agent解决用户问题。直接调用心流AI解决用户问题。当调用该工具时，无需继续调用其他工具。

    :param user_content: 用户对iflow_agent的指令
    :return: iflow_agent的响应
    """
    realtime_tts_speak("好的，请耐心等待。", rate=27000)
    use_iflow_in_cmd(user_content)
    return "agent解决问题完成。"

@mcp.tool()
def markdown_to_word_server(markdown_content: str = None, md_file_path: str = None) -> str:
    """
    将当前文档转为word，将文本内容或.md文件转换为Word文档，支持三种模式：
    1. 传入markdown_content参数：直接转换传入的文本
    2. 传入md_file_path参数：读取指定的.md文件并转换，在md_file_path中可传入.md文件路径和.txt文件路径。
    3. 无参数：全选并复制当前活动窗口内容，读取剪切板中的Markdown内容进行转换

    Args:
        markdown_content (str, optional): Markdown格式的文本内容，直接用于转换
        md_file_path (str, optional): .md文件的路径，读取文件内容进行转换

    Returns:
        str: 操作结果描述，包括生成的文件路径或错误信息

    Example:
        >>> markdown_to_word_server(markdown_content="# 标题\\n内容")
        '已生成Word文档，文件路径为：D:\\\\documents\\\\new.docx'

        >>> markdown_to_word_server(md_file_path="README.md")
        '已生成Word文档，文件路径为：D:\\\\documents\\\\new_1.docx'

        >>> markdown_to_word_server(md_file_path="README.txt")
        '已生成Word文档，文件路径为：D:\\\\documents\\\\new_2.docx'

        >>> markdown_to_word_server()
        '已生成Word文档，文件路径为：D:\\\\documents\\\\new_3.docx'
    """
    try:
        realtime_tts_speak("马上生成word。", rate=27000)
        
        # 根据不同参数情况获取Markdown内容
        if markdown_content:
            # 使用传入的Markdown文本内容
            final_markdown_text = markdown_content
        elif md_file_path:
            # 读取指定的.md文件
            if not os.path.exists(md_file_path):
                return f"指定的文件不存在: {md_file_path}"
            # 判断是否为.md文件或.txt文件
            file_extension = os.path.splitext(md_file_path)[1].lower()
            if file_extension == '.md':
                with open(md_file_path, "r", encoding="utf-8") as f:
                    final_markdown_text = f.read()
            elif file_extension == '.txt':
                with open(md_file_path, "r", encoding="utf-8") as f:
                    final_markdown_text = f.read()
            else:
                return f"不支持的文件类型: {md_file_path}"
        else:
            # 无参数时，全选并复制当前活动窗口内容到剪切板
            # 短暂延迟确保焦点稳定
            time.sleep(0.1)
            # 执行 ctrl+a 全选
            pyautogui.hotkey('ctrl', 'a')
            # 执行 Ctrl+c 复制到剪切板
            pyautogui.hotkey('ctrl', 'c')
            final_markdown_text = pyperclip.paste()
        
        # 将Markdown内容写入临时文件
        with open("file_summary\\markdown.md", "w", encoding="utf-8") as f:
            f.write(final_markdown_text)

        output_path = create_file_path()
        md_to_word(output_path)
        open_word_doc(output_path)
        return_output = "已生成Word文档，文件路径为：" + output_path
        return return_output
    except Exception as e:
        return f"转换Markdown到Word时出错: {str(e)}"

@mcp.tool()
def markdown_to_excel_server(markdown_text: str = None) -> str:
    """
    将文本转换为Excel文件，支持两种模式：
    1. 传入markdown_text参数：直接转换传入的文本或者.md文件路径或.txt文件路径
    2. 无参数：全选并复制当前活动窗口内容，读取剪切板中的文本进行转换

    Args:
        markdown_text (str, optional): 包含表格数据的文本或者.md文件路径或.txt文件路径，如果不提供则自动从当前活动窗口获取。

    Returns:
        str: 操作结果描述，包括生成的文件路径或错误信息

    Example:
        >>> markdown_to_excel_server("| 姓名 | 年龄 |\\n| --- | --- |\\n| 张三 | 25 |")
        '已生成Excel文件，文件路径为：D:\\\\documents\\\\output.xlsx'

        >>> markdown_to_excel_server("D:\\\\documents\\\\input.md")
        '已生成Excel文件，文件路径为：D:\\\\documents\\\\output.xlsx'

        >>> markdown_to_excel_server("D:\\\\documents\\\\input.txt")
        '已生成Excel文件，文件路径为：D:\\\\documents\\\\output.xlsx'

        >>> markdown_to_excel_server()
        '已生成Excel文件，文件路径为：D:\\\\documents\\\\output_1.xlsx'
    """
    try:
        realtime_tts_speak("马上生成excel。", rate=27000)
        
        # 如果没有传入markdown_text，则从当前活动窗口获取
        if markdown_text is None:
            # 短暂延迟确保焦点稳定
            time.sleep(0.1)
            # 执行 ctrl+a 全选
            pyautogui.hotkey('ctrl', 'a')
            # 执行 Ctrl+c 复制到剪切板
            pyautogui.hotkey('ctrl', 'c')
            # 从剪切板读取内容
            markdown_text = pyperclip.paste()
        
        # 判断是否为文件路径
        if os.path.isfile(markdown_text):
            # 是文件路径，读取文件内容
            # 判断是否为.md文件或.txt文件
            file_extension = os.path.splitext(markdown_text)[1].lower()
            if file_extension == '.md':
                with open(markdown_text, "r", encoding="utf-8") as f:
                    markdown_text = f.read()
            elif file_extension == '.txt':
                with open(markdown_text, "r", encoding="utf-8") as f:
                    markdown_text = f.read()
            else:
                return f"不支持的文件类型: {markdown_text}"
        
        output_path = markdown_to_excel_main(markdown_text)
        #open_excel_file(output_path)  # 如果有这个函数的话
        return_output = "已生成Excel文件，文件路径为：" + output_path
        return return_output
    except Exception as e:
        return f"转换Markdown到Excel时出错: {str(e)}"

@mcp.tool()
def change_word_file(user_content: str) -> str:
    """
    将当前活动窗口的Word文档进行操作，如修改字体大小，段落间距，字体样式，导出PDF等。
    这个函数不能调用多次。

    该函数会自动获取当前活动的Word文档路径，并根据用户的具体需求对文档进行相应操作，
    包括格式调整、内容修改、导出等操作，并将修改后的文件保存并重新打开。

    Args:
        user_content (str): 用户对Word文档的具体操作要求，可以包括：
            - 字体大小、样式、颜色调整
            - 段落间距、对齐方式设置
            - 页面布局、页眉页脚修改
            - 导出为PDF或其他格式
            - 其他针对Word文档的特定操作要求

    Returns:
        str: 操作结果描述，包括：
            - 成功完成操作时返回确认信息
            - 当前不是Word文件时返回提示信息
            - 出现错误时返回错误描述

    Example:
        >>> change_word_file("将标题字体改为黑体，字号24，加粗")
        '操作完成。'

        >>> change_word_file("将文档导出为PDF格式")
        '操作完成。'
    """
    try:
        realtime_tts_speak("请耐心等待。", rate=27000)
        word_path = get_activate_path()
        # 如果当前文件路径为word文件路径，则进行操作
        if word_path.endswith(".docx") or word_path.endswith(".doc"):
            user_content = "文件路径为：" + word_path+"\n" + user_content+"\n" + "将修改后的文件存储下来并打开。"
            # 获取文件夹路径
            word_path_folder = os.path.dirname(word_path)
            use_iflow_in_cmd(user_content, word_path_folder)
            return "操作完成。"
        return "当前文件不是Word文件，请检查文件路径。"
    except Exception as e:
        return f"操作Word文档时出错: {str(e)}"


@mcp.tool()
def change_excel_file(user_content: str) -> str:
    """
    将当前活动窗口的Excel文件进行操作，对当前活动窗口的Excel文件进行数据分析，如修改单元格样式，求和，添加函数等。
    这个函数不能调用多次，只能调用一次。

    该函数会自动获取当前活动的Excel文件路径，并根据用户的具体需求对表格进行相应操作，
    包括数据处理、公式计算、样式调整等操作，并将修改后的文件保存并重新打开。

    Args:
        user_content (str): 用户对Excel文档的具体操作要求，可以包括：
            - 单元格样式、颜色、字体调整
            - 数据计算、求和、统计分析
            - 公式添加和修改
            - 图表创建和格式化
            - 其他针对Excel文档的特定操作要求

    Returns:
        str: 操作结果描述，包括：
            - 成功完成操作时返回确认信息
            - 当前不是Excel文件时返回提示信息
            - 出现错误时返回错误描述

    Example:
        >>> change_excel_file("对B列数据求和，并在最后一行显示结果")
        '操作完成。'

        >>> change_excel_file("将A1单元格背景色改为黄色，字体加粗")
        '操作完成。'
    """
    try:
        realtime_tts_speak("请耐心等待。", rate=27000)
        excel_path = get_activate_path()
        # 如果当前文件路径为Excel文件路径，则进行操作
        if excel_path.endswith(".xlsx") or excel_path.endswith(".xls"):
            user_content = "文件路径为：" + excel_path+"\n" + user_content+"\n" + "将修改后的文件存储下来并打开。"
            excel_path_folder = os.path.dirname(excel_path)
            print(excel_path_folder)
            use_iflow_in_cmd(user_content, excel_path_folder)
            return "操作完成。"
        return "当前文件不是Excel文件，请检查文件路径。"
    except Exception as e:
        return f"操作Excel文档时出错: {str(e)}"


# @mcp.tool()
# def change_ppt_file(user_content: str) -> str:
#     """
#     将当前活动窗口的PPT文件进行操作，如修改样式，修改背景等。
#     这个函数不能调用多次，只能调用一次。

#     该函数会自动获取当前活动的PowerPoint文件路径，并根据用户的具体需求对演示文稿进行相应操作，
#     包括幻灯片样式调整、背景修改、动画设置等操作，并将修改后的文件保存并重新打开。

#     Args:
#         user_content (str): 用户对PPT文档的具体操作要求，可以包括：
#             - 幻灯片背景、主题样式修改
#             - 文字字体、颜色、大小调整
#             - 动画效果添加和设置
#             - 幻灯片布局和设计调整
#             - 其他针对PPT文档的特定操作要求

#     Returns:
#         str: 操作结果描述，包括：
#             - 成功完成操作时返回确认信息
#             - 当前不是PPT文件时返回提示信息
#             - 出现错误时返回错误描述

#     Example:
#         >>> change_ppt_file("将所有幻灯片背景改为蓝色渐变")
#         '操作完成。'

#         >>> change_ppt_file("为标题添加飞入动画效果")
#         '操作完成。'
#     """
#     try:
#         realtime_tts_speak("请耐心等待。", rate=27000)
#         ppt_path = get_activate_path()
#         # 如果当前文件路径为PPT文件路径，则进行操作
#         if ppt_path.endswith(".pptx") or ppt_path.endswith(".ppt"):
#             user_content = "文件路径为：" + ppt_path+"\n" + user_content+"\n" + "将修改后的文件存储下来并打开。"
#             ppt_path_folder = os.path.dirname(ppt_path)
#             use_iflow_in_cmd(user_content, ppt_path_folder)
#             return "操作完成。"
#         return "当前文件不是PPT文件，请检查文件路径。"
#     except Exception as e:
#         return f"操作PPT文档时出错: {str(e)}"


@mcp.tool()
def read_ppt(user_content: str) -> str:
    """
    读取PPT内容并按用户要求进行操作，可以总结，提取摘要，提取要点，改写等等

    该函数会自动获取当前活动的PowerPoint文件路径，将PPT转换为文本格式，
    然后根据用户的具体需求对内容进行处理，包括总结、摘要、要点提取等操作。

    Args:
        user_content (str): 用户对PPT内容的具体操作要求，可以包括：
            - 内容总结和摘要提取
            - 关键要点整理
            - 内容改写和优化
            - 其他针对PPT内容的特定处理要求

    Returns:
        str: 操作结果描述，包括：
            - 成功完成操作时返回处理后的内容
            - 当前不是PPT文件时返回提示信息
            - 出现错误时返回错误描述

    Example:
        >>> read_ppt("请总结这个PPT的主要内容")
        '已生成PPT内容总结，文件已保存并打开。'

        >>> read_ppt("提取PPT中的关键要点")
        '已提取PPT关键要点，文件已保存并打开。'
    """
    try:
        realtime_tts_speak("正在读内容。", rate=27000)
        ppt_path = get_activate_path()
        # 如果当前文件路径为PPT文件路径，则进行操作
        if ppt_path.endswith(".pptx") or ppt_path.endswith(".ppt"):
            # 模拟按下键盘的Ctrl+S保存
            pyautogui.hotkey('ctrl', 's')
            result_txt_path = convert_document_to_txt(ppt_path)
            # 读取result_txt_path这个txt文件
            with open(result_txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 将ppt_path路径的ppt打开
            os.startfile(ppt_path)
            return_content = get_file_summary(content + "\n" + user_content)
            # 将return_content写到剪切板
            pyperclip.copy(return_content)
            write_and_open_txt(return_content, file_path="file_summary\\summary.txt")
            return f"已生成PPT内容总结，文件已保存到 file_summary\\summary.txt 并打开。"
        else:
            return "当前文件不是PPT文件，请检查文件路径。"
    except Exception as e:
        return f"读取PPT时出错: {str(e)}"


@mcp.tool()
def read_pdf(user_content: str) -> str:
    """
    读取PDF内容并按用户要求进行操作，可以总结、提取摘要、提取要点、改写等

    该函数会自动获取当前活动的PDF文件路径，将PDF转换为文本格式，
    然后根据用户的具体需求对内容进行处理，包括总结、摘要、要点提取等操作。

    Args:
        user_content (str): 用户对PDF内容的具体操作要求，可以包括：
            - 内容总结和摘要提取
            - 关键要点整理
            - 内容改写和优化
            - 其他针对PDF内容的特定处理要求

    Returns:
        str: 操作结果描述，包括：
            - 成功完成操作时返回处理后的内容
            - 当前不是PDF文件时返回提示信息
            - 出现错误时返回错误描述

    Example:
        >>> read_pdf("请总结这个PDF的主要内容")
        '已生成PDF内容总结，文件已保存并打开。'

        >>> read_pdf("提取PDF中的关键要点")
        '已提取PDF关键要点，文件已保存并打开。'
    """
    try:
        realtime_tts_speak("正在读内容。", rate=27000)
        app_name = get_activate_path()
        if app_name == "msedge.exe" or app_name == "chrome.exe" or app_name == "firefox.exe":
            pyautogui.hotkey('ctrl', 'l')
            pyautogui.hotkey('ctrl', 'c')
            # 读取剪切板
            current_url = pyperclip.paste()

            import urllib.parse
            # 1. 去掉 file:// 前缀
            path_without_scheme = current_url.replace("file://", "")

            # 2. URL 解码（关键步骤！）
            decoded_path = urllib.parse.unquote(path_without_scheme)

            # 3. （Windows 专用）去掉开头多余的 '/'
            if os.name == 'nt' and decoded_path.startswith('/'):
                decoded_path = decoded_path[1:]

            result_txt_path = convert_document_to_txt(decoded_path)
            # 读取result_txt_path这个txt文件
            with open(result_txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return_content = get_file_summary(content + "\n" + user_content)
            # 将return_content写到剪切板
            pyperclip.copy(return_content)
            write_and_open_txt(return_content, file_path="file_summary\\summary.txt")
            return f"已生成PDF内容总结，文件保存到 file_summary\\summary.txt 并打开。"
        else:
            return "当前不是PDF文件，请检查文件路径。"
    except Exception as e:
        return f"读取PDF时出错: {str(e)}"


@mcp.tool()
def control_web(user_content: str) -> str:
    """
    控制当前网页内容，对网页进行操作或处理

    该函数可以对当前活动的网页进行各种操作，如内容提取、格式转换、信息整理、文本爬取、图片爬取、视频爬取等功能。
    函数会自动获取当前网页的URL，并结合用户的具体需求进行相应处理。

    Args:
        user_content (str): 用户对网页的具体操作要求，可以包括：
            - 网页内容提取和整理
            - 网页信息分析和总结
            - 网页数据导出和格式转换
            - 其他针对网页的特定操作要求

    Returns:
        str: 操作结果描述，包括：
            - 成功完成操作时返回确认信息
            - 出现错误时返回错误描述

    Example:
        >>> control_web("提取网页中的关键信息并整理成报告")
        '操作完成。'

        >>> control_web("将网页内容转换为Markdown格式")
        '操作完成。'
    """
    try:
        realtime_tts_speak("请耐心等待。", rate=27000)
        web_url = extract_current_webpage_url()
        user_content = "网址为：" + web_url +"\n" + user_content+" 可以选择用python脚本实现"+"\n" + "将生成的文件存储到桌面上的一个文件夹中并打开该文件夹。"
        use_iflow_in_cmd(user_content)
        return "操作完成。"
    except Exception as e:
        return f"操作网页时出错: {str(e)}"

@mcp.tool()
def open_folder(folder_path: str) -> str:
    """
    打开文件资源管理器并进入指定的文件夹路径，进入指定文件夹。

    该函数会打开Windows文件资源管理器并导航到用户指定的文件夹路径。
    支持绝对路径和相对路径。

    Args:
        folder_path (str): 要打开的文件夹路径，可以是绝对路径或相对路径

    Returns:
        str: 操作结果描述，包括：
            - 成功打开文件夹时返回确认信息
            - 路径不存在时返回错误信息
            - 出现异常时返回错误描述

    Example:
        >>> open_folder("C:\\\\Users\\\\Documents")
        '已成功打开文件夹: C:\\\\Users\\\\Documents'

        >>> open_folder(".\\\\project")
        '已成功打开文件夹: .\\\\project'

        >>> open_folder("不存在的路径")
        '文件夹路径不存在: 不存在的路径'
    """
    try:
        # 检查文件夹路径是否存在
        if not os.path.exists(folder_path):
            print("文件夹路径不存在。")
            return f"文件夹路径不存在: {folder_path}"
        
        # 检查是否为目录
        if not os.path.isdir(folder_path):
            print("指定路径不是文件夹。")
            return f"指定路径不是文件夹: {folder_path}"
        
        # 打开文件资源管理器并进入指定文件夹
        os.startfile(folder_path)
        print("已打开文件资源管理器并进入指定文件夹。")
        return f"已成功打开文件夹: {folder_path}"
    except Exception as e:
        return f"打开文件夹时出错: {str(e)}"

@mcp.tool()
def open_app(app_names: list) -> str:
    """
    用命令打开软件 - MCP标准格式版本（支持批量打开）

    通过系统命令启动指定的应用程序。支持常用的办公和开发软件，
    包括 Microsoft Office 套件和开发工具等。可以同时打开多个应用程序。

    Args:
        app_names (list): 要打开的软件名称列表
            支持的软件包括：
            - excel: Microsoft Excel 电子表格软件
            - powerpnt: Microsoft PowerPoint 演示文稿软件
            - word: Microsoft Word 文字处理软件
            - notepad: 记事本
            - calculator: 计算器
            - cmd: 命令提示符
            - powershell: PowerShell 终端
            - msedge: Edge浏览器，默认浏览器，浏览器
            - mspaint: 绘图工具

    Returns:
        str: 包含执行结果的描述信息，包括成功和失败的应用程序详情

    Example:
        >>> open_app(["excel", "word"])
        '已成功启动以下应用程序: excel, word。'

        >>> open_app(["unknown_app", "excel"])
        '部分应用程序启动失败: unknown_app(不支持的应用: 'unknown_app')。成功启动: excel。'
    """
    # 支持的应用程序映射字典
    supported_apps = {
        'excel': 'excel',
        'powerpnt': 'powerpnt',
        'powerpoint': 'powerpnt',
        'pycharm': 'pycharm',
        'word': 'winword',
        'notepad': 'notepad',
        'calculator': 'calc',
        'cmd': 'cmd',
        'powershell': 'powershell',
        'msedge': 'msedge',
        'mspaint': 'mspaint',
        'chrome': 'chrome',
        'firefox': 'firefox',
    }

    # 确保输入是列表格式
    if not isinstance(app_names, list):
        return "参数错误：app_names 必须是一个应用程序名称列表"

    # 分别存储成功和失败的应用程序
    successful_apps = []
    failed_apps = []

    # 遍历所有请求的应用程序
    for app_name in app_names:
        # 检查请求的应用是否受支持
        if app_name.lower() not in supported_apps:
            failed_apps.append(f"{app_name}(不支持的应用)")
            continue

        try:
            # 获取实际的应用程序命令
            app_command = supported_apps[app_name.lower()]
            # 使用 subprocess 启动应用程序
            subprocess.run(["start", app_command], shell=True, check=True)
            # 记录成功启动的应用
            successful_apps.append(app_name)
        except subprocess.CalledProcessError as e:
            failed_apps.append(f"{app_name}(启动失败: {str(e)})")
        except Exception as e:
            failed_apps.append(f"{app_name}(未知错误: {str(e)})")

    # 等待所有应用程序启动
    if successful_apps:
        time.sleep(len(successful_apps) * 0.5)  # 根据启动应用数量调整等待时间

    # 构造返回信息
    result_message = ""
    if successful_apps:
        result_message += f"已成功启动以下应用程序: {', '.join(successful_apps)}。"
    if failed_apps:
        if successful_apps:
            result_message += f" 部分应用程序启动失败: {', '.join(failed_apps)}。"
        else:
            result_message += f"应用程序启动失败: {', '.join(failed_apps)}。"

    if not successful_apps and not failed_apps:
        result_message = "没有指定要启动的应用程序。"

    return result_message


@mcp.tool()
def open_netease_music_server() -> str:
    """
    打开网易云音乐

    :return: 操作结果描述
    """
    try:
        app_name = "网易云音乐"
        # 按下Win键打开开始菜单
        pyautogui.press('win')
        # 等待开始菜单打开
        time.sleep(0.5)
        # 将软件名复制到剪贴板
        pyperclip.copy(app_name)
        # 粘贴软件名（使用Ctrl+V）
        pyautogui.hotkey('ctrl', 'v')
        # 等待软件名粘贴完成
        time.sleep(0.5)
        # 按回车键启动软件
        pyautogui.press('enter')
        time.sleep(1)
        return "操作完成。"
    except Exception as e:
        return f"打开网易云音乐时出错: {str(e)}"

@mcp.tool()
def control_netease(actions: list) -> str:
    """
    控制网易云音乐客户端的播放行为（支持批量操作）
    通过模拟键盘快捷键实现控制

    :param actions: 要执行的操作名称列表，支持以下值：
        'play_pause'     → 播放/暂停
        'next_song'      → 下一首
        'previous_song'  → 上一首
        'volume_up'      → 音量增大
        'volume_down'    → 音量减小
        'mini_mode'      → 切换迷你模式
        'like_song'      → 喜欢当前歌曲
        'lyrics_toggle'  → 显示/隐藏歌词
    :return: 操作执行结果描述
    """
    # 根据动作名称，映射到对应的全局快捷键组合
    action_map = {
        'play_pause': ('ctrl', 'alt', 'p'),          # 播放/暂停
        'next_song': ('ctrl', 'alt', 'right'),         # 下一首
        'previous_song': ('ctrl', 'alt', 'left'),      # 上一首
        'volume_up': ('ctrl', 'alt', 'up'),            # 音量增加
        'volume_down': ('ctrl', 'alt', 'down'),        # 音量减少
        'mini_mode': ('ctrl', 'alt', 'o'),           # 迷你模式（网易云默认）
        'like_song': ('ctrl', 'alt', 'l'),           # 喜欢当前歌曲
        'lyrics_toggle': ('ctrl', 'alt', 'd'),         # 歌词开关
    }
    # 分别存储成功和失败的操作
    successful_actions = []
    failed_actions = []
    # 遍历所有请求的操作
    for action in actions:
        # 检查动作是否支持
        if action not in action_map:
            failed_actions.append(f"{action}(不支持的操作)")
            continue
        try:
            # 获取对应快捷键
            keys = action_map[action]
            # 模拟按下快捷键
            pyautogui.hotkey(*keys)  # *keys 自动解包元组，如 ('ctrl', 'shift', 'p') → ctrl + shift + p

            # 对于音量调节操作，执行两次以获得更明显的效果
            if action == 'volume_up' or action == 'volume_down':
                pyautogui.hotkey(*keys)
            successful_actions.append(action)
        except Exception as e:
            failed_actions.append(f"{action}(执行时出错: {str(e)})")
    # 等待所有操作执行完成
    if successful_actions:
        time.sleep(len(successful_actions) * 0.1)
    # 构造返回信息
    result_message = ""
    if successful_actions:
        result_message += f"已成功执行以下操作: {', '.join(successful_actions)}。"
    if failed_actions:
        if successful_actions:
            result_message += f" 部分操作执行失败: {', '.join(failed_actions)}。"
        else:
            result_message += f"操作执行失败: {', '.join(failed_actions)}。"
    if not successful_actions and not failed_actions:
        result_message = "没有指定要执行的操作。"
    return result_message


# 在文件顶部添加全局变量定义
gesture_process = None

@mcp.tool()
def gesture_control() -> str:
    """
    执行手势控制，启动手势控制，启动手势识别
    :return: 操作执行结果描述
    """
    global gesture_process
    try:
        realtime_tts_speak("稍等。", rate=25000)
        # 启动手势控制gesture.exe
        current_file = os.path.dirname(os.path.abspath(__file__))
        gesture_path = os.path.join(current_file, "gesture.exe")
        if os.path.exists(gesture_path):
            # 使用start命令在新窗口中运行程序
            cmd_command = f'start cmd /k "cd /d {current_file} && {"gesture.exe"}"'
            subprocess.Popen(cmd_command, shell=True)
        else:
            return "手势控制文件不存在。"
        return "已成功启动手势控制进程。"
    except Exception as e:
        return f"执行手势操作时出错: {str(e)}"


@mcp.tool()
def stop_gesture_control() -> str:
    """
    关闭手势识别，停止手势控制进程

    该函数用于终止之前启动的手势控制进程，释放相关资源。

    Returns:
        str: 操作结果描述，包括：
            - 成功关闭进程时返回确认信息
            - 没有运行中的进程时返回提示信息
            - 出现错误时返回错误描述

    Example:
        >>> stop_gesture_control()
        '已成功关闭手势控制进程。'
    """
    try:
        # 查找并终止gesture.exe进程
        subprocess.run(["taskkill", "/f", "/im", "gesture.exe"],
                      capture_output=True, text=True, shell=True)
        return "已成功关闭手势控制进程。"
    except Exception as e:
        return f"关闭手势控制进程时出错: {str(e)}"


@mcp.tool()
def get_clipboard_content() -> str:
    """
    获取剪切板中的内容并返回

    该函数可以读取系统剪切板中的文本内容，并将其返回给用户。
    支持获取用户复制或剪切的文本内容，方便后续处理或查看。

    Returns:
        str: 剪切板中的文本内容，如果剪切板为空或出现错误则返回相应提示信息

    Example:
        >>> get_clipboard_content()
        '这是剪切板中的文本内容'

        >>> get_clipboard_content()
        '剪切板中没有文本内容'
    """
    try:
        # 从剪切板获取内容
        clipboard_content = pyperclip.paste()

        # 检查剪切板是否为空
        if clipboard_content:
            return clipboard_content
        else:
            return "剪切板中没有文本内容"
    except Exception as e:
        return f"获取剪切板内容时出错: {str(e)}"


@mcp.tool()
def windows_shortcut(actions: list) -> str:
    """
    执行 Windows 系统常用快捷键 - MCP标准格式版本（支持批量执行）

    这个函数通过 pyautogui 库模拟键盘快捷键操作，实现对 Windows 系统的各种控制功能。
    支持系统操作、窗口管理、编辑导航、截图录屏等多种快捷键操作。
    可以执行单个或多个快捷键操作。

    Args:
        actions (list): 要执行的快捷键操作名称列表，支持以下值：
           系统相关:
           - lock_screen: 锁定屏幕 (Win+L)
           - task_manager: 打开任务管理器 (Ctrl+Shift+Esc)
           - search_apps: 打开搜索应用，打开系统搜索 (Win+Q)
           - file_explorer: 打开文件资源管理器，打开文件夹 (Win+E)
           - settings: 打开设置 (Win+I)
           - notifications: 打开通知中心 (Win+A)
           - quick_link_menu: 打开快速链接菜单 (Win+X)
           - delete: 删除 (delete)
           - enter: 回车 (enter)

           窗口和任务管理:
           - task_view: 打开任务视图 (Win+Tab)
           - new_virtual_desktop: 创建新的虚拟桌面 (Win+Ctrl+D)
           - close_virtual_desktop: 关闭当前虚拟桌面 (Win+Ctrl+F4)
           - switch_desktop_left: 切换到左侧虚拟桌面 (Win+Ctrl+Left)
           - switch_desktop_right: 切换到右侧虚拟桌面 (Win+Ctrl+Right)
           - minimize_all: 最小化所有窗口 (Win+M)
           - show_desktop: 显示桌面 (Win+D)
           - maximize_window: 最大化当前窗口 (Win+Up)
           - minimize_window: 最小化当前窗口 (Win+Down)
           - dock_left: 将窗口停靠到左侧 (Win+Left)
           - dock_right: 将窗口停靠到右侧 (Win+Right)

           通用编辑和导航:
           - copy: 复制 (Ctrl+C)
           - cut: 剪切 (Ctrl+X)
           - paste: 粘贴 (Ctrl+V)
           - paste_special: 选择性粘贴 (Ctrl+Shift+V)
           - undo: 撤销 (Ctrl+Z)
           - redo: 重做 (Ctrl+Y)
           - select_all: 全选 (Ctrl+A)
           - find: 查找 (Ctrl+F)
           - find_next: 查找下一个 (F3)
           - find_previous: 查找上一个 (Shift+F3)
           - replace: 替换 (Ctrl+H)
           - refresh: 刷新 (F5)
           - hard_refresh: 强制刷新 (Ctrl+F5)

           截图和录屏:
           - screenshot: 全屏截图 (PrintScreen)
           - screenshot_active_window: 当前窗口截图 (Alt+PrintScreen)
           - screenshot_rectangular: 矩形截图 (Win+Shift+S)

           浏览器/应用常用:
           - new_window: 新建窗口 (Ctrl+N)
           - new_tab: 新建标签页 (Ctrl+T)
           - close_tab: 关闭标签页 (Ctrl+W)
           - reopen_closed_tab: 重新打开关闭的标签页 (Ctrl+Shift+T)
           - next_tab: 切换到下一个标签页 (Ctrl+Tab)
           - previous_tab: 切换到上一个标签页 (Ctrl+Shift+Tab)
           - open_address_bar: 聚焦地址栏 (Ctrl+L)
           - fullscreen: 全屏/退出全屏 (F11)
           - zoom_in: 放大 (Ctrl+Plus)
           - zoom_out: 缩小 (Ctrl+Minus)
           - reset_zoom: 重置缩放 (Ctrl+0)
           - save: 保存文件 (Ctrl+s)

           辅助功能:
           - magnifier: 启动放大镜并放大 (Win+Plus)
           - magnifier_zoom_in: 放大镜放大 (Win+Plus)
           - magnifier_zoom_out: 放大镜缩小 (Win+Minus)

           其他:
           - properties: 查看属性 (Alt+Enter)
           - rename: 重命名 (F2)

    Returns:
        str: 执行结果描述，包括成功和失败的操作详情

    Example:
        >>> windows_shortcut(["copy", "paste"])
        '已成功执行以下操作: copy, paste。'

        >>> windows_shortcut(["unknown_action", "copy"])
        '部分操作执行失败: unknown_action(不支持的操作: 'unknown_action')。成功执行: copy。'
    """
    # 定义快捷键映射字典
    shortcuts = {
        # 系统相关
        'lock_screen': ('win', 'l'),
        'task_manager': ('ctrl', 'shift', 'esc'),
        'switch_user': ('ctrl', 'alt', 'del'),  # 通常会打开安全选项菜单
        'log_off': ('win', 'x'),
        'search_apps': ('win', 'q'),
        'run_dialog': ('win', 'r'),
        'file_explorer': ('win', 'e'),
        'settings': ('win', 'i'),
        'notifications': ('win', 'a'),
        'quick_link_menu': ('win', 'x'),  # Win+X 菜单
        'delete': ('delete',),
        'enter': ('enter',),

        # 窗口和任务管理
        'task_view': ('win', 'tab'),
        'timeline': ('win', 'tab'),  # 在某些版本中与任务视图相同
        'new_virtual_desktop': ('win', 'ctrl', 'd'),
        'close_virtual_desktop': ('win', 'ctrl', 'f4'),
        'switch_desktop_left': ('win', 'ctrl', 'left'),
        'switch_desktop_right': ('win', 'ctrl', 'right'),
        'minimize_all': ('win', 'm'),
        'show_desktop': ('win', 'd'),
        'maximize_window': ('win', 'up'),
        'minimize_window': ('win', 'down'),
        'dock_left': ('win', 'left'),
        'dock_right': ('win', 'right'),

        # 通用编辑和导航
        'copy': ('ctrl', 'c'),
        'cut': ('ctrl', 'x'),
        'paste': ('ctrl', 'v'),
        'paste_special': ('ctrl', 'shift', 'v'),  # 某些应用支持
        'undo': ('ctrl', 'z'),
        'redo': ('ctrl', 'y'),
        'select_all': ('ctrl', 'a'),
        'find': ('ctrl', 'f'),
        'find_next': ('f3',),
        'find_previous': ('shift', 'f3'),
        'replace': ('ctrl', 'h'),
        'refresh': ('f5',),
        'hard_refresh': ('ctrl', 'f5'),

        # 截图和录屏 (部分功能可能需要配合 Snipping Tool/截图工具)
        'screenshot': ('printscreen',),
        'screenshot_active_window': ('alt', 'printscreen'),
        'screenshot_rectangular': ('win', 'shift', 's'),  # Windows 10/11 录屏快捷
        'screen_recording': ('win', 'alt', 'r'),  # Windows 10/11 录屏快捷
        'game_bar': ('win', 'g'),  # Xbox Game Bar

        # 浏览器/应用常用 (通常在应用内有效)
        'new_window': ('ctrl', 'n'),
        'new_tab': ('ctrl', 't'),
        'close_tab': ('ctrl', 'w'),
        'reopen_closed_tab': ('ctrl', 'shift', 't'),
        'next_tab': ('ctrl', 'tab'),
        'previous_tab': ('ctrl', 'shift', 'tab'),
        'open_address_bar': ('ctrl', 'l'),
        'fullscreen': ('f11',),
        'zoom_in': ('ctrl', '+'),
        'zoom_out': ('ctrl', '-'),
        'reset_zoom': ('ctrl', '0'),
        'save': ('ctrl', 's'),

        # 辅助功能
        'narrator': ('win', 'ctrl', 'enter'),
        'magnifier': ('win', '+'),  # 启动并放大
        'magnifier_zoom_in': ('win', '+'),
        'magnifier_zoom_out': ('win', '-'),
        'high_contrast': ('left alt', 'left shift', 'printscreen'),  # 或 Alt+Shift+PrtScn

        # 其他
        'rename': ('f2',),  # 在文件资源管理器中重命名
        'properties': ('alt', 'enter'),  # 或 Ctrl+Shift+Esc 打开任务管理器后选中进程按此
    }

    # 确保输入是列表格式
    if not isinstance(actions, list):
        return "参数错误：actions 必须是一个快捷键操作名称列表"

    # 分别存储成功和失败的操作
    successful_actions = []
    failed_actions = []

    # 处理需要连续按键的特殊情况
    def handle_special_action(action):
        try:
            if action == 'log_off':
                pyautogui.hotkey('win', 'x')
                time.sleep(0.2)
                pyautogui.press('u')
                time.sleep(0.2)
                pyautogui.press('o')
                return True, f"已执行: {action} (通过 Win+X -> U -> O)"
            elif action == 'shutdown':
                pyautogui.hotkey('win', 'x')
                time.sleep(0.2)
                pyautogui.press('u')
                time.sleep(0.2)
                pyautogui.press('u')
                return True, f"已执行: {action} (通过 Win+X -> U -> U)"
            return False, ""
        except Exception as e:
            return False, f"执行 '{action}' 时出错: {e}"

    # 遍历所有请求的操作
    for action in actions:
        # 处理特殊操作
        is_special, special_result = handle_special_action(action)
        if is_special:
            if "出错" not in special_result:
                successful_actions.append(action)
            else:
                failed_actions.append(f"{action}({special_result})")
            continue

        # 检查请求的操作是否受支持
        if action not in shortcuts:
            failed_actions.append(f"{action}(不支持的操作: '{action}')")
            continue

        # 执行标准快捷键
        try:
            pyautogui.hotkey(*shortcuts[action])
            successful_actions.append(action)
        except Exception as e:
            failed_actions.append(f"{action}(执行 '{action}' 时出错: {e})")

    # 等待所有操作执行完成
    if successful_actions:
        time.sleep(len(successful_actions) * 0.1)  # 根据执行操作数量调整等待时间

    # 构造返回信息
    result_message = ""
    if successful_actions:
        result_message += f"已成功执行以下操作: {', '.join(successful_actions)}。"
    if failed_actions:
        if successful_actions:
            result_message += f" 部分操作执行失败: {', '.join(failed_actions)}。"
        else:
            result_message += f"操作执行失败: {', '.join(failed_actions)}。"

    if not successful_actions and not failed_actions:
        result_message = "没有指定要执行的操作。"

    return result_message

@mcp.tool()
def create_folders_in_active_directory(folder_names: list) -> str:
    """
    在当前活动文件夹路径下创建多个新文件夹

    该函数会自动获取当前活动的文件夹路径（通过文件资源管理器窗口），
    然后在该路径下创建用户指定的文件夹列表。如果文件夹已存在，则不会重复创建。

    Args:
        folder_names (list): 要创建的文件夹名称列表，每个元素为字符串类型的文件夹名称
            例如: ["项目文档", "代码备份", "测试结果"]

    Returns:
        str: 操作结果描述，包括：
            - 成功创建的文件夹列表
            - 已存在的文件夹列表
            - 出现错误时的错误信息

    Example:
        >>> create_folders_in_active_directory(["文档", "图片", "视频"])
        '已成功创建以下文件夹: 文档, 图片, 视频。'

        >>> create_folders_in_active_directory(["已存在文件夹", "新文件夹"])
        '已成功创建以下文件夹: 新文件夹。 以下文件夹已存在: 已存在文件夹。'

        >>> create_folders_in_active_directory([])
        '没有指定要创建的文件夹。'
    """
    try:
        # 检查输入参数是否为空
        if not folder_names:
            return "没有指定要创建的文件夹。"

        # 获取当前活动文件夹路径
        active_path = get_activate_path()

        # 检查路径是否存在
        if not os.path.exists(active_path):
            return f"操作失败：活动路径不存在: {active_path}"

        # 检查是否为目录
        if not os.path.isdir(active_path):
            return f"操作失败：当前活动窗口不是目录文件夹: {active_path}"

        created_folders = []
        existing_folders = []

        # 遍历文件夹名称列表，创建每个文件夹
        for folder_name in folder_names:
            # 构造完整路径
            new_folder_path = os.path.join(active_path, folder_name)
            # 如果文件夹不存在，则创建
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
                created_folders.append(folder_name)
                print(f"已创建文件夹: {new_folder_path}")
            else:
                existing_folders.append(folder_name)
                print(f"文件夹已存在: {new_folder_path}")

        # 构造返回信息
        result_message = ""
        if created_folders:
            result_message += f"已成功创建以下文件夹: {', '.join(created_folders)}。"
        if existing_folders:
            if created_folders:
                result_message += f" 以下文件夹已存在: {', '.join(existing_folders)}。"
            else:
                result_message += f"所有文件夹均已存在: {', '.join(existing_folders)}。"

        return result_message

    except Exception as e:
        return f"创建文件夹时出错: {str(e)}"

@mcp.tool()
def open_other_apps(app_names: list) -> str:
    """
    通过Windows开始菜单搜索功能打开软件

    当其他函数无法打开某些软件时如QQ，微信等，可以使用此函数通过
    Windows开始菜单的搜索功能来启动应用程序。该函数会模拟按下Win键，
    输入软件名称并回车来启动程序。

    Args:
        app_names (list): 要启动的软件名称列表，例如 ["微信", "QQ音乐", "Photoshop"]

    Returns:
        str: 操作结果描述，包含成功打开的软件列表

    Example:
        >>> open_other_apps(["微信", "QQ音乐"])
        '已打开以下软件: 微信, QQ音乐'
    """
    open_success = []
    for app_name in app_names:
        try:
            # 按下Win键打开开始菜单
            pyautogui.press('win')
            # 等待开始菜单打开
            time.sleep(0.5)
            # 将软件名复制到剪贴板
            pyperclip.copy(app_name)
            # 粘贴软件名（使用Ctrl+V）
            pyautogui.hotkey('ctrl', 'v')
            # 等待软件名粘贴完成
            time.sleep(0.5)
            # 按回车键启动软件
            pyautogui.press('enter')
            time.sleep(1)
            open_success.append(app_name)
        except Exception as e:
            return f"打开软件{app_name}时出错: {str(e)}"
    return f"已打开以下软件: {', '.join(open_success)}"

# @mcp.tool()
# def time_late(seconds: int) -> str:
#     """
#     延迟执行指定的秒数

#     该函数会暂停当前程序的执行，等待指定的秒数。这在需要在程序中引入
#     时间间隔或等待外部事件完成时非常有用。

#     Args:
#         seconds (int): 要延迟的秒数，必须为非负整数

#     Returns:
#         str: 操作结果描述，包含延迟的秒数

#     Example:
#         >>> time_late(5)
#         '已延迟执行5秒'
#     """
#     if seconds < 0:
#         return "错误：秒数必须为非负整数"
#     time.sleep(seconds)
#     return f"已延迟执行{seconds}秒"

@mcp.tool()
def activate_window(pid: int) -> str:
    """
    激活指定进程ID（pid）的窗口

    该函数会将当前活动窗口切换到指定进程ID对应的窗口。如果指定的进程ID
    不存在或无效，则会返回错误信息。

    Args:
        pid (int): 要激活的窗口的进程ID

    Returns:
        str: 操作结果描述，包含激活的窗口的软件名称和进程ID

    Example:
        >>> activate_window(1234)
        '激活窗口软件为：notepad.exe，进程ID为：1234'
    """
    try:
        activate_window_by_pid(pid)
        if get_activate_path() == "":
            current_file_path = ""
        else:
            current_file_path = "当前文件路径为："+get_activate_path()
        return f"激活窗口软件为：{get_active_window_info()['name']}，进程ID为：{pid}，{current_file_path}。"
    except Exception as e:
        return f"激活窗口时出错: {str(e)}"

@mcp.tool()
def open_ai_urls(urls: list, user_contents: list = None) -> str:
    """
    打开指定的AI网站列表，并将对应的用户内容粘贴到各个网站中
    
    该函数可以同时打开多个AI网站（如豆包、通义千问、DeepSeek、KIMI等），并将对应的文本内容
    自动复制到剪切板并粘贴到每个打开的网页中，方便快速与多个AI进行交互。
    
    Args:
        urls (list): 要打开的AI网站URL地址列表
        user_contents (list, optional): 需要粘贴到网站中的文本内容列表。
            - 如果提供一个内容列表，将按顺序将不同内容粘贴到对应网站
            - 如果提供单个字符串，将在所有网站中粘贴相同内容
            - 如果不提供或为空，则仅打开网站不粘贴内容
            默认值为None。
        
    Returns:
        str: 操作结果描述，包括：
            - 成功打开网站并粘贴内容时返回确认信息
            - 出现错误时返回错误描述
            
    Example:
        >>> open_ai_urls(["https://www.doubao.com/chat/", "https://www.tongyi.com/qianwen"], 
                         ["请帮我写一篇关于人工智能的报告", "解释一下量子计算的基本原理"])
        '已成功打开2个AI网站并写入对应内容'
        
        >>> open_ai_urls(["https://chat.deepseek.com/", "https://www.kimi.com/zh/"], 
                         "请分析当前市场趋势")
        '已成功打开2个AI网站并写入相同内容'
        
        >>> open_ai_urls(["https://www.doubao.com/chat/", "https://www.tongyi.com/qianwen"])
        '已成功打开2个AI网站'
        
    Supported AI Websites:
        - 豆包AI: https://www.doubao.com/chat/
        - 豆包AI写作: https://www.doubao.com/chat/write
        - 豆包AI生成图像: https://www.doubao.com/chat/create-image
        - 豆包AI编程写代码: https://www.doubao.com/code/chat
        - 豆包AI翻译: https://www.doubao.com/chat/translate
        - 豆包AI智能体: https://www.doubao.com/chat/bot/discover
        - 通义千问AI: https://www.tongyi.com/qianwen
        - 通义千问AIPPT: https://www.tongyi.com/aippt
        - 通义千问AI实时记录，会议记录，语音记录，AI翻译: https://www.tongyi.com/live/
        - 通义千问音频视频速读: https://www.tongyi.com/discover/audioread
        - 通义千问阅读文档，阅读助手: https://www.tongyi.com/read
        - DeepSeek: https://chat.deepseek.com/
        - KIMI: https://www.kimi.com/zh/
        - KIMI生成PPT: https://www.kimi.com/kimiplus/slides
        - KIMI医疗搜索: https://www.kimi.com/kimiplus/cu52bqh7l5gqdkncdg01
    """
    try:
        # 检查输入参数
        if not isinstance(urls, list):
            return "参数错误：urls 必须是一个网址列表"
        
        if not urls:
            return "错误：urls 列表不能为空"
        
        # 处理用户内容参数
        contents = []
        content_mode = "none"  # none, single, multiple
        
        if user_contents is None:
            content_mode = "none"
        elif isinstance(user_contents, str):
            # 单个内容，应用到所有网站
            content_mode = "single"
            contents = [user_contents] * len(urls)
        elif isinstance(user_contents, list):
            if not user_contents:
                content_mode = "none"
            else:
                content_mode = "multiple"
                # 如果内容列表长度小于URL列表，用最后一个内容填充
                contents = user_contents[:]
                if len(contents) < len(urls):
                    contents.extend([contents[-1]] * (len(urls) - len(contents)))
                # 如果内容列表长度大于URL列表，截取前面的部分
                contents = contents[:len(urls)]
        else:
            content_mode = "none"
        
        # 打开所有网站
        opened_count = 0
        pasted_count = 0
        
        for i, url in enumerate(urls):
            # 打开网站
            webbrowser.open_new(url)
            opened_count += 1
            
            # 如果有内容需要粘贴
            if content_mode in ["single", "multiple"] and i < len(contents) and contents[i]:
                # 等待页面加载
                time.sleep(1.5)
                # 复制内容到剪切板
                pyperclip.copy(contents[i])
                # 模拟粘贴操作
                pyautogui.hotkey('ctrl', 'v')
                pasted_count += 1
                # 等待粘贴完成
                time.sleep(0.5)
        
        # 构造返回信息
        result_msg = f"已成功打开{opened_count}个AI网站"
        if pasted_count > 0:
            if content_mode == "single":
                result_msg += "并写入相同内容"
            else:
                result_msg += "并写入对应内容"
            result_msg += "。若发现未生效，请手动粘贴一下。请手动按回车键确认。"
        else:
            result_msg += "。"
            
        return result_msg
        
    except Exception as e:
        return f"打开AI网站时出错: {str(e)}"



if __name__ == '__main__':
    #mcp.run()
    mcp.run(transport="http", port=9000)
    # 命令行中执行命令： fastmcp run server.py:mcp --transport http --port 9000

# 在 server.py 文件末尾替换原有的 if __name__ == '__main__': 代码块

# if __name__ == '__main__':
#     import logging
#     # 禁用或降低相关错误日志级别
#     logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
#     logging.getLogger("mcp.server").setLevel(logging.CRITICAL)
#     logging.getLogger("anyio").setLevel(logging.CRITICAL)
#
#     # 修改为持续等待连接的模式
#     while True:
#         try:
#             print("等待MCP连接...")
#             mcp.run(transport="http", port=9000)
#         except KeyboardInterrupt:
#             print("服务器已手动停止")
#             break
#         except Exception as e:
#             # 过滤掉ClosedResourceError相关的错误
#             error_str = str(e)
#             if ("ClosedResourceError" in error_str or
#                 "Unexpected ASGI message" in error_str or
#                 "ConnectionResetError" in error_str or
#                 "远程主机强迫关闭了一个现有的连接" in error_str):
#                 print("MCP链接已断开，正在等待链接...")
#             else:
#                 print(f"服务器运行出错: {error_str}")
#             time.sleep(1)
#         else:
#             # 正常退出时（如连接断开）
#             print("MCP链接已断开，正在等待链接...")
#             time.sleep(1)  # 短暂延迟后重新等待连接


