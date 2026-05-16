import time
import random
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logs.generate_sample_logs import generate_live_log_line

LOG_FILE    = os.path.join(os.path.dirname(__file__), "live_access.log")
WRITE_INTERVAL_SECS = 2
LOGS_PER_TICK       = random.randint(1, 5)


def stream_logs():
    print(f"SentinelLog — Live Log Streamer")
    print(f"Writing to: {LOG_FILE}")
    print(f"Interval  : every {WRITE_INTERVAL_SECS}s")
    print(f"Press Ctrl+C to stop\n")

    total_written = 0

    with open(LOG_FILE, "a") as f:
        while True:
            batch = random.randint(1, 8)
            for _ in range(batch):
                line = generate_live_log_line()
                f.write(line)
                total_written += 1

            f.flush()
            print(f"[{total_written:>6} logs written] +{batch} this tick", end="\r")
            time.sleep(WRITE_INTERVAL_SECS)


if __name__ == "__main__":
    try:
        stream_logs()
    except KeyboardInterrupt:
        print(f"\nStreamer stopped.")