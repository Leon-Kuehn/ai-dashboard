# ai-dashboard

A modern, self-hostable single-page dashboard for an AI server running **OpenClaw + Ollama** on a Proxmox VM with an NVIDIA RTX 3060 Ti.

## Features

- **Chat** – Full chat interface with conversation threads, model selector, and streaming-ready message bubbles (mock responses included)
- **Tasks** – Create and track AI agent tasks with status badges (queued / running / done / failed), progress bars, and log detail views
- **System Monitor** – Live metrics panel: CPU, RAM, GPU load, VRAM, GPU temperature, disk usage, uptime — auto-refreshing every 3 seconds with animated Chart.js graphs
- **Settings** – Configure Ollama/OpenClaw API endpoints, default model, dark/light mode, and API credentials (persisted to localStorage)

## Docker Deploy (recommended)

### Prerequisites

- Docker ≥ 24 and Docker Compose v2 installed on the Proxmox VM
- Port 80 and 443 open on the VM's firewall

### Steps

1. **Clone the repo** on the Proxmox VM:

   ```bash
   git clone https://github.com/Leon-Kuehn/ai-dashboard.git
   cd ai-dashboard
   ```

2. **Configure environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env and set OLLAMA_HOST / OPENCLAW_HOST to the correct IPs
   ```

   `.env` example:
   ```
   OLLAMA_HOST=192.168.1.100
   OLLAMA_PORT=11434
   OPENCLAW_HOST=192.168.1.100
   OPENCLAW_PORT=3000
   ```

3. **Start the stack:**

   ```bash
   docker compose up -d
   ```

4. **Open the dashboard** in your browser:

   ```
   https://<proxmox-vm-ip>
   ```

   Accept the self-signed certificate warning (or replace it — see below).

### Architecture

| Container | Role | Published ports |
|---|---|---|
| `dashboard` | nginx serving `dashboard.html` over HTTPS | 80, 443 |
| `metrics-proxy` | Read-only system metrics API | none (internal only) |

- All containers run as **non-root** with `cap_drop: ALL` and `read_only: true` filesystems.
- The metrics-proxy is only reachable from within the Docker network — never directly from the host or internet.
- nginx proxies `/api/metrics` → metrics-proxy, `/api/ollama/` → Ollama, `/api/openclaw/` → OpenClaw, so the browser never talks to external hosts directly.

### Replacing the self-signed certificate

The container generates a self-signed cert on first start and stores it in a named Docker volume (`nginx_ssl`).

**Option A — mkcert (trusted on LAN):**

```bash
mkcert -install
mkcert 192.168.1.100   # or your VM hostname
# Copy the generated cert/key into the volume:
docker cp 192.168.1.100.pem   ai-dashboard-dashboard-1:/etc/nginx/ssl/cert.pem
docker cp 192.168.1.100-key.pem ai-dashboard-dashboard-1:/etc/nginx/ssl/key.pem
docker compose restart dashboard
```

**Option B — Let's Encrypt (requires a public domain):**

Use Certbot to obtain a certificate for your domain, then mount the cert/key into the container via a bind mount in `docker-compose.yml`.

---

## Open locally (no Docker)

Just open `dashboard.html` directly in your browser:

```
open dashboard.html
```

Or serve it with Python for full local-network access:

```bash
python -m http.server 8000
# then visit http://localhost:8000/dashboard.html
```

> When opened without Docker, the System Monitor falls back to simulated data because `/api/metrics` is unavailable.

## Integrating with Ollama

1. Open the **Settings** page in the dashboard
2. Set **Ollama Base URL** to `/api/ollama` (default when using Docker) or your direct Ollama URL
3. Click **Test Connection** to verify
4. Select your default model from the dropdown
5. The Chat section will use this endpoint for completions (`POST /api/chat`)

## Integrating with OpenClaw

1. In **Settings**, set **OpenClaw Base URL** to `/api/openclaw` (default when using Docker) or your direct OpenClaw URL
2. API key and bearer token fields are available for authenticated endpoints
3. Full integration is prepared — swap mock responses in `dashboard.html` with real `fetch()` calls to your OpenClaw endpoints

## Proxmox GPU Passthrough (RTX 3060 Ti)

For GPU passthrough on Proxmox, the general steps are:

1. Enable IOMMU in your host BIOS (VT-d / AMD-Vi)
2. Add `intel_iommu=on` (or `amd_iommu=on`) to your GRUB cmdline
3. Blacklist the `nouveau` driver on the host and add `vfio-pci` to `/etc/modules`
4. In Proxmox, add the GPU PCI device to your VM with **Primary GPU** and **ROM-Bar** enabled
5. Install NVIDIA drivers inside the VM normally

See the [Proxmox PCI Passthrough wiki](https://pve.proxmox.com/wiki/PCI_Passthrough) for full details.

