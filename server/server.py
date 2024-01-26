from quart import Quart, request, jsonify
from ava.ava_ai import Ava


app = Quart(__name__)
Ava = Ava()

@app.before_serving
async def initialize():
    await Ava.initialize()

@app.route("/")
async def index():
    return 'Hello, World!'

@app.route("/chat", methods=["POST"])
async def chat():
        req = await request.get_json()
        user = req['user']
        message = req['request']['content']
        ava_response = await Ava.send_message(message)
        return jsonify({"user": user, "response": {"type":"text", "content": ava_response, "voice_audio": None}}), 200

app.run(debug=True)