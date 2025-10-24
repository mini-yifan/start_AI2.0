import requests
from urllib.parse import quote
import time
import webbrowser

def get_city_by_ip():
    try:
        # 添加lang=zh-CN参数指定返回中文结果
        response = requests.get('http://ip-api.com/json/?lang=zh-CN')
        data = response.json()
        #print(data)  # 打印完整返回数据，方便调试

        # 提取城市信息
        if data['status'] == 'success':
            city = data['city']  # 此时city为中文名称
            country = data['country']  # 国家也会是中文
            return city
        else:
            return "无法获取城市信息"
    except Exception as e:
        return f"获取失败：{str(e)}"

# city_name = get_city_by_ip()
# print("当前所在城市：", city_name)
#city_name = "杭州市"

def get_weather_use_url(city_name):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': 'https://weather.cma.cn/web/weather/58457.html',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Microsoft Edge";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        # 'Cookie': 'Hm_lvt_c758855eca53e5d78186936566552a13=1760605204; HMACCOUNT=31287CA8B298ACFF; _trs_uv=mgt6vtrn_6252_1dz2; _trs_ua_s_1=mgt6vtrn_6252_eklp; Hm_lpvt_c758855eca53e5d78186936566552a13=1760605675',
    }

    params = {
        'q': quote(city_name),
        'limit': '10',
        'timestamp': str(int(time.time() * 1000)),
    }

    response = requests.get('https://weather.cma.cn/api/autocomplete', params=params, headers=headers)

    data = response.json()
    city_code = data["data"][0].split("|")[0]

    open_url = "https://weather.cma.cn/web/weather/"+city_code+".html"
    # 在浏览器中打开搜索结果页面
    webbrowser.open_new(open_url)

    print(city_code, data["data"][0])

    url = "https://weather.cma.cn/api/now/"
    response = requests.get(url + city_code, headers=headers)
    print(response.json())
    return response.json()


def parse_weather_now(data):
    """
    解析天气数据中的 now 部分，并以中文格式返回
    """
    now_data = data['data']['now']

    # 将英文字段名映射为中文描述
    chinese_mapping = {
        'precipitation': '降水量',
        'temperature': '温度',
        'pressure': '气压',
        'humidity': '湿度',
        'windDirection': '风向',
        'windDirectionDegree': '风向角度',
        'windSpeed': '风速',
        'windScale': '风力等级',
        'feelst': '体感温度'
    }

    # 构建中文格式的天气信息
    result = []
    result.append("当前天气情况:")
    result.append(f"  {chinese_mapping['precipitation']}: {now_data['precipitation']}")
    result.append(f"  {chinese_mapping['temperature']}: {now_data['temperature']}°C")
    result.append(f"  {chinese_mapping['feelst']}: {now_data['feelst']}°C")
    result.append(f"  {chinese_mapping['precipitation']}: {now_data['precipitation']}mm")
    #result.append(f"  {chinese_mapping['pressure']}: {now_data['pressure']}hPa")
    result.append(f"  {chinese_mapping['humidity']}: {now_data['humidity']}%")
    result.append(f"  {chinese_mapping['windDirection']}: {now_data['windDirection']}")
    #result.append(f"  {chinese_mapping['windDirectionDegree']}: {now_data['windDirectionDegree']}°")
    #result.append(f"  {chinese_mapping['windSpeed']}: {now_data['windSpeed']}km/h")
    result.append(f"  {chinese_mapping['windScale']}: {now_data['windScale']}")

    return '\n'.join(result)

def get_weather(city_name=None):
    try:
        if city_name is None:
            city_name = get_city_by_ip()
            print("当前所在城市：", city_name)
        weather_data = get_weather_use_url(city_name)
        weather_info = parse_weather_now(weather_data)
        print(weather_info)
        return weather_info
    except Exception as e:
        print(f"获取天气信息失败：{str(e)}")
        return f"获取天气信息失败，请检查是否使用正确的和风天气API"

if __name__ == "__main__":
    time1 = time.time()
    get_weather("杭州")
    print("耗时1：", time.time() - time1)
    #get_weather("浦东")
    #get_weather("北京")
    time2 = time.time()
    get_weather()
    print("耗时2：", time.time() - time2)


