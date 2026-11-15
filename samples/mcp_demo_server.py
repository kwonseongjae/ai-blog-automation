"""연습용 MCP 서버: 표준 입출력으로 JSON-RPC를 주고받고 도구 두 개(add, word_count)를 제공한다."""
import json
import os
import sys

TOOLS = [
    {"name": "add", "description": "두 정수를 더한 값을 돌려준다.",
     "inputSchema": {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                     "required": ["a", "b"]}},
    {"name": "word_count", "description": "공백으로 나눈 단어 수를 센다.",
     "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
]


def log(line):
    path = os.environ.get("MCP_DEMO_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def call(name, args):
    if name == "add":
        return str(int(args["a"]) + int(args["b"]))
    if name == "word_count":
        return str(len(str(args["text"]).split()))
    raise ValueError("알 수 없는 도구: " + name)


def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        version = msg.get("params", {}).get("protocolVersion", "2025-06-18")
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": version, "capabilities": {"tools": {}},
            "serverInfo": {"name": "demo", "version": "0.1.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        p = msg.get("params", {})
        log("call " + p.get("name", "?") + " " + json.dumps(p.get("arguments", {}), ensure_ascii=False))
        try:
            text, error = call(p["name"], p.get("arguments", {})), False
        except Exception as e:  # 도구 오류는 결과 안에 담아 돌려준다
            text, error = str(e), True
        return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": error}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "지원하지 않는 메서드: " + str(method)}}
    return None  # 알림(notifications/...)에는 응답하지 않는다


def main():
    log("start")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        reply = handle(json.loads(line))
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    log("stop")


if __name__ == "__main__":
    main()
