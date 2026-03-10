"""
异步客户端

提供异步数据获取接口。
"""

import asyncio
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from finshare.logger import logger
from finshare.sources.manager import DataSourceManager


class AsyncDataSourceManager:
    """
    异步数据源管理器

    提供异步方法获取金融数据。
    """

    def __init__(self, max_workers: int = 10):
        """
        初始化异步数据源管理器

        Args:
            max_workers: 最大并发工作线程数
        """
        self._sync_manager = DataSourceManager()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def _run_in_executor(self, func, *args, **kwargs):
        """在线程池中运行同步函数"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(
            self._executor,
            lambda: func(*args, **kwargs)
        )

    async def get_snapshot(self, code: str) -> pd.DataFrame:
        """
        异步获取实时快照

        Args:
            code: 股票代码

        Returns:
            DataFrame
        """
        snapshot = await self._run_in_executor(
            self._sync_manager.get_snapshot_data, code
        )
        if snapshot:
            # 转换为DataFrame
            return pd.DataFrame([{
                "fs_code": snapshot.code,
                "last_price": snapshot.last_price,
                "volume": snapshot.volume,
                "amount": snapshot.amount,
                "timestamp": snapshot.timestamp,
            }])
        return pd.DataFrame()

    async def get_kline(
        self,
        code: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        frequency: str = "d",
        adjustment: str = "qfq",
    ) -> pd.DataFrame:
        """
        异步获取K线数据

        Args:
            code: 股票代码
            start: 开始日期
            end: 结束日期
            frequency: 频率 (d=日线, w=周线, m=月线, 1/5/15/30/60=分钟线)
            adjustment: 复权类型 (qfq=前复权, hfq=后复权, 空=不复权)

        Returns:
            DataFrame
        """
        return await self._run_in_executor(
            self._sync_manager.get_kline,
            code, start, end, frequency, adjustment
        )

    async def get_minutely_data(
        self,
        code: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        frequency: int = 1,
    ) -> pd.DataFrame:
        """
        异步获取分钟线数据

        Args:
            code: 股票代码
            start: 开始时间
            end: 结束时间
            frequency: 频率 (1/5/15/30/60分钟)

        Returns:
            DataFrame
        """
        return await self._run_in_executor(
            self._sync_manager.get_minutely_data,
            code, start, end, frequency
        )

    async def get_batch_snapshot(self, codes: List[str]) -> pd.DataFrame:
        """
        批量异步获取实时快照

        Args:
            codes: 股票代码列表

        Returns:
            DataFrame
        """
        tasks = [self.get_snapshot(code) for code in codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"获取 {codes[i]} 失败: {result}")
            elif result is not None and not result.empty:
                valid_results.append(result)

        if valid_results:
            return pd.concat(valid_results, ignore_index=True)
        return pd.DataFrame()

    async def get_batch_kline(
        self,
        codes: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        frequency: str = "d",
        adjustment: str = "qfq",
    ) -> Dict[str, pd.DataFrame]:
        """
        批量异步获取K线数据

        Args:
            codes: 股票代码列表
            start: 开始日期
            end: 结束日期
            frequency: 频率
            adjustment: 复权类型

        Returns:
            Dict[code, DataFrame]
        """
        tasks = [
            self.get_kline(code, start, end, frequency, adjustment)
            for code in codes
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        data_dict = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"获取 {codes[i]} 失败: {result}")
            elif result is not None and not result.empty:
                data_dict[codes[i]] = result

        return data_dict

    def close(self):
        """关闭线程池"""
        self._executor.shutdown(wait=True)


# 全局异步管理器
_async_manager: Optional[AsyncDataSourceManager] = None


def get_async_manager(max_workers: int = 10) -> AsyncDataSourceManager:
    """
    获取异步数据源管理器

    Args:
        max_workers: 最大并发工作线程数

    Returns:
        AsyncDataSourceManager
    """
    global _async_manager
    if _async_manager is None:
        _async_manager = AsyncDataSourceManager(max_workers=max_workers)
    return _async_manager


__all__ = [
    "AsyncDataSourceManager",
    "get_async_manager",
]
