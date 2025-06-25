from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from scenario_logic import scenario_chat_stream,scenario_chat_logic
from chat_logic import interactive_chat_logic
import json, time, logging

app = Flask(__name__)
CORS(app)
log = logging.getLogger(__name__)

# ---------- 既有 /api (保留) ---------- #
@app.post("/api")
def api_router():
    body = request.get_json(force=True)
    mode = body.get("mode")

    if mode == "interactive":
        data, status = interactive_chat_logic(body)
    elif mode == "scenario":
        data, status = scenario_chat_logic(body)
    else:
        data, status = {"error": "invalid mode"}, 400

    return jsonify(data), status


@app.get("/stream")
def stream():
    scenario = request.args.get('scenario','')
    roles    = request.args.getlist('role')
    news     = request.args.get('news','')

    body = {"scenario":scenario, "roles":roles, "news":news}

    def sse_lines():
        for m in scenario_chat_stream(body):              # ★ 用新函式
            yield f"data:{json.dumps(m, ensure_ascii=False)}\n\n"
        yield "event:done\ndata:ok\n\n"

    return Response(
        sse_lines(),
        mimetype="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"}
    )


if __name__ == "__main__":
    app.run(port=5000, debug=True)
