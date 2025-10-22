import time
import logging
from functools import wraps
from typing import Callable, Any
import asyncio

logger = logging.getLogger(__name__)

def monitor_performance(operation_name: str = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            operation = operation_name or func.__name__
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(f"{operation} completed in {duration:.2f}s")
                
                # Log slow operations
                if duration > 5.0:
                    logger.warning(f"Slow operation: {operation} took {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation} failed after {duration:.2f}s: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            operation = operation_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(f"{operation} completed in {duration:.2f}s")
                
                if duration > 5.0:
                    logger.warning(f"Slow operation: {operation} took {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation} failed after {duration:.2f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
