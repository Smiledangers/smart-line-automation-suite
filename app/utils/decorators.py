"""
Shared decorators for services (retry, circuit breaker, etc.).
"""
import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail immediately
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            # Check if we should try half-open
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
                logger.info("Circuit breaker moving to half-open state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
                logger.info("Circuit breaker moving to half-open state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == "half_open":
            self.state = "closed"
            self.failure_count = 0
            logger.info("Circuit breaker CLOSED after successful call")
        else:
            self.failure_count = max(0, self.failure_count - 1)
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying a function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed")
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed")
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception,
    fallback_func: Optional[Callable] = None,
):
    """
    Decorator for circuit breaker pattern.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before trying again
        expected_exception: Exception type to catch
        fallback_func: Function to call when circuit is open
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout, expected_exception)
    fallback = fallback_func
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await breaker.call_async(func, *args, **kwargs)
            except Exception as e:
                if fallback:
                    return fallback(*args, **kwargs)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return breaker.call(func, *args, **kwargs)
            except Exception as e:
                if fallback:
                    return fallback(*args, **kwargs)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log function execution time.
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def rate_limit(calls: int, period: float = 60.0):
    """
    Decorator for rate limiting a function.
    
    Args:
        calls: Maximum number of calls allowed
        period: Time period in seconds
    """
    call_times = []
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            now = time.time()
            # Remove old calls outside the period
            call_times[:] = [t for t in call_times if now - t < period]
            
            if len(call_times) >= calls:
                wait_time = period - (now - call_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            call_times.append(now)
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            now = time.time()
            call_times[:] = [t for t in call_times if now - t < period]
            
            if len(call_times) >= calls:
                wait_time = period - (now - call_times[0])
                if wait_time > 0:
                    time.sleep(wait_time)
            
            call_times.append(now)
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator