"""Load testing for NEDC-BENCH API"""

import asyncio
import operator
import statistics
import sys
import time
from pathlib import Path

try:
    import aiohttp
except ImportError:
    print("Please install aiohttp: pip install aiohttp")
    sys.exit(1)


async def single_request(session, url, ref_data, hyp_data):
    """Execute single evaluation request"""

    data = aiohttp.FormData()
    data.add_field(
        "reference", ref_data, filename="ref.csv_bi", content_type="application/octet-stream"
    )
    data.add_field(
        "hypothesis", hyp_data, filename="hyp.csv_bi", content_type="application/octet-stream"
    )
    data.add_field("algorithms", "taes")
    data.add_field("pipeline", "dual")

    start_time = time.time()

    async with session.post(f"{url}/api/v1/evaluate", data=data) as response:
        result = await response.json()
        elapsed = time.time() - start_time

        return {
            "job_id": result.get("job_id"),
            "status_code": response.status,
            "elapsed": elapsed,
        }


async def load_test(
    base_url: str = "http://localhost:8000",
    n_requests: int = 100,
    concurrent: int = 10,
):
    """Load test the API"""

    # Load sample files
    ref_file = Path("nedc_eeg_eval/v6.0.0/data/csv/ref/aaaaaasf_s001_t000.csv_bi")
    hyp_file = Path("nedc_eeg_eval/v6.0.0/data/csv/hyp/aaaaaasf_s001_t000.csv_bi")

    if not ref_file.exists() or not hyp_file.exists():
        print(f"Error: Sample files not found at {ref_file} and {hyp_file}")
        return

    ref_data = ref_file.read_bytes()
    hyp_data = hyp_file.read_bytes()

    print(f"Starting load test: {n_requests} requests with {concurrent} concurrent")
    print(f"Target: {base_url}")
    print("-" * 60)

    async with aiohttp.ClientSession() as session:
        start_time = time.time()

        # Create batches of concurrent requests
        results = []
        for i in range(0, n_requests, concurrent):
            batch_size = min(concurrent, n_requests - i)
            batch = [
                single_request(session, base_url, ref_data, hyp_data) for _ in range(batch_size)
            ]

            batch_results = await asyncio.gather(*batch, return_exceptions=True)

            # Process results
            for r in batch_results:
                if isinstance(r, Exception):
                    results.append({"status_code": 0, "elapsed": 0, "error": str(r)})
                else:
                    results.append(r)

            # Progress indicator
            completed = min(i + concurrent, n_requests)
            print(f"Progress: {completed}/{n_requests} requests completed", end="\r")

        total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("Load Test Results:")
    print("=" * 60)

    # Calculate statistics
    successful = [r for r in results if r.get("status_code") == 200]
    failed = [r for r in results if r.get("status_code") != 200]
    response_times = [r["elapsed"] for r in successful if r["elapsed"] > 0]

    if response_times:
        print(f"  Total requests:     {n_requests}")
        print(
            f"  Successful:         {len(successful)} ({len(successful) / n_requests * 100:.1f}%)"
        )
        print(f"  Failed:             {len(failed)} ({len(failed) / n_requests * 100:.1f}%)")
        print(f"  Total time:         {total_time:.2f} seconds")
        print(f"  Requests/second:    {n_requests / total_time:.2f}")
        print()
        print("Response Times:")
        print(f"  Average:            {statistics.mean(response_times):.3f}s")
        print(f"  Minimum:            {min(response_times):.3f}s")
        print(f"  Maximum:            {max(response_times):.3f}s")
        print(f"  Median:             {statistics.median(response_times):.3f}s")

        if len(response_times) > 1:
            print(f"  Std Dev:            {statistics.stdev(response_times):.3f}s")

        # Calculate percentiles
        if len(response_times) >= 20:
            quantiles = statistics.quantiles(response_times, n=20)
            print(f"  P50 (median):       {quantiles[9]:.3f}s")
            print(f"  P90:                {quantiles[17]:.3f}s")
            print(f"  P95:                {quantiles[18]:.3f}s")
            print(
                f"  P99:                {quantiles[19] if len(quantiles) > 19 else max(response_times):.3f}s"
            )
    else:
        print("No successful requests!")

    # Print errors if any
    if failed:
        print("\nErrors encountered:")
        error_counts = {}
        for f in failed:
            error = f.get("error", f"HTTP {f.get('status_code', 'unknown')}")
            error_counts[error] = error_counts.get(error, 0) + 1

        for error, count in sorted(error_counts.items(), key=operator.itemgetter(1), reverse=True)[
            :5
        ]:
            print(f"  {error}: {count} times")

    print("=" * 60)

    # Performance assertions for CI
    if response_times:
        success_rate = len(successful) / n_requests
        requests_per_second = n_requests / total_time

        print("\nPerformance Checks:")
        print(
            f"  ✓ Success rate >= 99%:     {success_rate >= 0.99} (actual: {success_rate * 100:.1f}%)"
        )
        print(
            f"  ✓ Throughput >= 100 req/s: {requests_per_second >= 100} (actual: {requests_per_second:.1f} req/s)"
        )

        # Return True if all checks pass
        return success_rate >= 0.99 and requests_per_second >= 100
    return False


async def main():
    """Run load test with different configurations"""

    import argparse

    parser = argparse.ArgumentParser(description="Load test NEDC-BENCH API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--requests", type=int, default=100, help="Total number of requests")
    parser.add_argument("--concurrent", type=int, default=10, help="Number of concurrent requests")
    parser.add_argument("--test", action="store_true", help="Run quick test (10 requests)")

    args = parser.parse_args()

    if args.test:
        # Quick test mode
        success = await load_test(args.url, n_requests=10, concurrent=2)
    else:
        success = await load_test(args.url, n_requests=args.requests, concurrent=args.concurrent)

    # Exit with appropriate code for CI
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
