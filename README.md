# 📱 Beryllium Core: Mobile Bare-Metal Server

Transforming a retired smartphone into a fully functional, bare-metal Linux server and live telemetry dashboard.

## 🚀 The Vision
E-waste is a massive problem in the tech industry. Older flagship phones possess incredible hardware—often more powerful than standard Raspberry Pis—but are abandoned due to dead batteries or cracked screens. 

This project breathes new life into a retired Xiaomi Poco F1 (code-named *Beryllium*). By stripping away Android and flashing a bare-metal Linux kernel, I repurposed its Snapdragon 845 processor, LPDDR4X RAM, and UFS 2.1 storage into a secure, 24/7 private server.

## 🏗️ Architecture & Tech Stack

* **Hardware:** Xiaomi Poco F1 (Snapdragon 845, 256GB UFS 2.1, ZRAM).
* **Operating System:** postmarketOS (Alpine Linux based) directly interfaced with the device's bootloader.
* **Networking:** Tailscale (WireGuard) zero-trust mesh VPN.
* **Public Bridge:** Tailscale Funnel securely exposes the API to the public internet via Let's Encrypt SSL.
* **Backend API:** Python, FastAPI, and Uvicorn. The API reads raw Linux `/sys/` and `/proc/` files to monitor physical hardware telemetry in real-time.
* **Frontend:** HTML, TailwindCSS, and Chart.js. Deployed via a CI/CD pipeline to GitHub Pages.

## ⚡ Features
* **Live Hardware Telemetry:** Streams CPU per-core loads, SoC thermals, and memory usage.
* **Mobile-Specific Sensors:** Monitors battery UPS voltage and ambient light sensors via Linux IIO drivers.
* **ZRAM & Storage Metrics:** Tracks live Disk I/O speeds and compressed ZRAM swap usage.
* **Bento-Box UI:** A modern, highly responsive glassmorphism dashboard.
* **Secure Public Access:** Bypasses NAT and firewall restrictions using encrypted tunnels, allowing public viewing of the telemetry without exposing SSH access.

## 🛠️ How It Works
1. The Poco F1 runs headless, connected to power and Wi-Fi.
2. A Python FastAPI service runs permanently in the background via `systemd`.
3. The API translates physical hardware states into a JSON stream.
4. Tailscale Funnel grabs this local port and broadcasts it securely to a public HTTPS URL.
5. The GitHub Pages frontend fetches the JSON and renders the UI at 60fps.

## ACCESS IT HERE
[link](https://suberkhazi.github.io/Poco_Dashboard/)

## 💡 What I Learned
Building this required diving deep into Linux file systems, writing custom systemd daemon services, navigating complex CORS and Private Network Access (PNA) browser security policies, and managing internal DNS routing over a mesh VPN. It proved that cloud computing doesn't always have to happen in a data center—sometimes it's sitting right on your desk.