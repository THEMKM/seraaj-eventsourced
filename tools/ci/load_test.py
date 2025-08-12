#!/usr/bin/env python3
"""
Basic Load Testing for CI/CD Pipeline

Performs lightweight load testing to validate service performance
and detect performance regressions during CI.
"""

import asyncio
import httpx
import time
import json
import statistics
import sys
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LoadTestResult:
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    requests_per_second: float
    error_rate: float
    errors: List[str]

class LoadTester:
    """Simple load tester for CI validation"""
    
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
    async def run_requests(self, endpoint: str, method: str, 
                          request_count: int, concurrency: int,
                          request_data: Optional[Dict] = None) -> LoadTestResult:
        """Run load test for a single endpoint"""
        
        logger.info(f"Running load test: {method.upper()} {endpoint}")
        logger.info(f"Requests: {request_count}, Concurrency: {concurrency}")
        
        url = f"{self.base_url}{endpoint}"
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def make_request(session: httpx.AsyncClient) -> None:
            """Make a single request"""
            nonlocal successful_requests, failed_requests
            
            async with semaphore:
                start_time = time.time()
                
                try:
                    if method.upper() == 'GET':
                        response = await session.get(url)
                    elif method.upper() == 'POST':
                        response = await session.post(url, json=request_data or {})
                    else:
                        raise ValueError(f"Unsupported method: {method}")
                    
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code in [200, 201]:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        errors.append(f"HTTP {response.status_code}")
                        
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    failed_requests += 1
                    errors.append(str(e))
        
        # Run the load test
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=self.timeout) as session:
            tasks = [make_request(session) for _ in range(request_count)]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else avg_response_time
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0
        
        requests_per_second = request_count / total_time if total_time > 0 else 0
        error_rate = (failed_requests / request_count) * 100 if request_count > 0 else 0
        
        # Limit error samples
        error_samples = list(set(errors))[:5]
        
        return LoadTestResult(
            endpoint=endpoint,
            method=method.upper(),
            total_requests=request_count,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=round(avg_response_time, 2),
            min_response_time_ms=round(min_response_time, 2),
            max_response_time_ms=round(max_response_time, 2),
            p95_response_time_ms=round(p95_response_time, 2),
            requests_per_second=round(requests_per_second, 2),
            error_rate=round(error_rate, 2),
            errors=error_samples
        )
    
    def evaluate_performance(self, result: LoadTestResult) -> bool:
        """Evaluate if performance meets acceptable criteria"""
        
        # Define performance thresholds for CI
        max_avg_response_time = 1000  # 1 second
        max_p95_response_time = 2000  # 2 seconds
        max_error_rate = 5.0  # 5%
        min_requests_per_second = 10  # 10 RPS
        
        issues = []
        
        if result.avg_response_time_ms > max_avg_response_time:
            issues.append(f"Average response time too high: {result.avg_response_time_ms}ms > {max_avg_response_time}ms")
        
        if result.p95_response_time_ms > max_p95_response_time:
            issues.append(f"P95 response time too high: {result.p95_response_time_ms}ms > {max_p95_response_time}ms")
        
        if result.error_rate > max_error_rate:
            issues.append(f"Error rate too high: {result.error_rate}% > {max_error_rate}%")
        
        if result.requests_per_second < min_requests_per_second:
            issues.append(f"Throughput too low: {result.requests_per_second} RPS < {min_requests_per_second} RPS")
        
        if issues:
            logger.warning(f"Performance issues for {result.method} {result.endpoint}:")
            for issue in issues:
                logger.warning(f"  - {issue}")
            return False
        else:
            logger.info(f"✅ Performance acceptable for {result.method} {result.endpoint}")
            return True

def main():
    """Main load testing function"""
    import os
    
    base_url = os.getenv('BFF_BASE_URL', 'http://127.0.0.1:8000')
    logger.info(f"Starting load tests against {base_url}")
    
    tester = LoadTester(base_url, timeout=30)
    
    # Define load test scenarios
    test_scenarios = [
        {
            'endpoint': '/api/health',
            'method': 'GET',
            'requests': 50,
            'concurrency': 10,
            'description': 'Health endpoint stress test'
        },
        {
            'endpoint': '/api/volunteer/quick-match',
            'method': 'POST',
            'requests': 20,
            'concurrency': 5,
            'data': {
                'volunteerId': 'load-test-volunteer',
                'limit': 5
            },
            'description': 'Quick match endpoint load test'
        }
    ]
    
    logger.info(f"Running {len(test_scenarios)} load test scenarios...")
    
    all_results = []
    all_passed = True
    
    async def run_all_tests():
        nonlocal all_passed
        
        for i, scenario in enumerate(test_scenarios):
            logger.info(f"\n--- Test {i+1}/{len(test_scenarios)}: {scenario['description']} ---")
            
            result = await tester.run_requests(
                scenario['endpoint'],
                scenario['method'], 
                scenario['requests'],
                scenario['concurrency'],
                scenario.get('data')
            )
            
            all_results.append(result)
            
            # Log results
            logger.info(f"Results for {result.method} {result.endpoint}:")
            logger.info(f"  Total requests: {result.total_requests}")
            logger.info(f"  Successful: {result.successful_requests}")
            logger.info(f"  Failed: {result.failed_requests}")
            logger.info(f"  Error rate: {result.error_rate}%")
            logger.info(f"  Avg response time: {result.avg_response_time_ms}ms")
            logger.info(f"  P95 response time: {result.p95_response_time_ms}ms")
            logger.info(f"  Throughput: {result.requests_per_second} RPS")
            
            # Evaluate performance
            passed = tester.evaluate_performance(result)
            if not passed:
                all_passed = False
    
    # Run the tests
    asyncio.run(run_all_tests())
    
    # Generate summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Load Test Summary")
    logger.info(f"{'='*50}")
    
    for result in all_results:
        status = "✅ PASS" if tester.evaluate_performance(result) else "❌ FAIL"
        logger.info(f"{status} {result.method} {result.endpoint}: {result.avg_response_time_ms}ms avg, {result.error_rate}% errors")
    
    # Export results as JSON for CI artifacts
    results_json = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'base_url': base_url,
        'summary': {
            'total_scenarios': len(test_scenarios),
            'passed': sum(1 for r in all_results if tester.evaluate_performance(r)),
            'failed': sum(1 for r in all_results if not tester.evaluate_performance(r)),
            'overall_result': 'pass' if all_passed else 'fail'
        },
        'results': [asdict(result) for result in all_results]
    }
    
    with open('load-test-results.json', 'w') as f:
        json.dump(results_json, f, indent=2)
    
    logger.info(f"Load test results exported to load-test-results.json")
    
    if all_passed:
        logger.info("✅ All load tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some load tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()