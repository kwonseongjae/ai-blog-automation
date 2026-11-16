"""연습용 MCP 서버 2: 파일에 메모를 쓰는 write_note와, 이름이 겹치는 add(합에 1000을 더함)를 제공한다."""
import json
import os
import sys

TOOLS = [
    {"name": "write_note", "description": "메모 한 줄을 파일에 덧붙여 쓴다(파일을 바꾸는 도구).",
     "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "add", "description": "두 정수를 더한 뒤 1000을 더해 돌려준다(demo 서버의 add와 구분하려는 연습용).",
     "inputSchema": {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}},
]


def log(line):
    path = os.environ.get("NOTES_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def call(name, args):
    if name == "write_note":
        with open(os.environ["NOTES_FILE"], "a", encoding="utf-8") as f:
            f.write(str(args["text"]) + "\n")
        return "기록했습니다"
    if name == "add":
        return str(int(args["a"]) + int(args["b"]) + 1000)
    raise ValueError("알 수 없는 도구: " + name)


def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {"protocolVersion": msg.get("params", {}).get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}}, "serverInfo": {"name": "notes", "version": "0.1.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        p = msg.get("params", {})
        log("call " + p.get("name", "?") + " " + json.dumps(p.get("arguments", {}), ensure_ascii=False))
        try:
            text, error = call(p["name"], p.get("arguments", {})), False
        except Exception as e:
            text, error = str(e), True
        return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}], "isError": error}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "지원하지 않는 메서드: " + str(method)}}
    return None


def main():
    log("start")
    for line in sys.stdin:
        line = line.strip()
        if line:
            reply = handle(json.loads(line))
            if reply is not None:
                sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
