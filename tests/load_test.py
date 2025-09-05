"""Load test to validate performance improvements."""

import asyncio
import time

import aiohttp

from infra.config import settings


class LoadTester:
    """Simple load tester for bot performance validation."""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_mydramalist_search(self, query: str) -> float:
        """Test MyDramaList search endpoint."""
        url = settings.mydramalist_api_url.format(query)
        start_time = time.time()
        
        try:
            async with self.session.get(url) as response:
                await response.json()
                return time.time() - start_time
        except Exception as e:
            print(f"Error testing MDL search: {e}")
            return -1
    
    async def test_imdbinfo_performance(self) -> dict:
        """Test imdbinfo performance vs old cinemagoer."""
        from adapters.imdb import imdb_adapter
        
        queries = ["Inception", "The Matrix", "Pulp Fiction", "Godfather", "Shawshank"]
        results = {}
        
        for query in queries:
            start_time = time.time()
            movies = await imdb_adapter.search_movies(query)
            duration = time.time() - start_time
            
            results[query] = {
                'duration': duration,
                'count': len(movies)
            }
        
        return results
    
    async def concurrent_test(self, concurrency: int = 50, requests_per_worker: int = 10):
        """Test concurrent request handling."""
        queries = ["vincenzo", "squid game", "crash landing", "goblin", "descendants"]
        
        async def worker():
            times = []
            for _ in range(requests_per_worker):
                query = queries[len(times) % len(queries)]
                duration = await self.test_mydramalist_search(query)
                if duration > 0:
                    times.append(duration)
            return times
        
        print(f"Starting load test: {concurrency} concurrent workers, {requests_per_worker} requests each")
        start_time = time.time()
        
        # Run concurrent workers
        tasks = [worker() for _ in range(concurrency)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Collect all response times
        all_times = []
        for worker_times in results:
            all_times.extend(worker_times)
        
        if not all_times:
            print("No successful requests!")
            return
        
        # Calculate statistics
        all_times.sort()
        total_requests = len(all_times)
        avg_time = sum(all_times) / total_requests
        p95_time = all_times[int(0.95 * total_requests)]
        p99_time = all_times[int(0.99 * total_requests)]
        rps = total_requests / total_time
        
        print(f"\\n🚀 Load Test Results:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Requests/sec: {rps:.2f}")
        print(f"  Average Response Time: {avg_time:.3f}s")
        print(f"  P95 Response Time: {p95_time:.3f}s") 
        print(f"  P99 Response Time: {p99_time:.3f}s")
        
        return {
            'total_requests': total_requests,
            'rps': rps,
            'avg_response_time': avg_time,
            'p95_response_time': p95_time,
            'p99_response_time': p99_time
        }


async def run_performance_tests():
    """Run all performance validation tests."""
    print("🔍 Running performance validation tests...\\n")
    
    async with LoadTester() as tester:
        # Test 1: Basic functionality
        print("1. Testing basic search functionality...")
        duration = await tester.test_mydramalist_search("vincenzo")
        if duration > 0:
            print(f"   ✅ Search completed in {duration:.3f}s")
        else:
            print("   ❌ Search failed")
        
        # Test 2: IMDB performance
        print("\\n2. Testing IMDB adapter performance...")
        imdb_results = await tester.test_imdbinfo_performance()
        total_imdb_time = sum(r['duration'] for r in imdb_results.values())
        avg_imdb_time = total_imdb_time / len(imdb_results)
        print(f"   ✅ Average IMDB search: {avg_imdb_time:.3f}s")
        
        # Test 3: Concurrency test
        print("\\n3. Running concurrency test...")
        load_results = await tester.concurrent_test(concurrency=20, requests_per_worker=5)
        
        if load_results and load_results['rps'] >= 10:
            print("   ✅ Concurrency test passed (≥10 RPS)")
        else:
            print("   ⚠️  Concurrency test below target")
        
        print("\\n🎉 Performance validation complete!")
        
        return {
            'basic_search_time': duration,
            'avg_imdb_time': avg_imdb_time,
            'load_test': load_results
        }


if __name__ == "__main__":
    asyncio.run(run_performance_tests())