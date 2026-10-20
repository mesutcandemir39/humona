"""Embedding worker for brain semantic search. Runs inside the machine-local venv (fastembed).

One-shot:  echo '{"texts": [...]}' | python embed.py            → {"vectors": [...]}
Daemon:    python embed.py --serve <state_dir>                   → 127.0.0.1 TCP, port in <state_dir>/embed.port,
           one JSON line per request/response, exits after IDLE seconds without requests.
Vectors are L2-normalized (dot product = cosine).
"""
import json
import os
import socketserver
import sys
import threading
import time
from pathlib import Path

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # multilingual: TR query ↔ EN note
IDLE = 900


def load(state):
    from fastembed import TextEmbedding
    return TextEmbedding(MODEL, cache_dir=str(Path(state) / "models"))


def embed(model, texts):
    out = []
    for v in model.embed(texts, batch_size=32):
        n = float((v * v).sum()) ** 0.5 or 1.0
        out.append([round(float(x) / n, 5) for x in v])
    return out


def serve(state):
    model = load(state)
    last = [time.time()]
    lock = threading.Lock()

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            last[0] = time.time()
            try:
                req = json.loads(self.rfile.readline())
                with lock:
                    vecs = embed(model, req.get("texts", []))
                self.wfile.write((json.dumps({"vectors": vecs}) + "\n").encode())
            except Exception as e:
                self.wfile.write((json.dumps({"error": str(e)}) + "\n").encode())

    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
    port_file = Path(state) / "embed.port"
    port_file.write_text("%d %d" % (srv.server_address[1], os.getpid()))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    while time.time() - last[0] < IDLE:
        time.sleep(10)
    srv.shutdown()
    if port_file.exists() and port_file.read_text().split()[-1] == str(os.getpid()):
        port_file.unlink()


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--serve":
        serve(sys.argv[2])
        return
    req = json.load(sys.stdin)
    json.dump({"vectors": embed(load(req["state"]), req["texts"])}, sys.stdout)


if __name__ == "__main__":
    main()
