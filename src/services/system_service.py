import socket
import subprocess


def get_local_ip():
    """IP de salida de la Pi en la red local. No envia datos, solo abre un socket UDP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return None


def get_cpu_temp_c():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", encoding="utf-8") as f:
            milli = int(f.read().strip())
        return round(milli / 1000, 1)
    except (OSError, ValueError):
        return None


def get_memory_usage():
    try:
        info = {}
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                key, _, rest = line.partition(":")
                value = rest.strip().split()[0]
                info[key] = int(value)

        total = info.get("MemTotal", 0)
        available = info.get("MemAvailable", 0)
        if not total:
            return None
        used = total - available
        return {
            "total_mb": total // 1024,
            "used_mb": used // 1024,
            "percent": round(used / total * 100, 1),
        }
    except (OSError, ValueError, IndexError):
        return None


def get_uptime():
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            seconds = float(f.read().split()[0])
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    except (OSError, ValueError):
        return None


def shutdown():
    subprocess.Popen(["shutdown", "-h", "now"])


def reboot():
    subprocess.Popen(["reboot"])
