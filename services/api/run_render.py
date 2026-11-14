from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import uvicorn


def main() -> None:
    worker = subprocess.Popen(
        [sys.executable, "-m", "services.api.worker", "--poll-seconds", "2"],
        env=os.environ.copy(),
    )

    def stop_worker(_signum, _frame):
        if worker.poll() is None:
            worker.terminate()

    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)

    try:
        uvicorn.run(
            "services.api.app.main:app",
            host="0.0.0.0",
            port=int(os.getenv("PORT", "10000")),
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
        )
    finally:
        if worker.poll() is None:
            worker.terminate()
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait()


if __name__ == "__main__":
    main()
