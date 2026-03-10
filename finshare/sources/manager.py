# sources/manager.py
"""
数据源管理器

用于管理实时快照数据的获取，支持多数据源自动切换和故障恢复。

数据源优先级（按配置）：
1. 通达信(tdx) - 实时快照首选，速度快
2. 东方财富 - 支持历史K线和实时快照
3. 腾讯 - 支持历史K线和实时快照
4. 新浪 - 仅支持实时快照
5. BaoStock - 历史K线首选（支持前复权），实时较慢

统一单位规范：
- 价格: 元
- 成交量: 手
- 成交额: 元
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import time
import pandas as pd

from finshare.models.data_models import SnapshotData
from finshare.sources.base_source import BaseDataSource
from finshare.sources.tencent_source import TencentDataSource
from finshare.sources.sina_source import SinaDataSource
from finshare.sources.eastmoney_source import EastMoneyDataSource
from finshare.logger import logger
from finshare.config.settings import config


# 延迟导入新数据源，避免依赖问题
def _get_baostock_source():
    """获取 BaoStock 数据源（延迟导入）"""
    try:
        from finshare.sources.baostock_source import BaoStockDataSource

        return BaoStockDataSource()
    except ImportError as e:
        logger.warning(f"BaoStock 数据源不可用: {e}")
        return None


def _get_tdx_source():
    """获取通达信数据源（延迟导入）"""
    try:
        from finshare.sources.tdx_source import TdxDataSource

        return TdxDataSource()
    except ImportError as e:
        logger.warning(f"通达信数据源不可用: {e}")
        return None


class DataSourceManager:
    """数据源管理器 - 管理实时快照数据获取"""

    def __init__(self):
        self.sources = self._initialize_sources()
        self.source_status = {}

    def _initialize_sources(self) -> Dict[str, BaseDataSource]:
        """初始化数据源"""
        sources = {}

        for source_name in config.data_source.source_priority:
            try:
                source = None

                if source_name == "tencent":
                    source = TencentDataSource()
                elif source_name == "sina":
                    source = SinaDataSource()
                elif source_name == "eastmoney":
                    source = EastMoneyDataSource()
                elif source_name == "baostock":
                    source = _get_baostock_source()
                elif source_name == "tdx":
                    source = _get_tdx_source()
                else:
                    logger.warning(f"未知的数据源: {source_name}")
                    continue

                if source:
                    sources[source_name] = source
                    logger.info(f"初始化数据源: {source_name}")
                else:
                    logger.warning(f"数据源 {source_name} 初始化返回空")

            except Exception as e:
                logger.error(f"初始化数据源 {source_name} 失败: {e}")

        return sources

    def get_snapshot_data(self, code: str) -> Optional[SnapshotData]:
        """获取快照数据（自动选择数据源）"""
        for source_name in config.data_source.source_priority:
            if not self._is_source_available(source_name):
                continue

            source = self.sources.get(source_name)
            if not source:
                continue

            try:
                snapshot = source.get_snapshot_data(code)
                if snapshot:
                    logger.info(
                        f"[数据源:{source_name}] 获取快照成功: {code}, 价格={snapshot.last_price}"
                    )

                    # 确保快照中的代码是完整格式
                    if hasattr(source, "_ensure_full_code"):
                        snapshot.code = source._ensure_full_code(snapshot.code)

                    return snapshot
            except Exception as e:
                logger.warning(f"从 {source_name} 获取快照失败: {e}")
                self._record_source_failure(source_name, str(e))

        return None

    def get_minutely_data(
        self,
        code: str,
        start: str = None,
        end: str = None,
        freq: int = 5,
        adjust: str = None,
    ) -> Optional[pd.DataFrame]:
        """获取分钟K线数据

        Args:
            code: 股票代码 (支持 000001.SZ, SZ000001, 000001 等格式)
            start: 开始时间 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
            end: 结束时间 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
            freq: 频率 (1/5/15/30/60 分钟)
            adjust: 复权类型 qfq/hfq/None

        Returns:
            DataFrame 或 None
        """
        from finshare.models.data_models import AdjustmentType

        # 解析时间
        if start:
            try:
                if " " in start:
                    start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                else:
                    start_dt = datetime.strptime(start, "%Y-%m-%d")
            except ValueError:
                start_dt = datetime.now()
        else:
            start_dt = datetime.now()

        if end:
            try:
                if " " in end:
                    end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
                else:
                    end_dt = datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                end_dt = datetime.now()
        else:
            end_dt = datetime.now()

        # 转换复权类型
        adjustment = AdjustmentType.NONE
        if adjust == "qfq":
            adjustment = AdjustmentType.PREVIOUS
        elif adjust == "hfq":
            adjustment = AdjustmentType.POST

        # 优先使用东方财富（支持分钟线）
        source_name = "eastmoney"
        source = self.sources.get(source_name)

        if not source or not hasattr(source, "get_minutely_data"):
            logger.warning(f"数据源 {source_name} 不可用或不支持分钟线")
            return None

        try:
            data = source.get_minutely_data(
                code=code,
                start=start_dt,
                end=end_dt,
                freq=freq,
                adjustment=adjustment,
            )

            if data is not None and len(data) > 0:
                logger.info(
                    f"[数据源:{source_name}] 获取分钟线成功: {code}, "
                    f"freq={freq}min, {len(data)}条"
                )
                # 转换为 DataFrame
                df = pd.DataFrame([d.model_dump() for d in data])
                return df
            else:
                logger.warning(f"从 {source_name} 获取分钟线数据为空")
                return None

        except Exception as e:
            logger.warning(f"从 {source_name} 获取分钟线失败: {e}")
            return None

    def get_historical_data(
        self,
        code: str,
        start: str = None,
        end: str = None,
        period: str = "daily",
        adjust: str = None,
    ) -> Optional[pd.DataFrame]:
        """获取历史K线数据（自动选择数据源）

        Args:
            code: 股票代码（6位）
            start: 开始日期 YYYY-MM-DD
            end: 结束日期 YYYY-MM-DD
            period: 周期 daily/weekly/monthly
            adjust: 复权类型 qfq/hfq/None

        Returns:
            DataFrame 或 None
        """
        # 转换日期字符串为 date 对象
        from datetime import datetime
        from finshare.models.data_models import AdjustmentType

        start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
        end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else None

        # 转换复权类型
        adjustment = AdjustmentType.NONE
        if adjust == "qfq":
            adjustment = AdjustmentType.PREVIOUS  # 前复权
        elif adjust == "hfq":
            adjustment = AdjustmentType.POST  # 后复权

        for source_name in config.data_source.source_priority:
            if not self._is_source_available(source_name):
                continue

            source = self.sources.get(source_name)
            if not source:
                continue

            try:
                data = source.get_historical_data(
                    code=code,
                    start_date=start_date,
                    end_date=end_date,
                    adjustment=adjustment,
                )
                if data is not None and len(data) > 0:
                    logger.info(
                        f"[数据源:{source_name}] 获取历史数据成功: {code}, {len(data)}条"
                    )
                    # 转换为 DataFrame
                    import pandas as pd
                    df = pd.DataFrame([d.model_dump() for d in data])
                    return df
            except Exception as e:
                logger.warning(f"从 {source_name} 获取历史数据失败: {e}")
                self._record_source_failure(source_name, str(e))

        return None

    def get_batch_snapshots(self, codes: List[str]) -> Dict[str, SnapshotData]:
        """批量获取快照数据"""
        results = {}

        # 确保传入的代码都是完整格式
        full_codes = []
        for code in codes:
            # 尝试使用第一个可用的数据源来确保代码格式
            for source_name in config.data_source.source_priority:
                source = self.sources.get(source_name)
                if source and hasattr(source, "_ensure_full_code"):
                    full_codes.append(source._ensure_full_code(code))
                    break
            else:
                full_codes.append(code)

        logger.debug(f"批量获取快照，输入代码: {codes}")
        logger.debug(f"批量获取快照，完整代码: {full_codes}")

        for source_name in config.data_source.source_priority:
            if not self._is_source_available(source_name):
                continue

            source = self.sources.get(source_name)
            if not source:
                continue

            try:
                # 获取尚未成功的代码
                remaining_codes = [code for code in full_codes if code not in results]
                if not remaining_codes:
                    break

                batch_results = source.get_batch_snapshots(remaining_codes)

                # 过滤掉None值，并确保代码格式正确
                valid_results = {}
                for k, v in batch_results.items():
                    if v is not None:
                        # 确保键和值中的代码都是完整格式
                        if hasattr(source, "_ensure_full_code"):
                            full_key = source._ensure_full_code(k)
                            v.code = source._ensure_full_code(v.code)
                            valid_results[full_key] = v
                        else:
                            valid_results[k] = v

                results.update(valid_results)

                logger.info(
                    f"[数据源:{source_name}] 批量获取快照: {len(valid_results)}/{len(remaining_codes)} 成功"
                )

                # 如果已经获取了所有代码，提前退出
                if len(results) >= len(full_codes):
                    break

            except Exception as e:
                logger.warning(f"从 {source_name} 批量获取快照失败: {e}")
                self._record_source_failure(source_name, str(e))

        return results

    def _is_source_available(self, source_name: str) -> bool:
        """检查数据源是否可用"""
        # 检查冷却状态
        if source_name in self.source_status:
            status = self.source_status[source_name]
            if status.get("cool_down_until"):
                if datetime.now() < status["cool_down_until"]:
                    logger.debug(f"数据源 {source_name} 仍在冷却中")
                    return False

        return True

    def _record_source_failure(self, source_name: str, error_msg: str):
        """记录数据源失败（直接进入24小时冷却）"""
        cooldown_hours = config.data_source.failure_cooldown_hours
        cool_down_until = datetime.now() + timedelta(hours=cooldown_hours)

        self.source_status[source_name] = {
            "last_failure": datetime.now(),
            "cool_down_until": cool_down_until,
            "error_msg": error_msg,
        }

        logger.warning(
            f"数据源 {source_name} 请求失败: {error_msg}，"
            f"进入{cooldown_hours}小时冷却，将切换到其他数据源"
        )

    def reset_source_status(self, source_name: str = None):
        """重置数据源状态"""
        if source_name:
            if source_name in self.source_status:
                del self.source_status[source_name]
                logger.info(f"重置数据源状态: {source_name}")
        else:
            self.source_status = {}
            logger.info("重置所有数据源状态")

    def get_source_stats(self) -> Dict[str, Dict]:
        """获取数据源统计信息"""
        stats = {}

        for source_name, source in self.sources.items():
            status = self.source_status.get(source_name, {})
            cool_down_until = status.get("cool_down_until")

            # 计算剩余冷却时间
            remaining_hours = 0
            if cool_down_until and datetime.now() < cool_down_until:
                remaining_hours = (cool_down_until - datetime.now()).total_seconds() / 3600

            stats[source_name] = {
                "available": self._is_source_available(source_name),
                "last_failure": status.get("last_failure"),
                "cool_down_until": cool_down_until,
                "remaining_hours": round(remaining_hours, 1),
                "error_msg": status.get("error_msg"),
            }

        return stats

    def get_active_source(self, code: str = None) -> Optional[BaseDataSource]:
        """获取可用的数据源"""
        for source_name in config.data_source.source_priority:
            if not self._is_source_available(source_name):
                continue

            source = self.sources.get(source_name)
            if source:
                return source

        return None

    def test_snapshot(self, code: str = "159941"):
        """测试快照数据获取（示例方法）"""
        print(f"测试快照: {code}")

        snapshot = self.get_snapshot_data(code)
        if snapshot:
            print(f"✓ 快照数据获取成功: {snapshot.code}")
            print(f"  最新价格: {snapshot.last_price}")
            print(f"  成交量: {snapshot.volume}")
        else:
            print(f"✗ 快照数据获取失败: {code}")

        return snapshot
