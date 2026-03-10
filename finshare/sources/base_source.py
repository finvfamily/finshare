# sources/base_source.py (完整代码)
import time
import random
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict

import requests

from finshare.config.settings import config
from finshare.models.data_models import HistoricalData, SnapshotData, AdjustmentType
from finshare.logger import logger
from finshare.sources.resilience import (
    SmartCooldown,
    cooldown_manager,
    RetryHandler,
    retry_handler,
    HealthProbe,
    health_probe,
)

# User-Agent 池（模拟不同浏览器）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


class BaseDataSource(ABC):
    """数据源抽象基类 - 支持智能冷却、重试、健康探测"""

    # 类级别的请求时间记录（线程安全）
    _last_request_time: Dict[str, float] = {}  # source_name -> last_request_timestamp
    _rate_limit_lock = threading.Lock()  # 全局锁，确保请求间隔

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.base_url = None
        self.session = self._create_session()
        # 使用配置的请求间隔
        self.request_interval = config.data_source.request_interval
        self.request_jitter = 0.5  # 请求间隔随机抖动范围（±50%）

        # 使用全局弹性模块
        self._cooldown_mgr = cooldown_manager
        self._retry_handler = retry_handler
        self._health_probe = health_probe

    @staticmethod
    def get_random_user_agent() -> str:
        """获取随机User-Agent"""
        return random.choice(USER_AGENTS)

    def _create_session(self):
        """创建HTTP会话"""
        session = requests.Session()

        # 为 session 添加默认超时设置
        original_request = session.request

        def request_with_timeout(method, url, **kwargs):
            if "timeout" not in kwargs:
                kwargs["timeout"] = config.data_source.request_timeout
            return original_request(method, url, **kwargs)

        session.request = request_with_timeout

        return session

    def _rate_limit(self):
        """请求频率限制（线程安全，带随机抖动）"""
        # 计算带随机抖动的间隔时间
        jitter = random.uniform(-self.request_jitter, self.request_jitter)
        actual_interval = self.request_interval * (1 + jitter)
        actual_interval = max(0.5, actual_interval)  # 最小0.5秒

        with self._rate_limit_lock:
            last_time = self._last_request_time.get(self.source_name, 0)
            elapsed = time.time() - last_time
            if elapsed < actual_interval:
                sleep_time = actual_interval - elapsed
                # 先更新时间再释放锁，避免其他线程同时请求
                self._last_request_time[self.source_name] = time.time() + sleep_time
            else:
                sleep_time = 0
                self._last_request_time[self.source_name] = time.time()

        # 在锁外sleep，不阻塞其他数据源
        if sleep_time > 0:
            time.sleep(sleep_time)

    # ============ 智能冷却接口 ============

    def is_in_cooldown(self) -> bool:
        """检查数据源是否处于冷却状态"""
        return self._cooldown_mgr.is_in_cooldown(self.source_name)

    def get_cooldown_remaining(self) -> float:
        """获取剩余冷却时间（秒）"""
        return self._cooldown_mgr.get_cooldown_remaining(self.source_name)

    def _enter_cooldown(
        self,
        reason: str = "request_failed",
        http_status: Optional[int] = None,
    ):
        """进入智能冷却状态（根据错误类型分级冷却）"""
        # 判断错误类型
        error_type = self._classify_error(reason, http_status)
        self._cooldown_mgr.record_failure(
            self.source_name,
            error_type=error_type,
            http_status=http_status,
        )

    def _exit_cooldown(self):
        """冷却结束（请求成功时调用）"""
        self._cooldown_mgr.record_success(self.source_name)

    def _classify_error(self, reason: str, http_status: Optional[int] = None) -> str:
        """根据错误信息分类错误类型"""
        if http_status:
            if http_status == 429:
                return "rate_limit"
            elif http_status == 403:
                return "forbidden"
            elif http_status == 503:
                return "service_unavailable"

        reason_lower = reason.lower()
        if "timeout" in reason_lower:
            return "timeout"
        elif "connection" in reason_lower:
            return "connection_error"
        elif "refused" in reason_lower:
            return "connection_error"

        return "default"

    # ============ 重试处理接口 ============

    def _make_request_with_retry(
        self,
        url: str,
        params: Dict = None,
        headers: Dict = None,
    ) -> Optional[Dict]:
        """
        发送HTTP请求（带重试机制）

        失败后会进入智能冷却，不会直接切换数据源。
        """
        # 检查是否在冷却中
        if self.is_in_cooldown():
            remaining = self.get_cooldown_remaining()
            logger.debug(
                f"{self.source_name} 在冷却中，剩余 {remaining:.0f}秒"
            )
            return None

        self._rate_limit()

        # 合并请求头，使用随机User-Agent
        request_headers = {"User-Agent": self.get_random_user_agent()}
        if headers:
            request_headers.update(headers)

        # 使用重试机制
        try:
            return self._retry_handler.execute(
                self._do_request,
                url,
                params,
                request_headers,
            )
        except Exception as e:
            # 记录失败并进入冷却
            http_status = getattr(e, "response", None)
            if http_status:
                http_status = http_status.status_code

            self._enter_cooldown(str(e), http_status)
            return None

    def _do_request(
        self,
        url: str,
        params: Dict,
        request_headers: Dict,
    ) -> Optional[Dict]:
        """
        执行实际请求（供重试机制调用）
        """
        response = self.session.get(url, params=params, headers=request_headers)

        # 检测错误响应
        if response.status_code == 429:
            self._enter_cooldown("HTTP 429 Too Many Requests", http_status=429)
            raise Exception("HTTP 429 Rate Limited")

        if response.status_code == 403:
            self._enter_cooldown("HTTP 403 Forbidden", http_status=403)
            raise Exception("HTTP 403 Forbidden")

        if response.status_code == 503:
            self._enter_cooldown("HTTP 503 Service Unavailable", http_status=503)
            raise Exception("HTTP 503 Service Unavailable")

        if response.status_code >= 400:
            self._enter_cooldown(f"HTTP {response.status_code}", http_status=response.status_code)
            raise Exception(f"HTTP {response.status_code}")

        response.raise_for_status()

        # 尝试解析JSON
        try:
            return response.json()
        except ValueError:
            return response.text

    # ============ 兼容旧接口 ============

    def _make_request(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        """
        发送HTTP请求（兼容旧接口，内部调用重试版本）
        """
        return self._make_request_with_retry(url, params, headers)

    # ============ 抽象方法 ============

    @abstractmethod
    def get_historical_data(
        self,
        code: str,
        start_date: date,
        end_date: date,
        adjustment: AdjustmentType = AdjustmentType.NONE,
    ) -> List[HistoricalData]:
        """获取历史数据"""
        pass

    @abstractmethod
    def get_snapshot_data(self, code: str) -> Optional[SnapshotData]:
        """获取交易快照数据"""
        pass

    @abstractmethod
    def get_batch_snapshots(self, codes: List[str]) -> Dict[str, SnapshotData]:
        """批量获取快照数据"""
        pass

    # ============ 健康探测 ============

    def register_health_probe(self) -> None:
        """注册健康探测函数"""
        def probe_func() -> bool:
            """探测函数：尝试获取一个简单数据"""
            try:
                # 子类可覆盖此方法，提供更精准的探测
                result = self.health_check()
                return result
            except Exception:
                return False

        self._health_probe.register_probe_func(self.source_name, probe_func)

        # 添加恢复回调
        self._health_probe.add_recovery_callback(self._on_health_recovered)

    def _on_health_recovered(self, source_name: str, is_healthy: bool) -> None:
        """健康探测恢复回调"""
        if is_healthy and source_name == self.source_name:
            logger.info(f"{self.source_name} 健康探测通过，已恢复可用")

    def health_check(self) -> bool:
        """
        健康检查（子类可覆盖）

        Returns:
            True 表示健康
        """
        # 默认实现：尝试一次简单的快照请求
        try:
            # 尝试获取上证指数的快照
            result = self.get_snapshot_data("000001.SH")
            return result is not None
        except Exception:
            return False

    # ============ 状态查询 ============

    def get_status(self) -> dict:
        """获取数据源状态"""
        return {
            "source_name": self.source_name,
            "is_in_cooldown": self.is_in_cooldown(),
            "cooldown_remaining": self.get_cooldown_remaining(),
            **self._cooldown_mgr.get_status(self.source_name),
        }

    # ============ 代码格式转换 ============

    def _ensure_full_code(self, code: str) -> str:
        """
        确保返回完整代码格式（子类应覆盖此方法）

        支持输入格式:
        - sz.159915 / sh.600519 (BaoStock格式) -> 159915.SH / 159915.SZ
        - SZ159915 / SH600519 (标准格式) -> 保持不变
        - 159915 / 600519 (纯数字) -> 自动添加前缀
        - 000001.SZ / 600001.SH -> 保持不变

        返回格式: 000001.SZ / 600001.SH
        """
        if not code:
            return code

        code = code.strip().upper()

        # 已经是标准格式 (带点)
        if "." in code:
            return code

        # 处理 SZ/SH/BJ 前缀 (无点)
        prefix_map = {"SZ": "SZ", "SH": "SH", "BJ": "BJ", "HK": "HK", "US": "US"}
        for prefix, market in prefix_map.items():
            if code.startswith(prefix):
                num_code = code[len(prefix):]
                return f"{num_code}.{market}"

        # 纯数字代码，根据首位判断市场
        if code.isdigit():
            first = code[0]
            if first in ["6", "5"]:
                return f"{code}.SH"
            elif first in ["0", "1", "2", "3"]:
                return f"{code}.SZ"
            elif first == "9":
                if code.startswith("90"):
                    return f"{code}.SH"
                else:
                    return f"{code}.BJ"

        return code  # 无法确定，返回原样

    def _get_market_type(self, code: str) -> str:
        """
        根据代码获取市场类型

        Args:
            code: 股票代码 (支持多种格式)

        Returns:
            市场类型: sh, sz, bj, hk, us
        """
        # 标准化代码格式
        fs_code = self._ensure_full_code(code)

        if "." in fs_code:
            market = fs_code.split(".")[1].lower()
            return market

        # 尝试从原始代码判断
        code_upper = code.upper()
        if code_upper.startswith("SH"):
            return "sh"
        elif code_upper.startswith("SZ"):
            return "sz"
        elif code_upper.startswith("BJ"):
            return "bj"

        return "sh"  # 默认上海
