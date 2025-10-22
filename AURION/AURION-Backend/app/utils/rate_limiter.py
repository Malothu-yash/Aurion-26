from collections import defaultdict, deque
import time
import asyncio
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.limits = {
            'mini_agent': {'requests': 10, 'window': 60},  # 10 requests per minute
            'general': {'requests': 100, 'window': 60}     # 100 requests per minute
        }
    
    async def is_allowed(self, key: str, limit_type: str = 'general') -> bool:
        now = time.time()
        limit_config = self.limits.get(limit_type, self.limits['general'])
        max_requests = limit_config['requests']
        window = limit_config['window']
        
        # Clean old requests
        user_requests = self.requests[key]
        while user_requests and user_requests[0] <= now - window:
            user_requests.popleft()
        
        # Check if under limit
        if len(user_requests) < max_requests:
            user_requests.append(now)
            return True
        
        logger.warning(f"Rate limit exceeded for {key} ({limit_type})")
        return False
    
    def get_remaining_requests(self, key: str, limit_type: str = 'general') -> int:
        now = time.time()
        limit_config = self.limits.get(limit_type, self.limits['general'])
        max_requests = limit_config['requests']
        window = limit_config['window']
        
        user_requests = self.requests[key]
        while user_requests and user_requests[0] <= now - window:
            user_requests.popleft()
        
        return max(0, max_requests - len(user_requests))