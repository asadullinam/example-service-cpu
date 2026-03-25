#!/usr/bin/env python3
import json
import math
import multiprocessing
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = int(os.getenv("PORT", "8080"))
DEFAULT_SECONDS = 5
DEFAULT_WORKERS = 1
MAX_SECONDS = 60
MAX_WORKERS = 8


def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def cpu_worker(duration_seconds: int, result_queue: multiprocessing.Queue) -> None:
    deadline = time.perf_counter() + duration_seconds
    candidate = 10_000_019
    primes_found = 0
    iterations = 0

    while time.perf_counter() < deadline:
        limit = math.isqrt(candidate)
        is_prime = True
        divisor = 3
        while divisor <= limit:
            if candidate % divisor == 0:
                is_prime = False
                break
            divisor += 2
        if is_prime:
            primes_found += 1
        iterations += 1
        candidate += 2

    result_queue.put(
        {
            "iterations": iterations,
            "primesFound": primes_found,
            "lastCandidate": candidate,
        }
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "example-service-cpu/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self.send_json(
                200,
                {
                    "status": "ok",
                    "service": "example-service-cpu",
                },
            )
            return

        if parsed.path == "/cpu":
            params = parse_qs(parsed.query)
            seconds = clamp(
                int(params.get("seconds", [DEFAULT_SECONDS])[0]),
                1,
                MAX_SECONDS,
            )
            workers = clamp(
                int(params.get("workers", [DEFAULT_WORKERS])[0]),
                1,
                MAX_WORKERS,
            )

            started_at = time.time()
            queue: multiprocessing.Queue = multiprocessing.Queue()
            processes = [
                multiprocessing.Process(target=cpu_worker, args=(seconds, queue))
                for _ in range(workers)
            ]

            for process in processes:
                process.start()

            results = []
            for _ in processes:
                results.append(queue.get())

            for process in processes:
                process.join()

            elapsed = round(time.time() - started_at, 3)
            self.send_json(
                200,
                {
                    "status": "completed",
                    "seconds": seconds,
                    "workers": workers,
                    "elapsedSeconds": elapsed,
                    "hostCpuCount": os.cpu_count(),
                    "results": results,
                    "hint": "Increase workers or seconds to keep the container near its CPU quota.",
                },
            )
            return

        self.send_json(
            200,
            {
                "service": "example-service-cpu",
                "endpoints": {
                    "/healthz": "liveness endpoint",
                    "/cpu?seconds=10&workers=2": "run CPU-bound prime-search workers",
                },
            },
        )

    def log_message(self, format: str, *args) -> None:
        return

    def send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((DEFAULT_HOST, DEFAULT_PORT), Handler)
    print(f"example-service-cpu listening on {DEFAULT_HOST}:{DEFAULT_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
