"""
BaseClient - 数据客户端公共基类

提供HTTP请求、频率限制、User-Agent轮换等公共能力，
供 IndexClient、IndustryClient、ValuationClient 等继承使用。
"""

import time
import random
import requests
from typing import Optional, Dict

from finshare.logger import logger


class BaseClient:
    """数据客户端公共基类 - 提供HTTP请求、频率限制、UA轮换"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self, source_name: str, request_interval: float = 0.5):
        """
        初始化基类

        Args:
            source_name: 数据源名称，用于日志标识
            request_interval: 请求间隔（秒），默认 0.5s
        """
        self.source_name = source_name
        self.session = requests.Session()
        self.request_interval = request_interval

    def get_random_user_agent(self) -> str:
        """随机获取一个 User-Agent"""
        return random.choice(self.USER_AGENTS)

    def _rate_limit(self):
        """简单的频率限制"""
        time.sleep(self.request_interval)

    def _make_request(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Optional[Dict]:
        """
        发送 HTTP GET 请求并返回 JSON 结果

        Args:
            url: 请求地址
            params: 查询参数
            headers: 额外请求头（会合并到默认头之后）
            timeout: 超时时间（秒），默认 30

        Returns:
            解析后的 JSON 字典，请求失败时返回 None
        """
        self._rate_limit()

        request_headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "application/json, text/plain, */*",
        }
        if headers:
            request_headers.update(headers)

        try:
            response = self.session.get(
                url, params=params, headers=request_headers, timeout=timeout
            )

            if response.status_code >= 400:
                logger.warning(
                    f"[{self.source_name}] HTTP 请求失败: {response.status_code} {url}"
                )
                return None

            return response.json()

        except requests.RequestException as e:
            logger.warning(f"[{self.source_name}] 请求异常: {e}")
            return None
        except ValueError as e:
            logger.warning(f"[{self.source_name}] JSON 解析失败: {e}")
            return None

    def _ensure_full_code(self, code: str) -> str:
        """
        将股票代码标准化为 000001.SZ 格式

        支持输入格式:
        - 000001.SZ / 600519.SH  (已是标准格式，直接返回)
        - SZ000001 / SH600519     (前缀格式)
        - 000001 / 600519         (纯数字，自动识别市场)

        市场判断规则（首位数字）:
        - 6 / 5 → .SH
        - 0 / 1 / 2 / 3 → .SZ
        - 4 / 8 → .BJ
        - 9 → .SH

        Returns:
            标准格式代码，如 000001.SZ
        """
        if not code:
            return code

        code = code.strip().upper()

        # 已经是标准 XXXXXX.XX 格式
        if "." in code:
            return code

        # 处理 SZ/SH/BJ 前缀格式
        prefix_map = {"SZ": "SZ", "SH": "SH", "BJ": "BJ"}
        for prefix, market in prefix_map.items():
            if code.startswith(prefix):
                num_code = code[len(prefix):]
                return f"{num_code}.{market}"

        # 纯数字，按首位自动识别
        if code.isdigit():
            first = code[0]
            if first in ("6", "5", "9"):
                return f"{code}.SH"
            elif first in ("0", "1", "2", "3"):
                return f"{code}.SZ"
            elif first in ("4", "8"):
                return f"{code}.BJ"

        return code

    def close(self):
        """关闭 HTTP Session"""
        self.session.close()
