#!/usr/bin/env python3
"""
Server Monitoring Dashboard - Python/Flask
kenalipaslon.online/mon2
"""

from flask import Flask, render_template_string, jsonify
import psutil
import platform
import datetime
import socket

app = Flask(__name__)

def get_size(bytes_value):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"

def get_status_color(percent):
    """Return color based on percentage"""
    if percent < 50:
        return '#22c55e'
    elif percent < 80:
        return '#f59e0b'
    return '#ef4444'

def get_uptime():
    """Get system uptime"""
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    now = datetime.datetime.now()
    delta = now - boot_time
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"

def to_mhz(value):
    """Normalize frequency to MHz. psutil may return GHz (< 100) or MHz (>= 100)."""
    if value < 100:
        return round(value * 1000, 0)
    return round(value, 0)

def get_cpu_freq_mhz():
    """Read per-core MHz from /proc/cpuinfo for accuracy."""
    freqs = []
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('cpu MHz'):
                    mhz = float(line.split(':')[1].strip())
                    freqs.append(round(mhz, 0))
    except:
        pass
    return freqs

@app.route('/api/realtime')
def api_realtime():
    """API endpoint for real-time data"""
    cpu_percent_per_core = psutil.cpu_percent(percpu=True)
    cpu_freq_current = psutil.cpu_freq()

    # Read actual MHz from /proc/cpuinfo
    core_mhz = get_cpu_freq_mhz()
    freq_max = to_mhz(cpu_freq_current.max) if cpu_freq_current else 3700
    freq_min = to_mhz(cpu_freq_current.min) if cpu_freq_current else 1200

    core_clocks = []
    for i, mhz in enumerate(core_mhz):
        core_clocks.append({
            'core': i,
            'current': mhz,
            'min': freq_min,
            'max': freq_max,
        })

    avg_mhz = round(sum(core_mhz) / len(core_mhz), 0) if core_mhz else 0

    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent()

    return jsonify({
        'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
        'cpu_percent': cpu_percent,
        'cpu_percent_per_core': cpu_percent_per_core,
        'cpu_freq_avg': avg_mhz,
        'cpu_freq_max': freq_max,
        'cpu_freq_min': freq_min,
        'core_clocks': core_clocks,
        'mem_percent': memory.percent,
        'mem_used': get_size(memory.used),
        'mem_total': get_size(memory.total),
        'server_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })

@app.route('/')
def monitor():
    # CPU Info
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    load_avg = psutil.getloadavg()
    load_str = f"{load_avg[0]:.2f} / {load_avg[1]:.2f} / {load_avg[2]:.2f}"

    # Read actual MHz
    core_mhz = get_cpu_freq_mhz()
    avg_mhz = round(sum(core_mhz) / len(core_mhz)) if core_mhz else 0
    freq_max = int(to_mhz(cpu_freq.max)) if cpu_freq else 3700
    freq_min = int(to_mhz(cpu_freq.min)) if cpu_freq else 1200

    # Memory Info
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk Info
    disk = psutil.disk_usage('/')

    # Network Info
    net_io = psutil.net_io_counters()
    connections = len(psutil.net_connections())

    # System Info
    uptime = get_uptime()
    hostname = socket.gethostname()
    server_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    os_info = f"{platform.system()} {platform.release()}"
    python_version = platform.python_version()

    # Process Info
    process_count = len(psutil.pids())

    # CPU model name
    cpu_model = "Unknown"
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if 'model name' in line:
                    cpu_model = line.split(':')[1].strip()
                    break
    except:
        pass

    html_template = '''
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Monitor (Python) - kenalipaslon.online</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; padding: 20px; }
        .header h1 {
            font-size: 2rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #a78bfa, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header .subtitle { color: #94a3b8; font-size: 0.9rem; }
        .header .badge-container { margin-top: 15px; display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
        .badge { display: inline-block; padding: 5px 15px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .badge-online { background: #22c55e; color: white; animation: pulse 2s infinite; }
        .badge-python { background: #3b82f6; color: white; }
        .badge-live { background: #ef4444; color: white; animation: pulse 1.5s infinite; font-size: 0.7rem; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3); border-color: rgba(167, 139, 250, 0.3); }
        .card-title { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
        .card-value { font-size: 2.5rem; font-weight: 700; margin-bottom: 8px; letter-spacing: -1px; }
        .card-detail { font-size: 0.85rem; color: #64748b; }
        .card-sub { font-size: 0.75rem; color: #475569; margin-top: 5px; }
        .progress-bar { background: rgba(255, 255, 255, 0.08); border-radius: 10px; height: 8px; margin-top: 15px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 10px; transition: width 0.5s ease; }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
        .info-item { background: rgba(255, 255, 255, 0.02); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); }
        .info-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
        .info-value { font-size: 0.9rem; color: #e2e8f0; word-break: break-all; }
        .footer { text-align: center; margin-top: 30px; padding: 20px; color: #475569; font-size: 0.8rem; }
        .icon { width: 18px; height: 18px; opacity: 0.8; }
        .dual-stat { display: flex; gap: 20px; margin-top: 10px; }
        .dual-stat-item { flex: 1; }
        .dual-stat-label { font-size: 0.7rem; color: #64748b; }
        .dual-stat-value { font-size: 0.9rem; color: #94a3b8; }
        .card-full { grid-column: 1 / -1; }
        .chart-container { position: relative; height: 300px; margin-top: 10px; }
        .core-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 15px; }
        .core-item {
            background: rgba(255, 255, 255, 0.04);
            border-radius: 10px;
            padding: 12px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.06);
            transition: all 0.3s ease;
        }
        .core-item:hover { border-color: rgba(96, 165, 250, 0.4); }
        .core-label { font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
        .core-clock { font-size: 1.2rem; font-weight: 700; color: #60a5fa; }
        .core-clock-unit { font-size: 0.65rem; color: #475569; }
        .core-bar { background: rgba(255, 255, 255, 0.06); border-radius: 4px; height: 4px; margin-top: 8px; overflow: hidden; }
        .core-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #60a5fa, #a78bfa); transition: width 0.5s ease; }
        .clock-summary { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px; }
        .clock-summary-item { flex: 1; min-width: 100px; text-align: center; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 10px; }
        .clock-summary-label { font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }
        .clock-summary-value { font-size: 1.4rem; font-weight: 700; margin-top: 4px; }
        .live-dot { width: 8px; height: 8px; background: #ef4444; border-radius: 50%; display: inline-block; animation: pulse 1s infinite; margin-right: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Server Monitor</h1>
            <div class="subtitle">kenalipaslon.online/mon2</div>
            <div class="badge-container">
                <span class="badge badge-online">ONLINE</span>
                <span class="badge badge-python">Python {{ python_version }}</span>
                <span class="badge badge-live"><span class="live-dot"></span>LIVE</span>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>
                    CPU Usage
                </div>
                <div class="card-value" id="cpu-percent" style="color: {{ cpu_color }}">{{ cpu_percent }}%</div>
                <div class="card-detail" id="cpu-detail">{{ cpu_count }} cores @ {{ avg_mhz }} MHz</div>
                <div class="card-sub">Load: {{ load_str }}</div>
                <div class="progress-bar"><div class="progress-fill" id="cpu-bar" style="width: {{ cpu_percent }}%; background: {{ cpu_color }}"></div></div>
            </div>

            <div class="card">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
                    Memory Usage
                </div>
                <div class="card-value" id="mem-percent" style="color: {{ mem_color }}">{{ mem_percent }}%</div>
                <div class="card-detail" id="mem-detail">{{ mem_used }} / {{ mem_total }}</div>
                <div class="card-sub">Available: {{ mem_available }}</div>
                <div class="progress-bar"><div class="progress-fill" id="mem-bar" style="width: {{ mem_percent }}%; background: {{ mem_color }}"></div></div>
            </div>

            <div class="card">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/></svg>
                    Disk Usage
                </div>
                <div class="card-value" style="color: {{ disk_color }}">{{ disk_percent }}%</div>
                <div class="card-detail">{{ disk_used }} / {{ disk_total }}</div>
                <div class="card-sub">Free: {{ disk_free }}</div>
                <div class="progress-bar"><div class="progress-fill" style="width: {{ disk_percent }}%; background: {{ disk_color }}"></div></div>
            </div>

            <div class="card">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    Uptime
                </div>
                <div class="card-value" style="color: #a78bfa">{{ uptime }}</div>
                <div class="card-detail">Since last restart</div>
                <div class="card-sub">{{ process_count }} processes running</div>
            </div>
        </div>

        <!-- CPU Clock Per Core Card -->
        <div class="grid">
            <div class="card card-full">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    CPU Clock Speed <span class="badge badge-live" style="margin-left:8px;font-size:0.6rem;padding:2px 8px;"><span class="live-dot"></span>REAL-TIME</span>
                </div>
                <div class="card-sub" style="margin-bottom:10px;">{{ cpu_model }}</div>
                <div class="clock-summary">
                    <div class="clock-summary-item">
                        <div class="clock-summary-label">Current Avg</div>
                        <div class="clock-summary-value" id="clock-avg" style="color:#60a5fa;">{{ avg_mhz }} MHz</div>
                    </div>
                    <div class="clock-summary-item">
                        <div class="clock-summary-label">Base Clock</div>
                        <div class="clock-summary-value" style="color:#22c55e;">2700 MHz</div>
                    </div>
                    <div class="clock-summary-item">
                        <div class="clock-summary-label">Max Turbo</div>
                        <div class="clock-summary-value" style="color:#f59e0b;">{{ freq_max }} MHz</div>
                    </div>
                    <div class="clock-summary-item">
                        <div class="clock-summary-label">Min Clock</div>
                        <div class="clock-summary-value" style="color:#94a3b8;">{{ freq_min }} MHz</div>
                    </div>
                </div>
                <div class="core-grid" id="core-grid">
                </div>
            </div>
        </div>

        <!-- Real-time Clock Chart -->
        <div class="grid">
            <div class="card card-full">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                    CPU Clock History <span class="badge badge-live" style="margin-left:8px;font-size:0.6rem;padding:2px 8px;"><span class="live-dot"></span>LIVE</span>
                </div>
                <div class="card-sub">Clock speed per core (MHz) - Updated every 2 seconds</div>
                <div class="chart-container">
                    <canvas id="clockChart"></canvas>
                </div>
            </div>
        </div>

        <!-- CPU & Memory Usage Chart -->
        <div class="grid">
            <div class="card card-full">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                    CPU & Memory Usage History <span class="badge badge-live" style="margin-left:8px;font-size:0.6rem;padding:2px 8px;"><span class="live-dot"></span>LIVE</span>
                </div>
                <div class="card-sub">Usage percentage - Updated every 2 seconds</div>
                <div class="chart-container">
                    <canvas id="usageChart"></canvas>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
                    Swap Memory
                </div>
                <div class="card-value" style="color: {{ swap_color }}">{{ swap_percent }}%</div>
                <div class="card-detail">{{ swap_used }} / {{ swap_total }}</div>
                <div class="progress-bar"><div class="progress-fill" style="width: {{ swap_percent }}%; background: {{ swap_color }}"></div></div>
            </div>

            <div class="card">
                <div class="card-title">
                    <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    Network I/O
                </div>
                <div class="card-value" style="color: #60a5fa">{{ connections }}</div>
                <div class="card-detail">Active connections</div>
                <div class="dual-stat">
                    <div class="dual-stat-item"><div class="dual-stat-label">Sent</div><div class="dual-stat-value">{{ net_sent }}</div></div>
                    <div class="dual-stat-item"><div class="dual-stat-label">Received</div><div class="dual-stat-value">{{ net_recv }}</div></div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">
                <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2"/></svg>
                Server Information
            </div>
            <div class="info-grid">
                <div class="info-item"><div class="info-label">Hostname</div><div class="info-value">{{ hostname }}</div></div>
                <div class="info-item"><div class="info-label">Operating System</div><div class="info-value">{{ os_info }}</div></div>
                <div class="info-item"><div class="info-label">CPU Model</div><div class="info-value">{{ cpu_model }}</div></div>
                <div class="info-item"><div class="info-label">Python Version</div><div class="info-value">{{ python_version }}</div></div>
                <div class="info-item"><div class="info-label">Server Time</div><div class="info-value" id="server-time">{{ server_time }}</div></div>
                <div class="info-item"><div class="info-label">Architecture</div><div class="info-value">{{ arch }}</div></div>
                <div class="info-item"><div class="info-label">CPU Cores</div><div class="info-value">{{ cpu_count }} threads ({{ cpu_count // 2 }} cores)</div></div>
            </div>
        </div>

        <div class="footer">
            <div>Last updated: <span id="last-update">{{ server_time }}</span></div>
            <div style="margin-top: 5px; font-size: 0.75rem;">Real-time update every 2 seconds | Powered by Python & psutil</div>
        </div>
    </div>

    <script>
        var MAX_POINTS = 60;
        var API_BASE = window.location.pathname.replace(/\/+$/, '');
        var CORE_COLORS = [
            '#ef4444', '#f59e0b', '#22c55e', '#06b6d4',
            '#3b82f6', '#8b5cf6', '#ec4899', '#f97316'
        ];

        var labels = [];

        // Clock Chart
        var clockCtx = document.getElementById('clockChart').getContext('2d');
        var clockDatasets = [];
        for (var i = 0; i < {{ cpu_count }}; i++) {
            clockDatasets.push({
                label: 'Core ' + i,
                data: [],
                borderColor: CORE_COLORS[i % CORE_COLORS.length],
                backgroundColor: CORE_COLORS[i % CORE_COLORS.length] + '20',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.3,
                fill: false,
            });
        }
        var clockChart = new Chart(clockCtx, {
            type: 'line',
            data: { labels: labels, datasets: clockDatasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 300 },
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { labels: { color: '#94a3b8', usePointStyle: true, pointStyle: 'circle', font: { size: 11 } } },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#e2e8f0', bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1,
                        callbacks: { label: function(ctx) { return ctx.dataset.label + ': ' + ctx.parsed.y + ' MHz'; } }
                    }
                },
                scales: {
                    x: { ticks: { color: '#475569', maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.03)' } },
                    y: { min: 0, max: {{ freq_max }} + 200,
                        ticks: { color: '#475569', callback: function(v) { return v + ' MHz'; } },
                        grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });

        // Usage Chart
        var usageCtx = document.getElementById('usageChart').getContext('2d');
        var usageChart = new Chart(usageCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'CPU %', data: [], borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.1)', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: true },
                    { label: 'Memory %', data: [], borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.1)', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: true }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                animation: { duration: 300 },
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { labels: { color: '#94a3b8', usePointStyle: true, pointStyle: 'circle', font: { size: 11 } } },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#e2e8f0', bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1,
                        callbacks: { label: function(ctx) { return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(1) + '%'; } }
                    }
                },
                scales: {
                    x: { ticks: { color: '#475569', maxTicksLimit: 10 }, grid: { color: 'rgba(255,255,255,0.03)' } },
                    y: { min: 0, max: 100,
                        ticks: { color: '#475569', callback: function(v) { return v + '%'; } },
                        grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });

        function getColor(percent) {
            if (percent < 50) return '#22c55e';
            if (percent < 80) return '#f59e0b';
            return '#ef4444';
        }

        function updateCoreGrid(coreClocks, maxFreq) {
            var grid = document.getElementById('core-grid');
            var html = '';
            coreClocks.forEach(function(core) {
                var pct = (core.current / maxFreq * 100).toFixed(0);
                var ghz = (core.current / 1000).toFixed(2);
                html += '<div class="core-item">' +
                    '<div class="core-label">Core ' + core.core + '</div>' +
                    '<div class="core-clock">' + ghz + '</div>' +
                    '<div class="core-clock-unit">GHz (' + Math.round(core.current) + ' MHz)</div>' +
                    '<div class="core-bar"><div class="core-bar-fill" style="width:' + pct + '%"></div></div></div>';
            });
            grid.innerHTML = html;
        }

        function fetchData() {
            fetch(API_BASE + '/api/realtime')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    labels.push(data.timestamp);
                    if (labels.length > MAX_POINTS) labels.shift();

                    data.core_clocks.forEach(function(core, i) {
                        if (clockChart.data.datasets[i]) {
                            clockChart.data.datasets[i].data.push(core.current);
                            if (clockChart.data.datasets[i].data.length > MAX_POINTS)
                                clockChart.data.datasets[i].data.shift();
                        }
                    });
                    clockChart.update('none');

                    usageChart.data.datasets[0].data.push(data.cpu_percent);
                    usageChart.data.datasets[1].data.push(data.mem_percent);
                    if (usageChart.data.datasets[0].data.length > MAX_POINTS) {
                        usageChart.data.datasets[0].data.shift();
                        usageChart.data.datasets[1].data.shift();
                    }
                    usageChart.update('none');

                    updateCoreGrid(data.core_clocks, data.cpu_freq_max);
                    document.getElementById('clock-avg').textContent = Math.round(data.cpu_freq_avg) + ' MHz';

                    var cpuEl = document.getElementById('cpu-percent');
                    cpuEl.textContent = data.cpu_percent.toFixed(1) + '%';
                    cpuEl.style.color = getColor(data.cpu_percent);
                    document.getElementById('cpu-bar').style.width = data.cpu_percent + '%';
                    document.getElementById('cpu-bar').style.background = getColor(data.cpu_percent);
                    document.getElementById('cpu-detail').textContent = data.core_clocks.length + ' cores @ ' + Math.round(data.cpu_freq_avg) + ' MHz';

                    var memEl = document.getElementById('mem-percent');
                    memEl.textContent = data.mem_percent.toFixed(1) + '%';
                    memEl.style.color = getColor(data.mem_percent);
                    document.getElementById('mem-bar').style.width = data.mem_percent + '%';
                    document.getElementById('mem-bar').style.background = getColor(data.mem_percent);
                    document.getElementById('mem-detail').textContent = data.mem_used + ' / ' + data.mem_total;

                    document.getElementById('server-time').textContent = data.server_time;
                    document.getElementById('last-update').textContent = data.server_time;
                })
                .catch(function(err) { console.error('Fetch error:', err); });
        }

        fetchData();
        setInterval(fetchData, 2000);
    </script>
</body>
</html>
'''

    return render_template_string(html_template,
        cpu_percent=cpu_percent,
        cpu_count=cpu_count,
        avg_mhz=avg_mhz,
        freq_max=freq_max,
        freq_min=freq_min,
        cpu_color=get_status_color(cpu_percent),
        cpu_model=cpu_model,
        load_str=load_str,
        mem_percent=memory.percent,
        mem_used=get_size(memory.used),
        mem_total=get_size(memory.total),
        mem_available=get_size(memory.available),
        mem_color=get_status_color(memory.percent),
        swap_percent=swap.percent,
        swap_used=get_size(swap.used),
        swap_total=get_size(swap.total),
        swap_color=get_status_color(swap.percent),
        disk_percent=disk.percent,
        disk_used=get_size(disk.used),
        disk_total=get_size(disk.total),
        disk_free=get_size(disk.free),
        disk_color=get_status_color(disk.percent),
        uptime=uptime,
        hostname=hostname,
        server_time=server_time,
        os_info=os_info,
        python_version=python_version,
        arch=platform.machine(),
        connections=connections,
        net_sent=get_size(net_io.bytes_sent),
        net_recv=get_size(net_io.bytes_recv),
        process_count=process_count
    )

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
