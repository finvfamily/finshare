# sources/fund_source.py
"""
基金数据源实现

支持获取基金净值、基金信息等数据。

数据源:
- 天天基金: 基金净值数据
"""

import json
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict

from finshare.sources.base_source import BaseDataSource
from finshare.models.data_models import FundData, SnapshotData, HistoricalData
from finshare.logger import logger


class FundDataSource(BaseDataSource):
    """基金数据源实现"""

    def __init__(self):
        super().__init__("fund")
        self.eastmoney_base_url = "http://fund.eastmoney.com"
        self.jjj_base_url = "https://jjj.eastmoney.com"

    def get_fund_nav(self, code: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[FundData]:
        """
        获取基金净值数据

        Args:
            code: 基金代码 (如 161039, 000001)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[FundData] 基金净值数据列表
        """
        try:
            # 格式化基金代码
            fund_code = self._format_fund_code(code)

            # 默认日期范围
            if end_date is None:
                end_date = date.today()
            if start_date is None:
                start_date = end_date - timedelta(days=90)

            # 东方财富基金净值API
            # http://fund.eastmoney.com/pingzhongdata/161039.js?v=20240101
            url = f"{self.eastmoney_base_url}/pingzhongdata/{fund_code}.js"

            # 添加时间戳避免缓存
            params = {"v": datetime.now().strftime("%Y%m%d%H%M%S")}

            logger.debug(f"请求基金净值: {fund_code}, {start_date} - {end_date}")

            response_data = self._make_request(url, params)

            if not response_data:
                logger.warning(f"基金净值请求无响应: {fund_code}")
                return []

            # 解析基金净值数据
            fund_data = self._parse_fund_nav(response_data, fund_code)

            if not fund_data:
                logger.warning(f"基金净值解析失败: {fund_code}")
                return []

            # 筛选日期范围
            filtered_data = [d for d in fund_data if start_date <= d.nav_date <= end_date]

            if filtered_data:
                logger.info(f"获取基金净值成功: {fund_code}, 共{len(filtered_data)}条")
            else:
                logger.warning(f"基金净值为空: {fund_code}")

            return filtered_data

        except Exception as e:
            logger.error(f"获取基金净值失败 {code}: {e}")
            return []

    def get_fund_info(self, code: str) -> Optional[dict]:
        """
        获取基金基本信息

        Args:
            code: 基金代码

        Returns:
            基金信息字典
        """
        try:
            fund_code = self._format_fund_code(code)

            # 东方财富基金信息API
            url = f"{self.eastmoney_base_url}/jjj/{fund_code}.html"

            response_data = self._make_request(url)

            if not response_data:
                return None

            # 解析基金信息
            info = self._parse_fund_info(response_data, fund_code)

            return info

        except Exception as e:
            logger.error(f"获取基金信息失败 {code}: {e}")
            return None

    def get_fund_list(self, market: str = "all") -> List[dict]:
        """
        获取基金列表

        Args:
            market: 市场类型 (all, sh, sz)

        Returns:
            基金列表
        """
        try:
            # 东方财富基金列表API
            url = f"{self.eastmoney_base_url}/data/fund_rank_list"

            params = {
                "m": market,
                "dt": "net",
                "sd": "",
                "ed": "",
                "qdii": "",
                "ltfc": "true",
                "py": "true",
                "zq": "true",
                "vip": "true",
            }

            response_data = self._make_request(url, params)

            if not response_data:
                return []

            # 解析基金列表
            fund_list = self._parse_fund_list(response_data)

            return fund_list

        except Exception as e:
            logger.error(f"获取基金列表失败: {e}")
            return []

    def _format_fund_code(self, code: str) -> str:
        """格式化基金代码"""
        code = code.strip()

        # 移除可能的字母前缀
        code = code.lstrip("OF")

        # 确保是6位数字
        if len(code) < 6:
            code = code.zfill(6)

        return code

    def _parse_fund_nav(self, response_data: str, code: str) -> List[FundData]:
        """
        解析基金净值数据

        天天基金数据格式:
        var Data_netWorthTrend = [{"x": timestamp, "y": nav, "equityReturn": change_pct}, ...]
        x: Unix timestamp in milliseconds
        y: 单位净值
        equityReturn: 涨跌幅(%)
        """
        fund_data_list = []
        fund_name = code

        try:
            # 提取基金名称
            name_match = 'var fS_name = "'
            if name_match in response_data:
                start = response_data.find(name_match) + len(name_match)
                end = response_data.find('"', start)
                fund_name = response_data[start:end]

            # 提取净值数据 - Data_netWorthTrend 包含每日净值
            data_pattern = "var Data_netWorthTrend = "
            if data_pattern not in response_data:
                logger.warning(f"未找到基金净值数据: {code}")
                return []

            start = response_data.find(data_pattern) + len(data_pattern)
            # 找到下一个分号
            end = response_data.find(";", start)
            if end == -1:
                end = response_data.find("\n", start)

            data_str = response_data[start:end].strip()

            # 解析JSON数据
            if data_str.startswith("["):
                data_list = json.loads(data_str)
            else:
                # 可能需要处理其他格式
                return []

            for item in data_list:
                try:
                    # 新格式: {"x": timestamp_ms, "y": nav, "equityReturn": change_pct}
                    if not isinstance(item, dict):
                        continue

                    # 解析时间戳
                    timestamp_ms = item.get("x")
                    if not timestamp_ms:
                        continue

                    # 转换为日期
                    nav_date = datetime.fromtimestamp(timestamp_ms / 1000).date()

                    # 解析净值
                    nav = float(item.get("y")) if item.get("y") else 0

                    # 涨跌幅
                    change_pct = float(item.get("equityReturn")) if item.get("equityReturn") else 0

                    # 累计净值 - 需要从另一个字段获取，这里暂时用nav代替
                    nav_acc = nav

                    # 计算涨跌额
                    change = nav * change_pct / 100 if change_pct else 0

                    fund_data = FundData(
                        code=code,
                        name=fund_name,
                        nav=nav,
                        nav_acc=nav_acc,
                        change=change,
                        change_pct=change_pct,
                        nav_date=nav_date,
                        data_source=self.source_name,
                    )
                    fund_data_list.append(fund_data)

                except (ValueError, TypeError, KeyError) as e:
                    logger.debug(f"解析净值条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析基金净值数据失败: {e}")

        return fund_data_list

    def _parse_fund_info(self, response_data: str, code: str) -> Optional[dict]:
        """解析基金信息"""
        try:
            info = {"code": code}

            # 提取基金规模
            scale_pattern = 'fundScale":'
            if scale_pattern in response_data:
                start = response_data.find(scale_pattern) + len(scale_pattern)
                end = response_data.find(",", start)
                scale_str = response_data[start:end].strip().strip('"')
                info["scale"] = scale_str

            # 提取基金经理
            manager_pattern = 'fundManager":'
            if manager_pattern in response_data:
                start = response_data.find(manager_pattern) + len(manager_pattern)
                end = response_data.find(",", start)
                manager = response_data[start:end].strip().strip('"')
                info["manager"] = manager

            return info

        except Exception as e:
            logger.error(f"解析基金信息失败: {e}")
            return None

    def _parse_fund_list(self, response_data: str) -> List[dict]:
        """解析基金列表"""
        try:
            if isinstance(response_data, str):
                data = json.loads(response_data)
            else:
                data = response_data

            if "data" not in data:
                return []

            fund_list = data["data"]
            return fund_list

        except Exception as e:
            logger.error(f"解析基金列表失败: {e}")
            return []

    # ============ 实现抽象方法 (基金不支持，返回空) ============

    def get_historical_data(self, code, start_date, end_date, adjustment=None):
        """获取历史数据 (基金不支持，返回空列表)"""
        logger.warning("基金数据源不支持 get_historical_data，请使用 get_fund_nav")
        return []

    def get_snapshot_data(self, code):
        """获取交易快照数据 (基金不支持，返回 None)"""
        logger.warning("基金数据源不支持 get_snapshot_data，请使用 get_fund_nav")
        return None

    def get_batch_snapshots(self, codes):
        """批量获取快照数据 (基金不支持，返回空字典)"""
        logger.warning("基金数据源不支持 get_batch_snapshots，请使用 get_fund_nav")
        return {}


# 为了兼容性，提供别名
FundSource = FundDataSource
