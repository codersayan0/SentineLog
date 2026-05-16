import random
import os
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

NORMAL_IPS = [fake.ipv4() for _ in range(50)]
ATTACK_IPS = [fake.ipv4() for _ in range(10)]

NORMAL_ENDPOINTS = ["/", "/home", "/about", "/crop", "/weather", "/market", "/api/data"]
ATTACK_ENDPOINTS = ["/admin", "/wp-login.php", "/.env", "/phpmyadmin", "/api/users", "/config"]

METHODS = ["GET", "POST", "PUT", "DELETE"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "curl/7.68.0",
    "python-requests/2.28.0",
    "sqlmap/1.6",
    "Nikto/2.1.6",
]

def generate_normal_log():
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 3600))
    return {
        "timestamp": timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000"),
        "ip": random.choice(NORMAL_IPS),
        "method": random.choice(["GET", "POST"]),
        "endpoint": random.choice(NORMAL_ENDPOINTS),
        "status_code": random.choice([200, 200, 200, 301, 304, 404]),
        "response_time": round(random.uniform(0.05, 0.8), 3),
        "payload_size": random.randint(200, 5000),
        "user_agent": random.choice(USER_AGENTS[:3]),
    }

def generate_attack_log(attack_type="random"):
    timestamp = datetime.now() - timedelta(seconds=random.randint(0, 300))

    if attack_type == "brute_force" or attack_type == "random":
        return {
            "timestamp": timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000"),
            "ip": random.choice(ATTACK_IPS),
            "method": "POST",
            "endpoint": "/admin/login",
            "status_code": random.choice([401, 403, 200]),
            "response_time": round(random.uniform(0.01, 0.1), 3),
            "payload_size": random.randint(50, 200),
            "user_agent": random.choice(USER_AGENTS[3:]),
        }
    elif attack_type == "sql_injection":
        return {
            "timestamp": timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000"),
            "ip": random.choice(ATTACK_IPS),
            "method": "GET",
            "endpoint": "/api/users?id=1' OR '1'='1",
            "status_code": random.choice([200, 500]),
            "response_time": round(random.uniform(2.0, 8.0), 3),
            "payload_size": random.randint(5000, 50000),
            "user_agent": "sqlmap/1.6",
        }
    elif attack_type == "ddos":
        return {
            "timestamp": timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000"),
            "ip": random.choice(ATTACK_IPS),
            "method": "GET",
            "endpoint": "/",
            "status_code": random.choice([200, 503]),
            "response_time": round(random.uniform(5.0, 30.0), 3),
            "payload_size": random.randint(100, 500),
            "user_agent": "python-requests/2.28.0",
        }

def generate_log_file(filepath="logs/sample_access.log", total=1000, attack_ratio=0.08):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    attack_types = ["brute_force", "sql_injection", "ddos"]
    
    with open(filepath, "w") as f:
        for _ in range(total):
            if random.random() < attack_ratio:
                log = generate_attack_log(random.choice(attack_types))
            else:
                log = generate_normal_log()

            line = (
                f'{log["ip"]} - - [{log["timestamp"]}] '
                f'"{log["method"]} {log["endpoint"]} HTTP/1.1" '
                f'{log["status_code"]} {log["payload_size"]} '
                f'"{log["user_agent"]}" {log["response_time"]}\n'
            )
            f.write(line)

    print(f"Generated {total} log entries at {filepath}")

if __name__ == "__main__":
    generate_log_file()