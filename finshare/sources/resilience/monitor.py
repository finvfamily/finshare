"""
监控模块

提供请求统计、响应时间监控等功能。
"""

import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque


@dataclass
class RequestStats:
    """请求统计"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    last_request_time: Optional[float] = None


@dataclass
class TimeWindowStats:
    """时间窗口统计"""
    window_size: int = 60  # 窗口大小（秒）
    max_points: int = 100  # 最大数据点

    requests: deque = field(default_factory=lambda: deque(maxlen=100))
    errors: deque = field(default_factory=lambda: deque(maxlen=100))
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))


class Monitor:
    """
    监控系统

    监控数据源的请求成功率、响应时间等指标。
    """

    def __init__(self, window_size: int = 60):
        """
        初始化监控器

        Args:
            window_size: 时间窗口大小（秒）
        """
        self._window_size = window_size
        self._stats: Dict[str, RequestStats] = defaultdict(RequestStats)
        self._time_windows: Dict[str, TimeWindowStats] = defaultdict(
            lambda: TimeWindowStats(window_size=window_size)
        )
        self._lock = threading.RLock()
        self._start_time = time.time()

    def record_request(
        self,
        source: str,
        success: bool,
        response_time: float,
        error: Optional[str] = None,
    ) -> None:
        """
        记录请求

        Args:
            source: 数据源名称
            success: 是否成功
            response_time: 响应时间（秒）
            error: 错误信息
        """
        with self._lock:
            # 更新总体统计
            stats = self._stats[source]
            stats.total_requests += 1
            if success:
                stats.successful_requests += 1
            else:
                stats.failed_requests += 1

            stats.total_response_time += response_time
            stats.min_response_time = min(stats.min_response_time, response_time)
            stats.max_response_time = max(stats.max_response_time, response_time)
            stats.last_request_time = time.time()

            # 更新时间窗口统计
            window = self._time_windows[source]
            window.requests.append((time.time(), 1))
            if not success:
                window.errors.append((time.time(), error or "unknown"))
            window.response_times.append((time.time(), response_time))

            # 清理过期数据
            self._cleanup(source)

    def _cleanup(self, source: str) -> None:
        """清理过期数据"""
        cutoff_time = time.time() - self._window_size
        window = self._time_windows[source]

        while window.requests and window.requests[0][0] < cutoff_time:
            window.requests.popleft()

        while window.errors and window.errors[0][0] < cutoff_time:
            window.errors.popleft()

        while window.response_times and window.response_times[0][0] < cutoff_time:
            window.response_times.popleft()

    def get_stats(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            source: 数据源名称，None表示所有

        Returns:
            统计信息
        """
        with self._lock:
            if source:
                stats = self._stats.get(source, RequestStats())
                return self._format_stats(source, stats)

            return {
                src: self._format_stats(src, stats)
                for src, stats in self._stats.items()
            }

    def _format_stats(self, source: str, stats: RequestStats) -> Dict[str, Any]:
        """格式化统计信息"""
        total = stats.total_requests
        success = stats.successful_requests

        return {
            "source": source,
            "total_requests": total,
            "successful_requests": success,
            "failed_requests": stats.failed_requests,
            "success_rate": success / total if total > 0 else 0,
            "avg_response_time": stats.total_response_time / total if total > 0 else 0,
            "min_response_time": stats.min_response_time if stats.min_response_time != float('inf') else 0,
            "max_response_time": stats.max_response_time,
            "last_request_time": stats.last_request_time,
        }

    def get_time_window_stats(self, source: str) -> Dict[str, Any]:
        """
        获取时间窗口统计

        Args:
            source: 数据源名称

        Returns:
            时间窗口统计
        """
        with self._lock:
            window = self._time_windows.get(source, TimeWindowStats())
            now = time.time()
            cutoff = now - self._window_size

            # 计算窗口内的统计数据
            window_requests = sum(1 for t, _ in window.requests if t >= cutoff)
            window_errors = sum(1 for t, _ in window.errors if t >= cutoff)
            window_response_times = [rt for t, rt in window.response_times if t >= cutoff]

            return {
                "source": source,
                "window_size": self._window_size,
                "requests_in_window": window_requests,
                "errors_in_window": window_errors,
                "success_rate_in_window": (window_requests - window_errors) / window_requests if window_requests > 0 else 0,
                "avg_response_time_in_window": sum(window_response_times) / len(window_response_times) if window_response_times else 0,
            }

    def get_health_status(self) -> Dict[str, bool]:
        """
        获取数据源健康状态

        Returns:
            数据源健康状态
        """
        with self._lock:
            status = {}
            for source, stats in self._stats.items():
                total = stats.total_requests
                if total == 0:
                    # 没有请求过，默认健康
                    status[source] = True
                else:
                    success_rate = stats.successful_requests / total
                    # 成功率低于50%认为不健康
                    status[source] = success_rate >= 0.5

            return status

    def get_uptime(self) -> float:
        """获取运行时间（秒）"""
        return time.time() - self._start_time

    def reset(self, source: Optional[str] = None) -> None:
        """
        重置统计

        Args:
            source: 数据源名称，None表示所有
        """
        with self._lock:
            if source:
                if source in self._stats:
                    self._stats[source] = RequestStats()
                if source in self._time_windows:
                    self._time_windows[source] = TimeWindowStats(window_size=self._window_size)
            else:
                self._stats.clear()
                self._time_windows.clear()
                self._start_time = time.time()


# 全局监控器
_monitor: Optional[Monitor] = None


def get_monitor(window_size: int = 60) -> Monitor:
    """获取监控器实例"""
    global _monitor
    if _monitor is None:
        _monitor = Monitor(window_size=window_size)
    return _monitor


def set_monitor(monitor: Monitor) -> None:
    """设置监控器实例"""
    global _monitor
    _monitor = monitor


__all__ = [
    "Monitor",
    "RequestStats",
    "TimeWindowStats",
    "get_monitor",
    "set_monitor",
]
