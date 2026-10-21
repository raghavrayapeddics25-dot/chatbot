from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)
import os
client = OpenAI(api_key=os.environ.get("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")

# Store chat history per session (simple version)
chat_histories = {}
import json
import requests

def get_weather(city):
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    r = requests.get(url).json()
    if r.get("cod") != 200:
        return {"error": f"Could not find weather for {city}"}
    return {
        "city": city,
        "temp": r["main"]["temp"],
        "description": r["weather"][0]["description"]
    }

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        }
    }
]

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data["message"]
    session_id = data.get("session_id", "default")

    history = chat_histories.setdefault(session_id, [
        {"role": "system", "content": "You are a friendly, helpful assistant."}
    ])

    history.append({"role": "user", "content": user_msg})

    # Keep memory short: system prompt + last 9 messages
    if len(history) > 10:
        history[:] = [history[0]] + history[-9:]

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=history,
        tools=tools,
        max_tokens=500
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        history.append({"role": "assistant", "tool_calls": [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = get_weather(args["city"])
            history.append({"role": "tool", "tool_call_id": tc.id,
                            "content": json.dumps(result)})
        final = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=history,
            max_tokens=500
        )
        bot_reply = final.choices[0].message.content
    else:
        bot_reply = msg.content

    history.append({"role": "assistant", "content": bot_reply})
    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    app.run(debug=True)

