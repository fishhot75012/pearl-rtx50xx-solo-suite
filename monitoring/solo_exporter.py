#!/usr/bin/env python3
import http.server
import socketserver
import subprocess
import urllib.request
import time
import re

PORT = 9401
CONTAINER_NAME = "pearl-miner"
VLLM_URL = "http://localhost:8000/metrics"
BLOCK_PATTERN = re.compile(r"Accepted block|Block accepted|found block|SubmitBlock.*accepted|Block submitted", re.IGNORECASE)

REF_TOK_PER_SEC = 215.0
REF_GPU_THS = 190.0
NETWORK_EHS = 102.0
BLOCKS_PER_DAY = 494.0

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def get_vllm_stats():
    try:
        req = urllib.request.urlopen(VLLM_URL, timeout=2).read().decode()
        reqs = 0
        tokens = 0
        for line in req.splitlines():
            if line.startswith("vllm:request_success_total"):
                reqs += float(line.split()[-1])
            elif line.startswith("vllm:generation_tokens_total"):
                tokens += float(line.split()[-1])
        return int(reqs), int(tokens)
    except Exception:
        return 0, 0

def count_solo_blocks():
    try:
        logs = subprocess.check_output(["docker", "logs", CONTAINER_NAME], stderr=subprocess.STDOUT).decode(errors="ignore")
        return len(BLOCK_PATTERN.findall(logs))
    except Exception:
        return 0

INITIAL_REQUESTS, LAST_TOKENS = get_vllm_stats()
LAST_TIME = time.time()
CURRENT_TTF_DAYS = 1088.0

class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global LAST_TOKENS, LAST_TIME, CURRENT_TTF_DAYS
        if self.path == "/metrics":
            blocks = count_solo_blocks()
            curr_reqs, curr_tokens = get_vllm_stats()
            session_work = max(0, curr_reqs - INITIAL_REQUESTS)

            now = time.time()
            dt = now - LAST_TIME
            if dt >= 2.0 and curr_tokens >= LAST_TOKENS:
                tok_sec = (curr_tokens - LAST_TOKENS) / dt
                LAST_TOKENS = curr_tokens
                LAST_TIME = now
                if tok_sec > 5.0:
                    est_ths = (tok_sec / REF_TOK_PER_SEC) * REF_GPU_THS
                    prob_per_block = est_ths / (NETWORK_EHS * 1_000_000.0)
                    CURRENT_TTF_DAYS = round(1.0 / (prob_per_block * BLOCKS_PER_DAY), 1)
                else:
                    CURRENT_TTF_DAYS = 9999.0

            body = (
                "# HELP pearl_solo_blocks_found Total number of solo blocks found by pearl-miner\n"
                "# TYPE pearl_solo_blocks_found gauge\n"
                f"pearl_solo_blocks_found {blocks}\n"
                "# HELP pearl_session_work_units Completed inference work units since session start\n"
                "# TYPE pearl_session_work_units counter\n"
                f"pearl_session_work_units {session_work}\n"
                "# HELP pearl_estimated_ttf_days Estimated Time To Find a solo block in days\n"
                "# TYPE pearl_estimated_ttf_days gauge\n"
                f"pearl_estimated_ttf_days {CURRENT_TTF_DAYS}\n"
            ).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

with ReusableTCPServer(("0.0.0.0", PORT), MetricsHandler) as httpd:
    httpd.serve_forever()
