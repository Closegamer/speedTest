#!/usr/bin/env python3
"""Simple internet speed tester: downloads a URL N times and reports average speed."""

import argparse
import sys
import time
from dataclasses import dataclass

import requests

DEFAULT_URL = "https://speed.hetzner.de/100MB.bin"
CHUNK_SIZE = 64 * 1024
MB = 1024 * 1024


@dataclass
class RequestResult:
    seconds: float
    bytes_downloaded: int


def download_once(url: str, timeout: float) -> RequestResult:
    start = time.perf_counter()
    bytes_downloaded = 0
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            bytes_downloaded += len(chunk)
    elapsed = time.perf_counter() - start
    return RequestResult(seconds=elapsed, bytes_downloaded=bytes_downloaded)


def run_speed_test(url: str, count: int, timeout: float) -> list[RequestResult]:
    results: list[RequestResult] = []
    for i in range(1, count + 1):
        try:
            result = download_once(url, timeout)
        except requests.RequestException as exc:
            print(f"  [{i}/{count}] ошибка: {exc}", file=sys.stderr)
            continue
        speed_mb_s = (result.bytes_downloaded / MB) / result.seconds
        print(
            f"  [{i}/{count}] {result.bytes_downloaded / MB:8.2f} MB "
            f"за {result.seconds:6.2f} с -> {speed_mb_s:6.2f} MB/s"
        )
        results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Измеряет скорость интернет-соединения серией HTTP-запросов.")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help=f"URL файла для скачивания (по умолчанию: {DEFAULT_URL})")
    parser.add_argument("-n", "--count", type=int, default=10, help="количество запросов (по умолчанию: 10)")
    parser.add_argument("-t", "--timeout", type=float, default=30.0, help="таймаут одного запроса в секундах (по умолчанию: 30)")
    args = parser.parse_args()

    print(f"Тестируем скорость: {args.url}")
    print(f"Запросов: {args.count}\n")

    results = run_speed_test(args.url, args.count, args.timeout)

    if not results:
        print("\nНи один запрос не завершился успешно.", file=sys.stderr)
        sys.exit(1)

    total_bytes = sum(r.bytes_downloaded for r in results)
    total_seconds = sum(r.seconds for r in results)
    avg_seconds = total_seconds / len(results)
    avg_speed_mb_s = (total_bytes / MB) / total_seconds

    print("\nИтог:")
    print(f"  Успешных запросов:      {len(results)}/{args.count}")
    print(f"  Скачано данных:         {total_bytes / MB:.2f} MB")
    print(f"  Среднее время запроса:  {avg_seconds:.2f} с")
    print(f"  Средняя скорость:       {avg_speed_mb_s:.2f} MB/s")


if __name__ == "__main__":
    main()
