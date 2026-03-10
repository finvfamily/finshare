"""
请求重试处理器 - 指数退避重试机制

特性:
- 最大重试次数: 3次
- 指数退避: 10s → 20s → 40s
- 仅对临时性错误重试
- 线程安全
"""

import time
import random
import threading
from typing import Callable, Optional, Any, TypeVar, Set
from functools import wraps
from finshare.logger import logger

T = TypeVar('T')

# 可重试的 HTTP 状态码
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}

# 可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    ConnectionResetError,
    ConnectionRefusedError,
)


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 10.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: float = 0.3,
    ):
        """
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟（秒）
            max_delay: 最大延迟（秒）
            backoff_factor: 退避因子（指数）
            jitter: 随机抖动范围（0-1）
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter


class RetryHandler:
    """
    重试处理器

    支持指数退避和可选的重试条件。
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def calculate_delay(self, attempt: int) -> float:
        """
        计算延迟时间（指数退避 + 随机抖动）

        退避序列: 10s → 20s → 40s → 60s (max)
        """
        # 指数退避
        delay = self.config.base_delay * (self.config.backoff_factor ** attempt)

        # 限制最大延迟
        delay = min(delay, self.config.max_delay)

        # 添加随机抖动
        jitter_range = delay * self.config.jitter
        delay = delay + random.uniform(-jitter_range, jitter_range)

        # 确保延迟至少为 1 秒
        return max(1.0, delay)

    def should_retry(
        self,
        exception: Optional[Exception] = None,
        http_status: Optional[int] = None,
    ) -> bool:
        """
        判断是否应该重试

        Args:
            exception: 异常对象
            http_status: HTTP 状态码

        Returns:
            是否应该重试
        """
        # 检查 HTTP 状态码
        if http_status and http_status in RETRYABLE_HTTP_CODES:
            return True

        # 检查异常类型
        if exception:
            if isinstance(exception, RETRYABLE_EXCEPTIONS):
                return True
            # 检查异常是否包含可重试的错误信息
            error_msg = str(exception).lower()
            retry_keywords = [
                "timeout", "timed out", "connection",
                "reset", "refused", "temporary",
                "temporary failure", "service unavailable",
            ]
            if any(keyword in error_msg for keyword in retry_keywords):
                return True

        return False

    def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """
        执行函数，自动重试

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            最后一次重试的异常
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"重试成功 | 尝试次数: {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e

                # 判断是否应该重试
                http_status = getattr(e, "response", None)
                if http_status:
                    http_status = http_status.status_code

                if not self.should_retry(exception=e, http_status=http_status):
                    logger.warning(f"重试终止 | 错误类型: {type(e).__name__} | 消息: {e}")
                    raise

                # 判断是否还有重试机会
                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"重试 | "
                        f"尝试: {attempt + 1}/{self.config.max_retries + 1} | "
                        f"延迟: {delay:.1f}秒 | "
                        f"错误: {type(e).__name__}: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"重试次数用尽 | "
                        f"总尝试: {attempt + 1} | "
                        f"错误: {type(e).__name__}: {e}"
                    )

        # 所有重试都失败
        raise last_exception

    def retry_decorator(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        重试装饰器

        Usage:
            @retry_handler.retry_decorator
            def fetch_data():
                ...
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(func, *args, **kwargs)

        return wrapper


# 全局重试处理器
retry_handler = RetryHandler()


def get_retry_handler() -> RetryHandler:
    """获取全局重试处理器"""
    return retry_handler


# 便捷装饰器
def retry(
    max_retries: int = 3,
    base_delay: float = 10.0,
    max_delay: float = 60.0,
):
    """
    重试装饰器

    Usage:
        @retry(max_retries=3, base_delay=10)
        def fetch_data():
            ...
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
    )
    handler = RetryHandler(config)
    return handler.retry_decorator
