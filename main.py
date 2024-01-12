import requests
import json
import openai
openai.api_base = "https://ai.devtool.tech/proxy/v1"
openai.api_key = "sk-KYzhYJ3CFX7oSj***********************" # chatgpt的key
amap_key = '537bc4b5be00c6a4676eec*********************'  # 高德地图的key

def get_adcode(address):
    url = 'https://restapi.amap.com/v3/geocode/geo'
    params = {'key': amap_key, 'address': address}
    response = requests.get(url, params=params)
    return response.json()['geocodes'][0]['adcode']

def get_current_weather(location, unit="celsius"):
    url = "https://restapi.amap.com/v3/weather/weatherInfo?"
    params = {"key": amap_key, "city": get_adcode(location)}
    weather_data = requests.get(url=url, params=params).json().get("lives")[0]
    # 控制温度单位, 高德地图默认单位为摄氏度
    if unit not in ["celsius", "fahrenheit"]:
        print("Error: the unit is invalid!")
        return None
    elif unit == "fahrenheit":
        weather_data["temperature"] = str(int(weather_data["temperature"])*9/5 + 32)
    weather_info = {
        "location": location,
        "temperature": weather_data["temperature"],
        "unit": unit,
        "winddirection": weather_data["winddirection"],
        'windpower': weather_data['windpower'],
        'humidity':weather_data['humidity'],
        "forecast": weather_data["weather"],
    }
    return json.dumps(weather_info)
def get_weather_forecast(location, days=4):
    url = "https://restapi.amap.com/v3/weather/weatherInfo?extensions=all"
    params = {"key": amap_key, "city": get_adcode(location)}
    weather_data = requests.get(url=url, params=params).json().get("forecasts")[0]
    print("In the next three days",weather_data)
    forecast_info = []
    for d in weather_data["casts"][:days]:
        forecast_info.append({
            "date": d["date"],
            "dayweather": d["dayweather"],
            "nightweather": d["nightweather"],
            "daytemp": d["daytemp"],
            "nighttemp": d["nighttemp"]
        })
    return json.dumps({"location": location, "forecast": forecast_info})

# Step 1, send model the user query and what functions it has access to
def run_conversation(content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "user", "content": content}],
        functions=[
            {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
            {
                "name": "get_weather_forecast",
                "description": "Get weather forecast for a given location in the next few days",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Any location, for example 'Beijing'",
                        },
                        "days": {
                            "type": "integer",
                            "description": "number of days, up to 7",
                        }
                    },
                    "required": ["location"],
                },
            },
        ],
        function_call="auto",
    )
    message = response["choices"][0]["message"]
    print(message)
    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        arguments = json.loads(message.get('function_call', {}).get('arguments'))
        # 使用字典来映射函数名与函数之间的关系
        functions_map = {
            'get_current_weather': get_current_weather,
            'get_weather_forecast': get_weather_forecast,
            # 在这里添加任何你需要的函数...
        }
        function_to_call = functions_map.get(function_name)
        if function_to_call:
            function_response = function_to_call(location=arguments.get('location'))
        else:
            # 当找不到函数名时返回一个错误信息
            function_response = json.dumps({"error": f"The function {function_name} is not supported."})
        print(function_response)
        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "user", "content": "天气怎么样?"},
                message,
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                },
            ],
        )
        return second_response.choices[0].message['content']
print(run_conversation(content="北京市海淀区现在天气怎么样?"))
print("********************************************", end='\n\n')
print(run_conversation(content="预测一下辽宁省大连市金石滩最近两天的天气? "))



