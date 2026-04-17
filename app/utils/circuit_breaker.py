"""
Circuit Breaker utility for external calls.
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass

class CircuitBreaker:
    """
    Simple circuit breaker implementation.
    
    Args:
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Seconds to wait before attempting to close the circuit
        fallback_function: Function to call when circuit is open
        expected_exception: Exception type to count as failure (default: Exception)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        fallback_function: Optional[Callable] = None,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback_function = fallback_function
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                    logger.info(f"Circuit breaker for {func.__name__} moved to half-open")
                else:
                    logger.warning(f"Circuit breaker for {func.__name__} is open, using fallback")
                    if self.fallback_function:
                        return self.fallback_function(*args, **kwargs)
                    raise CircuitBreakerOpenException(f"Circuit breaker open for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self) -> None:
        """Reset failure count and close circuit on success."""
        self.failure_count = 0
        self.state = "closed"
        self.last_failure_time = None
        logger.debug("Circuit breaker reset to closed state")
    
    def _on_failure(self) -> None:
        """Increment failure count and open circuit if threshold reached."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures. "
                f"Will attempt reset after {self.recovery_timeout} seconds."
            )

# Pre-configured circuit breakers for different services
def line_api_circuit_breaker(fallback_func: Optional[Callable] = None) -> CircuitBreaker:
    """Circuit breaker for LINE API calls."""
    return CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30,
        fallback_function=fallback_func
    )

def llm_invoke_circuit_breaker(fallback_func: Optional[Callable] = None) -> CircuitBreaker:
    """Circuit breaker for LLM invoke calls."""
    return CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30,
        fallback_function=fallback_func
    )

def botasaurus_crawler_circuit_breaker(fallback_func: Optional[Callable] = None) -> CircuitBreaker:
    """Circuit breaker for Botasaurus crawler calls."""
    return CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=30,
        fallback_function=fallback_func
    )