"""
metrics_proxy.py — Read-only system metrics API.

Endpoints:
  GET /metrics  — JSON system metrics (CPU, RAM, disk, uptime, GPU, Ollama, OpenClaw)
  GET /health   — {"status": "ok"}
"""

import http.server
import json
import os
import subprocess
import urllib.request
import urllib.error

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "ollama")
OLLAMA_PORT = os.environ.get("OLLAMA_PORT", "11434")
OPENCLAW_HOST = os.environ.get("OPENCLAW_HOST", "openclaw")
OPENCLAW_PORT = os.environ.get("OPENCLAW_PORT", "3000")
LISTEN_PORT = int(os.environ.get("METRICS_PORT", "9090"))


def _cpu_percent():
    if HAS_PSUTIL:
        return psutil.cpu_percent(interval=0.2)
    # Fallback: read /proc/stat for a rough reading
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        parts = list(map(int, line.split()[1:]))
        idle = parts[3]
        total = sum(parts)
        return round((1 - idle / total) * 100, 1) if total else None
    except Exception:
        return None


def _ram():
    if HAS_PSUTIL:
        m = psutil.virtual_memory()
        return {
            "total_gb": round(m.total / 1024 ** 3, 1),
            "used_gb": round(m.used / 1024 ** 3, 1),
            "percent": m.percent,
        }
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k.strip()] = int(v.split()[0])  # kB
        total = info.get("MemTotal", 0)
        available = info.get("MemAvailable", 0)
        used = total - available
        pct = round(used / total * 100, 1) if total else 0
        return {
            "total_gb": round(total / 1024 ** 2, 1),
            "used_gb": round(used / 1024 ** 2, 1),
            "percent": pct,
        }
    except Exception:
        return {"total_gb": None, "used_gb": None, "percent": None}


def _disk():
    if HAS_PSUTIL:
        d = psutil.disk_usage("/")
        return {
            "total_gb": round(d.total / 1024 ** 3, 1),
            "used_gb": round(d.used / 1024 ** 3, 1),
            "percent": d.percent,
        }
    try:
        st = os.statvfs("/")
        total = st.f_frsize * st.f_blocks
        free = st.f_frsize * st.f_bfree
        used = total - free
        pct = round(used / total * 100, 1) if total else 0
        return {
            "total_gb": round(total / 1024 ** 3, 1),
            "used_gb": round(used / 1024 ** 3, 1),
            "percent": pct,
        }
    except Exception:
        return {"total_gb": None, "used_gb": None, "percent": None}


def _uptime():
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        return {"seconds": int(seconds), "days": days, "hours": hours, "minutes": minutes}
    except Exception:
        return {"seconds": None, "days": None, "hours": None, "minutes": None}


def _gpu():
    """Query nvidia-smi; return nulls if unavailable."""
    null_gpu = {
        "utilization_gpu": None,
        "utilization_memory": None,
        "memory_total_mb": None,
        "memory_used_mb": None,
        "temperature": None,
    }
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,utilization.memory,memory.total,memory.used,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return null_gpu
        parts = [p.strip() for p in result.stdout.strip().split(",")]
        if len(parts) < 5:
            return null_gpu
        return {
            "utilization_gpu": float(parts[0]),
            "utilization_memory": float(parts[1]),
            "memory_total_mb": float(parts[2]),
            "memory_used_mb": float(parts[3]),
            "temperature": float(parts[4]),
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, OSError):
        return null_gpu


def _ollama():
    try:
        url = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/tags"
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "") for m in data.get("models", [])]
            return {"status": "up", "models": models}
    except Exception:
        return {"status": "down", "models": []}


def _openclaw():
    try:
        url = f"http://{OPENCLAW_HOST}:{OPENCLAW_PORT}/health"
        with urllib.request.urlopen(url, timeout=3) as resp:
            if resp.status == 200:
                return {"status": "up"}
    except Exception:
        pass
    return {"status": "down"}


def _build_metrics():
    return {
        "cpu_percent": _cpu_percent(),
        "ram": _ram(),
        "disk": _disk(),
        "uptime": _uptime(),
        "gpu": _gpu(),
        "ollama": _ollama(),
        "openclaw": _openclaw(),
    }


class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # suppress default access log noise
        pass

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/metrics":
            self._send_json(200, _build_metrics())
        elif self.path == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", LISTEN_PORT), MetricsHandler)
    print(f"metrics-proxy listening on :{LISTEN_PORT}", flush=True)
    server.serve_forever()
