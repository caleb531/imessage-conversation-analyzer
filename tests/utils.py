import inspect
import os
from functools import wraps
from typing import Any, Callable, Generator


class use_env(object):
    """
    A decorator (can also be used as a context manager) which sets an
    environment variable for only the lifetime of the given code; this utility
    works seamlessly for both functions and generators
    """

    def __init__(self, key: str, value: str) -> None:
        self.key: str = key
        self.value: str = value

    def __enter__(self) -> None:
        self.orig_value: str = os.environ.get(self.key, "")
        os.environ[self.key] = self.value

    def __exit__(self, type: type, value: Exception, traceback: Any) -> None:
        os.environ[self.key] = self.orig_value

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def function_wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return func(*args, **kwargs)

        @wraps(func)
        def generator_wrapper(*args: Any, **kwargs: Any) -> Generator[Any, None, Any]:
            with self:
                return (yield from func(*args, **kwargs))

        if inspect.isgeneratorfunction(func):
            return generator_wrapper
        else:
            return function_wrapper
