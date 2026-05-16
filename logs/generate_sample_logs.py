import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# ── Config ────────────────────────────────────────────────
TOTAL_LOGS     = 5000
ATTACK_RATIO   = 0.08
OUTPUT_DIR     = os.path.dirname(os.path.abspath(__file__))

# ── IP pools ──────────────────────────────────────────────
NORMAL_IPS = [fake.ipv4() for _ in range(80)]
ATTACK_IPS = [fake.ipv4() for _ in range(15)]

# ── Endpoints ─────────────────────────────────────────────
NORMAL_ENDPOINTS = [
    "/", "/home", "/about", "/contact",
    "/api/crop", "/api/weather", "/api/market",
    "/api/disease", "/api/fertilizer",
    "/static/main.js", "/static/style.css",
    "/favicon.ico", "/robots.txt",
]

ATTACK_ENDPOINTS = [
    "/admin", "/admin/login", "/wp-login.php",
    "/.env", "/.git/config", "/phpmyadmin",
    "/api/users?id=1' OR '1'='1",
    "/api/admin?cmd=ls",
    "/config.php", "/backup.sql",
    "/shell.php", "/../../../etc/passwd",
]

# ── User agents ───────────────────────────────────────────
NORMAL_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

ATTACK_AGENTS = [
    "sqlmap/1.6#stable (https://sqlmap.org)",
    "Nikto/2.1.6",
    "python-requests/2.28.0",
    "curl/7.68.0",
    "masscan/1.3.2",
    "nmap scripting engine",
    "zgrab/0.x",
]

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE"]


# ── Log generators ────────────────────────────────────────

def random_timestamp(minutes_back=1440):
    delta = timedelta(minutes=random.randint(0, minutes_back))
    return (datetime.now() - delta).strftime("%d/%b/%Y:%H:%M:%S +0000")

def make_normal_log():
    status = random.choices(
        [200, 200, 200, 301, 304, 404, 500],
        weights=[60, 10, 10, 5, 5, 8, 2]
    )[0]
    return {
        "ip":            random.choice(NORMAL_IPS),
        "timestamp":     random_timestamp(),
        "method":        random.choice(["GET", "GET", "GET", "POST"]),
        "endpoint":      random.choice(NORMAL_ENDPOINTS),
        "status_code":   status,
        "payload_size":  random.randint(300, 8000),
        "user_agent":    random.choice(NORMAL_AGENTS),
        "response_time": round(random.uniform(0.05, 1.2), 3),
    }

def make_brute_force_log():
    return {
        "ip":            random.choice(ATTACK_IPS),
        "timestamp":     random_timestamp(minutes_back=60),
        "method":        "POST",
        "endpoint":      random.choice(["/admin/login", "/wp-login.php", "/api/auth/login"]),
        "status_code":   random.choice([401, 401, 403, 200]),
        "payload_size":  random.randint(50, 300),
        "user_agent":    random.choice(ATTACK_AGENTS),
        "response_time": round(random.uniform(0.01, 0.15), 3),
    }

def make_sql_injection_log():
    return {
        "ip":            random.choice(ATTACK_IPS),
        "timestamp":     random_timestamp(minutes_back=120),
        "method":        "GET",
        "endpoint":      random.choice([
            "/api/users?id=1' OR '1'='1",
            "/search?q='; DROP TABLE users;--",
            "/api/data?filter=1 UNION SELECT * FROM users",
        ]),
        "status_code":   random.choice([200, 500, 403]),
        "payload_size":  random.randint(5000, 80000),
        "user_agent":    "sqlmap/1.6#stable (https://sqlmap.org)",
        "response_time": round(random.uniform(2.5, 10.0), 3),
    }

def make_ddos_log():
    ip = random.choice(ATTACK_IPS)
    return {
        "ip":            ip,
        "timestamp":     random_timestamp(minutes_back=30),
        "method":        "GET",
        "endpoint":      "/",
        "status_code":   random.choice([200, 503, 503]),
        "payload_size":  random.randint(80, 400),
        "user_agent":    random.choice(ATTACK_AGENTS),
        "response_time": round(random.uniform(8.0, 45.0), 3),
    }

def make_recon_log():
    return {
        "ip":            random.choice(ATTACK_IPS),
        "timestamp":     random_timestamp(minutes_back=240),
        "method":        "GET",
        "endpoint":      random.choice(ATTACK_ENDPOINTS),
        "status_code":   random.choice([404, 403, 200]),
        "payload_size":  random.randint(100, 600),
        "user_agent":    random.choice(["Nikto/2.1.6", "nmap scripting engine", "masscan/1.3.2"]),
        "response_time": round(random.uniform(0.02, 0.3), 3),
    }

def make_data_exfil_log():
    return {
        "ip":            random.choice(ATTACK_IPS),
        "timestamp":     random_timestamp(minutes_back=180),
        "method":        "POST",
        "endpoint":      random.choice(["/api/export", "/api/backup", "/api/dump"]),
        "status_code":   random.choice([200, 200, 403]),
        "payload_size":  random.randint(500000, 5000000),
        "user_agent":    random.choice(NORMAL_AGENTS),
        "response_time": round(random.uniform(15.0, 60.0), 3),
    }


# ── Format to nginx log line ──────────────────────────────

def format_log_line(log: dict) -> str:
    return (
        f'{log["ip"]} - - [{log["timestamp"]}] '
        f'"{log["method"]} {log["endpoint"]} HTTP/1.1" '
        f'{log["status_code"]} {log["payload_size"]} '
        f'"{log["user_agent"]}" {log["response_time"]}\n'
    )


# ── Main generator ────────────────────────────────────────

ATTACK_GENERATORS = [
    make_brute_force_log,
    make_sql_injection_log,
    make_ddos_log,
    make_recon_log,
    make_data_exfil_log,
]

ATTACK_WEIGHTS = [35, 20, 20, 15, 10]

def generate_access_log(filename="sample_access.log", total=TOTAL_LOGS):
    filepath = os.path.join(OUTPUT_DIR, filename)
    attack_count = 0

    with open(filepath, "w") as f:
        for _ in range(total):
            if random.random() < ATTACK_RATIO:
                generator = random.choices(ATTACK_GENERATORS, weights=ATTACK_WEIGHTS)[0]
                log = generator()
                attack_count += 1
            else:
                log = make_normal_log()
            f.write(format_log_line(log))

    print(f"✅ Generated {total} logs → {filepath}")
    print(f"   Normal : {total - attack_count} ({(total-attack_count)/total*100:.1f}%)")
    print(f"   Attacks: {attack_count} ({attack_count/total*100:.1f}%)")
    return filepath


def generate_attack_log(filename="sample_attacks.log", total=500):
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w") as f:
        for _ in range(total):
            generator = random.choices(ATTACK_GENERATORS, weights=ATTACK_WEIGHTS)[0]
            log = generator()
            f.write(format_log_line(log))

    print(f"✅ Generated {total} pure attack logs → {filepath}")
    return filepath


def generate_live_log_line():
    """Call this in a loop to simulate real-time log streaming."""
    if random.random() < ATTACK_RATIO:
        generator = random.choices(ATTACK_GENERATORS, weights=ATTACK_WEIGHTS)[0]
        log = generator()
    else:
        log = make_normal_log()
    log["timestamp"] = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")
    return format_log_line(log)


if __name__ == "__main__":
    print("SentinelLog — Log Generator")
    print("=" * 40)
    generate_access_log("sample_access.log", total=5000)
    generate_attack_log("sample_attacks.log", total=500)
    print("\nDone! Files saved in logs/ folder.")