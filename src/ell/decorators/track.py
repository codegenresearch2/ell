import logging
from typing import Callable, Any, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the track function
def track(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to log function calls and their arguments."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        logger.info(f'Function {fn.__name__} called with args: {args}, kwargs: {kwargs}')
        try:
            result = fn(*args, **kwargs)
            logger.info(f'Function {fn.__name__} returned: {result}')
            return result
        except Exception as e:
            logger.error(f'Function {fn.__name__} raised an error: {e}')
            raise
    return wrapper

# Example usage
@track
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# Test the function
if __name__ == '__main__':
    result = add(3, 5)
    print(f'Result of add(3, 5): {result}')
    try:
        add('a', 'b')
    except TypeError as e:
        logger.error(f'Error during add("a", "b"): {e}')