from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psutil
import os
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://poco-f1-pmos.tailbbba48.ts.net:10000/stats"],
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

def read_iio_scaled(raw_path, scale_path):
    try:
        raw = read_sys_file(raw_path)
        scale = read_sys_file(scale_path)
        if raw and scale:
            return round(float(raw) * float(scale), 2)
    except Exception:
        return None
    return None

THERMAL_ZONES = {
    "aoss0":    "/sys/class/thermal/thermal_zone0/temp",
    "cpu0":     "/sys/class/thermal/thermal_zone1/temp",
    "cpu7":     "/sys/class/thermal/thermal_zone2/temp",
    "gpu_top":  "/sys/class/thermal/thermal_zone3/temp",
    "gpu_bot":  "/sys/class/thermal/thermal_zone4/temp",
    "aoss1":    "/sys/class/thermal/thermal_zone5/temp",
    "modem":    "/sys/class/thermal/thermal_zone6/temp",
    "mem":      "/sys/class/thermal/thermal_zone7/temp",
    "wlan":     "/sys/class/thermal/thermal_zone8/temp",
    "camera":   "/sys/class/thermal/thermal_zone10/temp",
    "pm8998":   "/sys/class/thermal/thermal_zone14/temp",
    "cluster0": "/sys/class/thermal/thermal_zone18/temp",
    "cluster1": "/sys/class/thermal/thermal_zone19/temp",
}

SKIP_IFACES = {'lo', 'rmnet_ipa0', 'usb0'}

boot_time = psutil.boot_time()
# Prime cpu_percent so first call returns real values
psutil.cpu_percent(interval=None, percpu=True)

@app.get("/stats")
def get_hardware_stats():
    cpu_percent_per_core = psutil.cpu_percent(interval=None, percpu=True)
    cpu_total = round(sum(cpu_percent_per_core) / len(cpu_percent_per_core), 1) if cpu_percent_per_core else 0
    load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage('/')
    disk_io = psutil.disk_io_counters()
    net_total = psutil.net_io_counters()

    # Per-interface (only active ones)
    net_ifaces = {}
    try:
        for iface, stats in psutil.net_io_counters(pernic=True).items():
            if iface in SKIP_IFACES:
                continue
            net_ifaces[iface] = {
                "bytes_recv": stats.bytes_recv,
                "bytes_sent": stats.bytes_sent,
                "packets_recv": stats.packets_recv,
                "packets_sent": stats.packets_sent,
            }
    except Exception:
        pass

    # Top processes via psutil (works on busybox)
    proc_count = 0
    top_procs = []
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = p.info
                procs.append({
                    "pid": info['pid'],
                    "name": (info['name'] or '')[:18],
                    "cpu": round(info['cpu_percent'] or 0, 1),
                    "mem": round(info['memory_percent'] or 0, 1),
                })
            except Exception:
                pass
        proc_count = len(procs)
        top_procs = sorted(procs, key=lambda x: x['cpu'], reverse=True)[:8]
    except Exception:
        pass

    # Battery
    batt_level   = read_sys_file('/sys/class/power_supply/qcom-battery/capacity') or "N/A"
    batt_status  = read_sys_file('/sys/class/power_supply/qcom-battery/status') or "N/A"
    batt_tech    = read_sys_file('/sys/class/power_supply/qcom-battery/technology') or "N/A"

    batt_voltage_raw = read_sys_file('/sys/class/power_supply/qcom-battery/voltage_now')
    batt_voltage = round(int(batt_voltage_raw) / 1_000_000, 3) if batt_voltage_raw else None

    # Current: negative = discharging, positive = charging
    batt_current_raw = read_sys_file('/sys/class/power_supply/qcom-battery/current_now')
    batt_current_ma = round(int(batt_current_raw) / 1000, 1) if batt_current_raw else None

    batt_temp_raw = read_sys_file('/sys/class/power_supply/qcom-battery/temp')
    batt_temp = round(int(batt_temp_raw) / 10, 1) if batt_temp_raw else None

    charge_full_raw = read_sys_file('/sys/class/power_supply/qcom-battery/charge_full_design')
    charge_full_mah = round(int(charge_full_raw) / 1000) if charge_full_raw else None

    volt_max_raw = read_sys_file('/sys/class/power_supply/qcom-battery/voltage_max_design')
    volt_max = round(int(volt_max_raw) / 1_000_000, 2) if volt_max_raw else None

    # IIO device0 — die temp
    iio0_raw = read_sys_file('/sys/bus/iio/devices/iio:device0/in_temp_die_temp_input')
    iio0_die_temp = round(int(iio0_raw) / 1000, 1) if iio0_raw else None

    # IIO device1 — fuel gauge
    iio1_i0   = read_iio_scaled('/sys/bus/iio/devices/iio:device1/in_current0_raw',    '/sys/bus/iio/devices/iio:device1/in_current0_scale')
    iio1_i1   = read_iio_scaled('/sys/bus/iio/devices/iio:device1/in_current1_raw',    '/sys/bus/iio/devices/iio:device1/in_current1_scale')
    iio1_v0   = read_iio_scaled('/sys/bus/iio/devices/iio:device1/in_voltage0_raw',    '/sys/bus/iio/devices/iio:device1/in_voltage0_scale')
    iio1_temp = read_iio_scaled('/sys/bus/iio/devices/iio:device1/in_temp0_raw',       '/sys/bus/iio/devices/iio:device1/in_temp0_scale')

    # Thermals
    thermals = {}
    for name, path in THERMAL_ZONES.items():
        val = read_sys_file(path)
        thermals[name] = round(int(val) / 1000, 1) if val else None

    return {
        "system": {
            "uptime_seconds": round(time.time() - boot_time),
            "load_avg": [round(x, 2) for x in load_avg],
            "proc_count": proc_count,
            "top_procs": top_procs,
        },
        "compute": {
            "total_percent": cpu_total,
            "cores": cpu_percent_per_core,
        },
        "memory": {
            "ram_used_gb": round(mem.used / (1024**3), 1),
            "ram_total_gb": round(mem.total / (1024**3), 1),
            "ram_percent": mem.percent,
            "ram_available_gb": round(mem.available / (1024**3), 1),
            "zram_used_mb": round(swap.used / (1024**2)),
            "zram_total_mb": round(swap.total / (1024**2)),
            "zram_percent": swap.percent,
        },
        "storage": {
            "root_used_gb": round(disk.used / (1024**3), 1),
            "root_total_gb": round(disk.total / (1024**3), 1),
            "root_free_gb": round(disk.free / (1024**3), 1),
            "root_percent": disk.percent,
            "bytes_read": disk_io.read_bytes if disk_io else 0,
            "bytes_written": disk_io.write_bytes if disk_io else 0,
        },
        "network": {
            "bytes_recv": net_total.bytes_recv,
            "bytes_sent": net_total.bytes_sent,
            "interfaces": net_ifaces,
        },
        "power": {
            "level_percent": batt_level,
            "status": batt_status,
            "technology": batt_tech,
            "voltage_v": batt_voltage,
            "current_ma": batt_current_ma,
            "temp_celsius": batt_temp,
            "design_capacity_mah": charge_full_mah,
            "max_voltage_v": volt_max,
        },
        "thermals": thermals,
        "iio": {
            "die_temp_celsius": iio0_die_temp,
            "fuel_gauge": {
                "current0_ma": iio1_i0,
                "current1_ma": iio1_i1,
                "voltage0_mv": iio1_v0,
                "temp_celsius": iio1_temp,
            }
        }
    }
