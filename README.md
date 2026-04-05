# ai-dashboard

A modern, self-hostable single-page dashboard for an AI server running **OpenClaw + Ollama** on a Proxmox VM with an NVIDIA RTX 3060 Ti.

## Features

- **Chat** – Full chat interface with conversation threads, model selector, and streaming-ready message bubbles (mock responses included)
- **Tasks** – Create and track AI agent tasks with status badges (queued / running / done / failed), progress bars, and log detail views
- **System Monitor** – Live metrics panel: CPU, RAM, GPU load, VRAM, GPU temperature, disk usage, uptime — auto-refreshing every 3 seconds with animated Chart.js graphs
- **Settings** – Configure Ollama/OpenClaw API endpoints, default model, dark/light mode, and API credentials (persisted to localStorage)

## Usage

### Open locally

Just open `dashboard.html` directly in your browser:

```
open dashboard.html
```

Or serve it with Python for full local-network access:

```bash
python -m http.server 8000
# then visit http://localhost:8000/dashboard.html
```

## Integrating with Ollama

1. Open the **Settings** page in the dashboard
2. Set **Ollama Base URL** to your Ollama instance (default: `http://localhost:11434`)
3. Click **Test Connection** to verify
4. Select your default model from the dropdown
5. The Chat section will use this endpoint for completions (`POST /api/chat`)

## Integrating with OpenClaw

1. In **Settings**, set **OpenClaw Base URL** (default: `http://localhost:8080`)
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

