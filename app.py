from flask import Flask, jsonify, render_template, request

from bot import generate_reply


app = Flask(__name__)


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()

    if not message:
        return jsonify({"reply": "Ketik pesan dulu ya, saya siap bantu."}), 400

    return jsonify({"reply": generate_reply(message)})


if __name__ == "__main__":
    app.run(debug=True)
