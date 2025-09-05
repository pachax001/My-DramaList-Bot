# Migration Guide: Cinemagoer → imdbinfo

## Overview
This guide covers the migration from the `cinemagoer` library to `imdbinfo` for better async compatibility and performance.

## Key Changes

### 1. Library Replacement
```bash
# Before
pip install git+https://github.com/cinemagoer/cinemagoer

# After  
pip install imdbinfo
```

### 2. API Differences

#### Search Movies
```python
# Before (cinemagoer)
ia = imdb.Cinemagoer()
results = ia.search_movie(query)

# After (imdbinfo)
from imdbinfo import ImdbInfo
info = ImdbInfo()
results = info.search_movie(query)
```

#### Get Movie Details
```python
# Before (cinemagoer)
movie = ia.get_movie(movie_id)
title = movie['title']

# After (imdbinfo) 
movie = info.get_movie(movie_id)
title = movie.get('title')
```

### 3. Async Integration

The new architecture wraps synchronous imdbinfo calls in a thread pool:

```python
class IMDBAdapter:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    async def search_movies(self, query: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._sync_search_movies,
            query
        )
```

## Data Structure Changes

### Movie Object Mapping
```python
# cinemagoer format
{
    'title': 'Movie Title',
    'year': 2023,
    'rating': 8.5,
    'plot outline': 'Plot text...',
    'genres': ['Action', 'Drama']
}

# imdbinfo format (similar but may have slight differences)
{
    'title': 'Movie Title', 
    'year': '2023',        # String instead of int
    'rating': '8.5',       # String instead of float
    'plot': 'Plot text...', # Different key name
    'genres': ['Action', 'Drama']
}
```

## Code Migration Steps

### Step 1: Update Requirements
```bash
# Remove old dependency
pip uninstall cinemagoer

# Install new dependency
pip install imdbinfo aiohttp motor pydantic aioredis
```

### Step 2: Update Imports
```python
# Before
import imdb
ia = imdb.Cinemagoer()

# After
from adapters.imdb import imdb_adapter
```

### Step 3: Update Function Calls
```python
# Before
def search_imdb(query):
    return ia.search_movie(query)

# After  
async def search_imdb(query):
    return await imdb_adapter.search_movies(query)
```

### Step 4: Update Handlers
```python
# Before
async def imdb_search_handler(client, message):
    results = filter_imdb(query)  # sync call
    
# After
async def imdb_search_handler(client, message):
    results = await filter_imdb(query)  # async call
```

## Testing Migration

### Unit Tests
```python
import pytest
from adapters.imdb import imdb_adapter

@pytest.mark.asyncio
async def test_imdb_search():
    results = await imdb_adapter.search_movies("Inception")
    assert len(results) > 0
    assert 'title' in results[0]

@pytest.mark.asyncio  
async def test_imdb_details():
    details = await imdb_adapter.get_movie_details("0816692")
    assert details is not None
    assert details.get('title') is not None
```

### Performance Comparison
```python
# Run before and after migration
python tests/load_test.py
```

Expected improvements:
- 50% reduction in IMDB query latency
- Better concurrent request handling
- Improved error handling and retries

## Rollback Plan

If issues arise, rollback is possible:

1. **Revert requirements.txt**
   ```bash
   git checkout HEAD~1 requirements.txt
   pip install -r requirements.txt
   ```

2. **Switch back to old main.py**
   ```bash
   mv main.py main_new.py
   mv main_old.py main.py  # if backup exists
   ```

3. **Remove new architecture directories**
   ```bash
   rm -rf infra/ adapters/ domain/ app/
   ```

## Production Deployment

### Staging Environment
1. Deploy to staging with new architecture
2. Run load tests to validate performance
3. Monitor error rates and latency
4. Test all bot commands thoroughly

### Production Rollout
1. **Blue-Green Deployment**: Keep old version running
2. **Deploy New Version**: Start new containers alongside old
3. **Traffic Switch**: Route 10% → 50% → 100% of traffic
4. **Monitor**: Watch metrics closely during transition
5. **Rollback if Needed**: Quick switch back to old version

### Monitoring During Migration
- **Error Rate**: Should remain <1%  
- **Response Time**: P95 should improve by 30%+
- **Memory Usage**: May increase slightly due to caching
- **CPU Usage**: Should decrease due to async efficiency

## Troubleshooting

### Common Issues

#### imdbinfo Import Errors
```bash
# Solution: Install with specific version
pip install imdbinfo==1.0.0
```

#### Thread Pool Exhaustion
```python
# Increase pool size if needed
self.executor = ThreadPoolExecutor(max_workers=10)
```

#### Memory Usage Increase
```python
# Tune cache TTLs to reduce memory
await cache_client.set("imdb_details", key, data, ttl=1800)  # 30min instead of 24h
```

## Verification Checklist

- [ ] All IMDB search functionality works
- [ ] Movie details display correctly  
- [ ] Templates still render properly
- [ ] Performance tests pass
- [ ] Error handling works as expected
- [ ] Caching reduces duplicate requests
- [ ] Logs show correlation IDs
- [ ] Health checks return success
- [ ] Docker deployment works
- [ ] Load testing shows improvements