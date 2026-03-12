from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psutil
import os
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_sys_file(path):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read().strip()
    except Exception:
        return None
    return None

boot_time = psutil.boot_time()

@app.get("/stats")
def get_hardware_stats():
    cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    cpu_total = sum(cpu_percent_per_core) / len(cpu_percent_per_core) if cpu_percent_per_core else 0
    load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
    
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory() # This is the ZRAM on phone
    disk = psutil.disk_usage('/')
    disk_io = psutil.disk_io_counters()
    net = psutil.net_io_counters()

    # Battery
    batt_level = read_sys_file('/sys/class/power_supply/battery/capacity') or "100"
    batt_voltage = read_sys_file('/sys/class/power_supply/battery/voltage_now')
    batt_voltage = str(round(int(batt_voltage) / 1000000, 2)) + "V" if batt_voltage else "N/A"

    # Thermals
    temp_raw = read_sys_file('/sys/class/thermal/thermal_zone0/temp')
    cpu_temp = str(round(int(temp_raw) / 1000, 1)) if temp_raw else "40.0"

    # Hardware IIO Sensors (Graceful fallback if paths vary)
    lux = read_sys_file('/sys/bus/iio/devices/iio:device0/in_illuminance_raw') or "N/A"

    return {
        "system": {
            "uptime_seconds": time.time() - boot_time,
            "load_avg": [round(x, 2) for x in load_avg]
        },
        "compute": {
            "total_percent": round(cpu_total),
            "cores": cpu_percent_per_core
        },
        "memory": {
            "ram_used_gb": round(mem.used / (1024**3), 1),
            "ram_total_gb": round(mem.total / (1024**3), 1),
            "ram_percent": mem.percent,
            "zram_used_mb": round(swap.used / (1024**2)),
            "zram_total_mb": round(swap.total / (1024**2)),
            "zram_percent": swap.percent
        },
        "storage": {
            "root_used_gb": round(disk.used / (1024**3), 1),
            "root_total_gb": round(disk.total / (1024**3), 1),
            "root_percent": disk.percent,
            "bytes_read": disk_io.read_bytes if disk_io else 0,
            "bytes_written": disk_io.write_bytes if disk_io else 0
        },
        "network": {
            "bytes_recv": net.bytes_recv,
            "bytes_sent": net.bytes_sent
        },
        "power": {
            "level": batt_level,
            "voltage": batt_voltage
        },
        "thermals": {
            "cpu_celsius": cpu_temp
        },
        "sensors": {
            "lux": lux
        }
    }