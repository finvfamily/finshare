"""
熔断器模块

提供熔断器模式实现，防止故障级联传播。
"""

import time
import threading
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from functools import wraps

from finshare.logger import logger


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5       # 失败阈值，连续失败次数
    success_threshold: int = 3       # 成功阈值，半开状态需要连续成功次数
    timeout: int = 60               # 恢复超时时间（秒）
    half_open_max_calls: int = 3   # 半开状态最大尝试次数


class CircuitBreaker:
    """
    熔断器实现

    状态转换:
    - CLOSED → OPEN: 连续失败达到阈值
    - OPEN → HALF_OPEN: 超过恢复超时时间
    - HALF_OPEN → CLOSED: 连续成功达到阈值
    - HALF_OPEN → OPEN: 失败则重新打开
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        初始化熔断器

        Args:
            name: 熔断器名称
            config: 熔断器配置
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change_time = time.time()
        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # 检查是否应该转换到半开状态
                if time.time() - self._last_state_change_time >= self.config.timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"熔断器 {self.name} 从 OPEN 切换到 HALF_OPEN")
            return self._state

    def is_available(self) -> bool:
        """检查是否可用"""
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        """记录成功"""
        with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._last_state_change_time = time.time()
                    logger.info(f"熔断器 {self.name} 从 HALF_OPEN 切换到 CLOSED")

    def record_failure(self) -> None:
        """记录失败"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._last_state_change_time = time.time()
                logger.warning(f"熔断器 {self.name} 从 HALF_OPEN 切换到 OPEN (半开状态失败)")
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._last_state_change_time = time.time()
                    logger.warning(f"熔断器 {self.name} 从 CLOSED 切换到 OPEN (连续 {self._failure_count} 次失败)")

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "last_failure_time": self._last_failure_time,
                "uptime": time.time() - self._last_state_change_time,
            }

    def reset(self) -> None:
        """重置熔断器"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._last_state_change_time = time.time()


def circuit_breaker(
    name: str = "",
    config: Optional[CircuitBreakerConfig] = None,
    fallback: Optional[Callable] = None,
):
    """
    熔断器装饰器

    Args:
        name: 熔断器名称
        config: 熔断器配置
        fallback: 降级函数

    Returns:
        装饰后的函数

    Example:
        @circuit_breaker("stock_api", fallback=get_cached_data)
        def fetch_stock_data(code):
            return api.get(code)
    """
    breaker = CircuitBreaker(name or "default", config)
    _circuit_breakers[name or "default"] = breaker

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not breaker.is_available():
                logger.warning(f"熔断器 {breaker.name} 处于 OPEN 状态，拒绝请求")
                if fallback:
                    return fallback(*args, **kwargs)
                raise CircuitBreakerOpenError(f"Circuit breaker {breaker.name} is OPEN")

            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                if fallback:
                    return fallback(*args, **kwargs)
                raise

        wrapper.circuit_breaker = breaker
        return wrapper

    return decorator


class CircuitBreakerOpenError(Exception):
    """熔断器打开异常"""
    pass


# 全局熔断器管理器
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """获取熔断器"""
    return _circuit_breakers.get(name)


def get_all_circuit_breakers() -> dict[str, CircuitBreaker]:
    """获取所有熔断器"""
    return _circuit_breakers.copy()


def reset_circuit_breaker(name: str) -> bool:
    """重置熔断器"""
    breaker = _circuit_breakers.get(name)
    if breaker:
        breaker.reset()
        return True
    return False


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "circuit_breaker",
    "CircuitBreakerOpenError",
    "get_circuit_breaker",
    "get_all_circuit_breakers",
    "reset_circuit_breaker",
]
