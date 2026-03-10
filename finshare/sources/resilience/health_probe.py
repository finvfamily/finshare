"""
健康探测机制 - 自动检测数据源恢复

特性:
- 每5分钟探测一次
- 探测成功立即恢复
- 连续失败累积冷却
- 支持自定义探测函数
"""

import time
import threading
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass
from finshare.logger import logger


@dataclass
class ProbeResult:
    """探测结果"""
    source_name: str
    is_healthy: bool
    response_time: float  # 毫秒
    error_message: Optional[str] = None
    timestamp: float = 0

    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class HealthProbe:
    """
    健康探测管理器

    自动定期探测数据源健康状态，探测成功后立即恢复。
    """

    def __init__(
        self,
        probe_interval: int = 300,  # 探测间隔（秒），默认5分钟
        probe_timeout: int = 10,     # 探测超时（秒）
        success_threshold: int = 1,  # 连续成功次数阈值
    ):
        """
        Args:
            probe_interval: 探测间隔（秒）
            probe_timeout: 探测超时时间（秒）
            success_threshold: 连续成功次数阈值（达到后恢复）
        """
        self.probe_interval = probe_interval
        self.probe_timeout = probe_timeout
        self.success_threshold = success_threshold

        self._probe_funcs: Dict[str, Callable[[], bool]] = {}  # 探测函数
        self._probe_results: Dict[str, List[ProbeResult]] = {}  # 探测结果历史
        self._consecutive_success: Dict[str, int] = {}  # 连续成功次数
        self._last_probe_time: Dict[str, float] = {}    # 上次探测时间

        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[str, bool], None]] = []  # 恢复回调

    def register_probe_func(
        self,
        source_name: str,
        probe_func: Callable[[], bool],
    ) -> None:
        """
        注册探测函数

        Args:
            source_name: 数据源名称
            probe_func: 探测函数，返回 True 表示健康
        """
        with self._lock:
            self._probe_funcs[source_name] = probe_func
            self._probe_results[source_name] = []
            self._consecutive_success[source_name] = 0
            self._last_probe_time[source_name] = 0
            logger.info(f"注册探测函数: {source_name}")

    def unregister_probe_func(self, source_name: str) -> None:
        """注销探测函数"""
        with self._lock:
            self._probe_funcs.pop(source_name, None)
            self._probe_results.pop(source_name, None)
            self._consecutive_success.pop(source_name, None)
            self._last_probe_time.pop(source_name, None)

    def add_recovery_callback(
        self,
        callback: Callable[[str, bool], None],
    ) -> None:
        """
        添加恢复回调

        当数据源从冷却状态恢复时调用。

        Args:
            callback: 回调函数，参数为 (source_name, is_healthy)
        """
        self._callbacks.append(callback)

    def probe(self, source_name: str) -> ProbeResult:
        """
        执行单次探测

        Args:
            source_name: 数据源名称

        Returns:
            探测结果
        """
        probe_func = self._probe_funcs.get(source_name)

        if not probe_func:
            return ProbeResult(
                source_name=source_name,
                is_healthy=False,
                response_time=0,
                error_message="未注册探测函数",
            )

        start_time = time.time()

        try:
            # 在超时时间内执行探测
            is_healthy = probe_func()
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒

            result = ProbeResult(
                source_name=source_name,
                is_healthy=is_healthy,
                response_time=response_time,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result = ProbeResult(
                source_name=source_name,
                is_healthy=False,
                response_time=response_time,
                error_message=str(e),
            )

        # 记录结果
        with self._lock:
            if source_name not in self._probe_results:
                self._probe_results[source_name] = []

            self._probe_results[source_name].append(result)

            # 只保留最近 100 条记录
            if len(self._probe_results[source_name]) > 100:
                self._probe_results[source_name] = self._probe_results[source_name][-100:]

            # 更新连续成功次数
            if result.is_healthy:
                self._consecutive_success[source_name] = self._consecutive_success.get(source_name, 0) + 1
            else:
                self._consecutive_success[source_name] = 0

            self._last_probe_time[source_name] = time.time()

        # 记录日志
        if result.is_healthy:
            logger.debug(
                f"[{source_name}] 探测成功 | "
                f"响应时间: {result.response_time:.0f}ms | "
                f"连续成功: {self._consecutive_success.get(source_name, 0)}"
            )
        else:
            logger.debug(
                f"[{source_name}] 探测失败 | "
                f"错误: {result.error_message}"
            )

        return result

    def should_restore(self, source_name: str) -> bool:
        """
        判断是否应该恢复数据源

        Args:
            source_name: 数据源名称

        Returns:
            是否应该恢复
        """
        consecutive = self._consecutive_success.get(source_name, 0)
        return consecutive >= self.success_threshold

    def probe_all(self) -> Dict[str, ProbeResult]:
        """
        探测所有已注册的数据源

        Returns:
            各数据源的探测结果
        """
        results = {}

        with self._lock:
            source_names = list(self._probe_funcs.keys())

        for source_name in source_names:
            result = self.probe(source_name)
            results[source_name] = result

            # 检查是否应该恢复
            if self.should_restore(source_name):
                self._notify_recovery(source_name)

        return results

    def get_status(self, source_name: str) -> dict:
        """
        获取数据源健康状态

        Args:
            source_name: 数据源名称

        Returns:
            状态信息
        """
        with self._lock:
            results = self._probe_results.get(source_name, [])
            consecutive = self._consecutive_success.get(source_name, 0)
            last_probe = self._last_probe_time.get(source_name, 0)

        # 计算成功率
        if results:
            success_count = sum(1 for r in results if r.is_healthy)
            success_rate = success_count / len(results)
        else:
            success_rate = 0.0

        return {
            "source_name": source_name,
            "is_registered": source_name in self._probe_funcs,
            "last_probe_time": last_probe,
            "consecutive_success": consecutive,
            "success_threshold": self.success_threshold,
            "should_restore": self.should_restore(source_name),
            "recent_results_count": len(results),
            "recent_success_rate": success_rate,
        }

    def start_auto_probe(self) -> None:
        """启动自动探测"""
        if self._running:
            logger.warning("自动探测已在运行中")
            return

        self._running = True
        self._thread = threading.Thread(target=self._auto_probe_loop, daemon=True)
        self._thread.start()
        logger.info("自动探测已启动")

    def stop_auto_probe(self) -> None:
        """停止自动探测"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("自动探测已停止")

    def _auto_probe_loop(self) -> None:
        """自动探测循环"""
        while self._running:
            try:
                self.probe_all()
            except Exception as e:
                logger.error(f"自动探测循环异常: {e}")

            # 等待下次探测
            time.sleep(self.probe_interval)

    def _notify_recovery(self, source_name: str) -> None:
        """通知恢复"""
        logger.info(f"[{source_name}] 健康探测通过，准备恢复")

        for callback in self._callbacks:
            try:
                callback(source_name, True)
            except Exception as e:
                logger.error(f"恢复回调执行失败: {e}")


# 全局健康探测实例
health_probe = HealthProbe()


def get_health_probe() -> HealthProbe:
    """获取全局健康探测实例"""
    return health_probe
