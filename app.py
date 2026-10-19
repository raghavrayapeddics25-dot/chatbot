from flask import Flask, render_template, request, jsonify
from openai import OpenAI

app = Flask(__name__)
import os
client = OpenAI(api_key=os.environ.get("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")

# Store chat history per session (simple version)
chat_histories = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data["message"]
    session_id = data.get("session_id", "default")

    # Get or create history for this user
    history = chat_histories.setdefault(session_id, [
        {"role": "system", "content": "You are a friendly, helpful assistant."}
    ])

    history.append({"role": "user", "content": user_msg})

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=history
    )

    bot_reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": bot_reply})

    return jsonify({"reply": bot_reply})

if __name__ == "__main__":
    app.run(debug=True)

