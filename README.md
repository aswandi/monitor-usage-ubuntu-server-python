# Server Monitor Dashboard

Dashboard monitoring server real-time berbasis **Python + Flask + psutil**.
Menampilkan CPU usage, CPU clock per core, Memory, Disk, Network, dan Swap secara live.


![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![psutil](https://img.shields.io/badge/psutil-latest-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Fitur

- **CPU Usage** — persentase real-time per core
- **CPU Clock Speed** — MHz per core dari `/proc/cpuinfo`
- **Memory Usage** — RAM used/total/available
- **Disk Usage** — penggunaan partisi root
- **Swap Memory** — penggunaan swap
- **Network I/O** — total bytes sent/received & koneksi aktif
- **System Info** — hostname, OS, uptime, proses berjalan
- **Grafik Real-time** — Chart.js, update setiap 2 detik
  - CPU Clock history per core
  - CPU % & Memory % history

---

## Screenshot

```
┌─────────────────────────────────────────┐
│        Server Monitor Dashboard           │
│  [ONLINE] [Python 3.x] [● LIVE]          │
├──────────┬──────────┬──────────┬────────┤
│ CPU 12%  │ MEM 50%  │ DISK 60% │ Uptime │
├──────────┴──────────┴──────────┴────────┤
│  CPU Clock Speed per Core  [● REAL-TIME] │
│  Core0: 1.20 GHz  Core1: 2.60 GHz ...   │
├─────────────────────────────────────────┤
│  [Grafik Clock History]                  │
│  [Grafik CPU & Memory Usage]             │
└─────────────────────────────────────────┘
```

---

## Persyaratan

- Python 3.8+
- pip
- Linux (Ubuntu 20.04 / 22.04 / 24.04 direkomendasikan)
- Akses ke `/proc/cpuinfo`

---

## Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/aswandi/monitor-usage-ubuntu-server-golang.git
cd monitor-usage-ubuntu-server-golang
```

### 2. Buat Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependensi

```bash
pip install flask psutil gunicorn
```

### 4. Jalankan (Development)

```bash
python app.py
```

Buka browser: `http://localhost:5000`

---

## Instalasi Production (Nginx + Gunicorn)

### 5. Jalankan dengan Gunicorn

```bash
gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
```

Atau background dengan nohup:

```bash
nohup gunicorn --workers 2 --bind 127.0.0.1:5000 app:app > /var/log/monitor.log 2>&1 &
```

### 6. Konfigurasi Nginx

Jika ingin akses di subdirectory `/mon2`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /mon2/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /mon2/api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Reload Nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### 7. Systemd Service (Auto-start)

Buat file `/etc/systemd/system/server-monitor.service`:

```ini
[Unit]
Description=Server Monitor Dashboard
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/monitor-usage-ubuntu-server-golang
ExecStart=/path/to/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable dan start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable server-monitor
sudo systemctl start server-monitor
sudo systemctl status server-monitor
```

---

## API Endpoint

| Endpoint | Method | Deskripsi |
|---|---|---|
| `/` | GET | Dashboard HTML |
| `/api/realtime` | GET | Data JSON real-time |

### Contoh Response `/api/realtime`

```json
{
  "timestamp": "18:04:44",
  "cpu_percent": 12.1,
  "cpu_percent_per_core": [9.8, 9.7, 9.8, 10.2],
  "cpu_freq_avg": 1501.0,
  "cpu_freq_max": 2700.0,
  "cpu_freq_min": 1200.0,
  "core_clocks": [
    {"core": 0, "current": 1200.0, "min": 1200.0, "max": 2700.0}
  ],
  "mem_percent": 50.7,
  "mem_used": "3.57 GB",
  "mem_total": "7.64 GB",
  "server_time": "2026-02-19 18:04:44"
}
```

---

## Struktur File

```
monitor-usage-ubuntu-server-golang/
├── app.py          # Aplikasi utama Flask
└── README.md       # Dokumentasi ini
```

---

## Teknologi

| Komponen | Teknologi |
|---|---|
| Backend | Python 3, Flask |
| System Stats | psutil, /proc/cpuinfo |
| Frontend | HTML5, CSS3, Vanilla JS |
| Charts | Chart.js 4.4.0 (CDN) |
| Server | Gunicorn + Nginx |

---

## Lisensi

MIT License — bebas digunakan dan dimodifikasi.
