#!/usr/bin/env python3
import http.server
import socketserver
import subprocess

PORT = 9400

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def get_gpu_metrics():
    try:
        cmd = [
            "nvidia-smi",
            "--query-gpu=temperature.gpu,power.draw,memory.used,memory.free",
            "--format=csv,noheader,nounits"
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip().splitlines()[0]
        temp, power, mem_used, mem_free = [x.strip() for x in out.split(",")]
        return float(temp), float(power), float(mem_used), float(mem_free)
    except Exception:
        return 0.0, 0.0, 0.0, 0.0

class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            temp, power, mem_used, mem_free = get_gpu_metrics()
            body = (
                "# HELP DCGM_FI_DEV_GPU_TEMP GPU temperature (in C).\n"
                "# TYPE DCGM_FI_DEV_GPU_TEMP gauge\n"
                f'DCGM_FI_DEV_GPU_TEMP{{gpu="0"}} {temp}\n'
                "# HELP DCGM_FI_DEV_POWER_USAGE Power draw (in W).\n"
                "# TYPE DCGM_FI_DEV_POWER_USAGE gauge\n"
                f'DCGM_FI_DEV_POWER_USAGE{{gpu="0"}} {power}\n'
                "# HELP DCGM_FI_DEV_FB_USED Framebuffer memory used (in MiB).\n"
                "# TYPE DCGM_FI_DEV_FB_USED gauge\n"
                f'DCGM_FI_DEV_FB_USED{{gpu="0"}} {mem_used}\n'
                "# HELP DCGM_FI_DEV_FB_FREE Framebuffer memory free (in MiB).\n"
                "# TYPE DCGM_FI_DEV_FB_FREE gauge\n"
                f'DCGM_FI_DEV_FB_FREE{{gpu="0"}} {mem_free}\n'
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
