"""
智能冷却机制 - 根据错误类型分级冷却

冷却策略:
- timeout: 30秒
- connection_error: 60秒
- 429限流: 5分钟 (300秒)
- 403禁止: 10分钟 (600秒)
- 503不可用: 5分钟 (300秒)
- default: 5分钟 (300秒)

支持:
- 连续失败累积冷却
- 配置化冷却策略
"""

import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass, field
from finshare.logger import logger


@dataclass
class CooldownConfig:
    """冷却配置"""
    timeout: int = 30              # 超时错误 (秒)
    connection_error: int = 60     # 连接错误 (秒)
    rate_limit_429: int = 300     # 429限流 (秒)
    forbidden_403: int = 600      # 403禁止 (秒)
    service_unavailable_503: int = 300  # 503服务不可用 (秒)
    default: int = 300            # 默认冷却 (秒)


@dataclass
class SourceState:
    """数据源状态"""
    source_name: str
    cooldown_until: float = 0     # 冷却结束时间戳
    consecutive_failures: int = 0 # 连续失败次数
    last_failure_time: float = 0   # 上次失败时间
    last_success_time: float = 0   # 上次成功时间
    total_requests: int = 0        # 总请求数
    total_failures: int = 0        # 总失败次数
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def is_in_cooldown(self) -> bool:
        """是否在冷却中"""
        return time.time() < self.cooldown_until

    @property
    def cooldown_remaining(self) -> float:
        """剩余冷却时间（秒）"""
        remaining = self.cooldown_until - time.time()
        return max(0, remaining)

    @property
    def success_rate(self) -> float:
        """请求成功率"""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.total_failures) / self.total_requests


class SmartCooldown:
    """
    智能冷却管理器

    根据错误类型动态调整冷却时间，支持连续失败累积。
    """

    def __init__(self, config: Optional[CooldownConfig] = None):
        self.config = config or CooldownConfig()
        self._source_states: Dict[str, SourceState] = {}
        self._lock = threading.Lock()

    def get_source_state(self, source_name: str) -> SourceState:
        """获取数据源状态"""
        with self._lock:
            if source_name not in self._source_states:
                self._source_states[source_name] = SourceState(source_name=source_name)
            return self._source_states[source_name]

    def enter_cooldown(
        self,
        source_name: str,
        error_type: str = "default",
        http_status: Optional[int] = None,
    ) -> float:
        """
        进入冷却状态

        Args:
            source_name: 数据源名称
            error_type: 错误类型 (timeout, connection_error, rate_limit, forbidden, etc.)
            http_status: HTTP 状态码

        Returns:
            冷却时间（秒）
        """
        state = self.get_source_state(source_name)

        with state._lock:
            # 计算基础冷却时间
            cooldown_seconds = self._get_base_cooldown(error_type, http_status)

            # 连续失败累积冷却：每次失败增加 1.5 倍冷却时间
            if state.consecutive_failures > 0:
                multiplier = min(1 + state.consecutive_failures * 0.5, 5.0)  # 最多5倍
                cooldown_seconds = cooldown_seconds * multiplier

            # 设置冷却结束时间
            state.cooldown_until = time.time() + cooldown_seconds
            state.consecutive_failures += 1
            state.last_failure_time = time.time()
            state.total_failures += 1

            logger.warning(
                f"[{source_name}] 进入冷却状态 | "
                f"错误类型: {error_type} | "
                f"HTTP状态: {http_status} | "
                f"冷却时间: {cooldown_seconds:.0f}秒 | "
                f"连续失败: {state.consecutive_failures}次 | "
                f"累积倍率: {1 + state.consecutive_failures * 0.5:.1f}x"
            )

            return cooldown_seconds

    def exit_cooldown(self, source_name: str) -> None:
        """冷却结束（请求成功时调用）"""
        state = self.get_source_state(source_name)

        with state._lock:
            if state.consecutive_failures > 0:
                logger.info(
                    f"[{source_name}] 冷却结束 | "
                    f"连续失败次数: {state.consecutive_failures} | "
                    f"成功率: {state.success_rate:.2%}"
                )
            # 重置连续失败计数
            state.consecutive_failures = 0
            state.last_success_time = time.time()

    def is_in_cooldown(self, source_name: str) -> bool:
        """检查是否在冷却中"""
        state = self.get_source_state(source_name)
        return state.is_in_cooldown

    def get_cooldown_remaining(self, source_name: str) -> float:
        """获取剩余冷却时间"""
        state = self.get_source_state(source_name)
        return state.cooldown_remaining

    def record_request(self, source_name: str) -> None:
        """记录请求"""
        state = self.get_source_state(source_name)
        with state._lock:
            state.total_requests += 1

    def record_success(self, source_name: str) -> None:
        """记录成功"""
        self.exit_cooldown(source_name)

    def record_failure(
        self,
        source_name: str,
        error_type: str = "default",
        http_status: Optional[int] = None,
    ) -> None:
        """记录失败"""
        self.enter_cooldown(source_name, error_type, http_status)

    def get_status(self, source_name: str) -> dict:
        """获取数据源状态"""
        state = self.get_source_state(source_name)
        return {
            "source_name": source_name,
            "is_in_cooldown": state.is_in_cooldown,
            "cooldown_remaining": state.cooldown_remaining,
            "consecutive_failures": state.consecutive_failures,
            "total_requests": state.total_requests,
            "total_failures": state.total_failures,
            "success_rate": state.success_rate,
            "last_success_time": state.last_success_time,
            "last_failure_time": state.last_failure_time,
        }

    def _get_base_cooldown(self, error_type: str, http_status: Optional[int]) -> float:
        """获取基础冷却时间"""
        # 如果有 HTTP 状态码，优先根据状态码
        if http_status:
            if http_status == 429:
                return self.config.rate_limit_429
            elif http_status == 403:
                return self.config.forbidden_403
            elif http_status == 503:
                return self.config.service_unavailable_503
            elif http_status >= 500:
                return self.config.service_unavailable_503
            elif http_status >= 400:
                return self.config.default

        # 根据错误类型
        error_cooldown_map = {
            "timeout": self.config.timeout,
            "connection_error": self.config.connection_error,
            "rate_limit": self.config.rate_limit_429,
            "forbidden": self.config.forbidden_403,
            "service_unavailable": self.config.service_unavailable_503,
            "default": self.config.default,
        }

        return error_cooldown_map.get(error_type, self.config.default)


# 全局智能冷却实例
cooldown_manager = SmartCooldown()


def get_cooldown_manager() -> SmartCooldown:
    """获取全局冷却管理器"""
    return cooldown_manager
