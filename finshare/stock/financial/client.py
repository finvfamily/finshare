"""
Financial Client - 东方财富财务数据客户端

提供财务报表和财务指标数据的获取。
注意: 完整财务报表API暂不可用，使用实时行情数据提供基本财务指标。
"""

import time
import random
import requests
import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime, date

from finshare.logger import logger
from finshare.sources.normalizer import get_normalizer


class FinancialClient:
    """东方财富财务数据客户端"""

    # 实时行情API (提供基本财务指标作为备用)
    QUOTE_URL = "https://push2.eastmoney.com/api/qt/stock/get"

    # 东方财富财务数据中心API (主要数据源)
    # 参考akshare实现: https://datacenter.eastmoney.com/securities/api/data/get
    FINANCE_MAIN_DATA_URL = "https://datacenter.eastmoney.com/securities/api/data/get"

    # 财务数据接口 (暂不可用，保留接口)
    INCOME_URL = "https://emweb.securities.eastmoney.com/PC_F10HS/FinancialAnalysisAjax"
    BALANCE_URL = "https://emweb.securities.eastmoney.com/PC_HSF10/FinancialAnalysisAjax"
    CASHFLOW_URL = "https://emweb.securities.eastmoney.com/PC_HSF10/FinancialAnalysisAjax"

    # 新版财务接口 (暂不可用)
    NEW_INCOME_URL = "https://emweb.securities.eastmoney.com/NewFinanceAnalysis/ggmx"
    NEW_INDICATOR_URL = "https://emweb.securities.eastmoney.com/NewFinanceAnalysis/zbxs"
    DIVIDEND_URL = "https://emweb.securities.eastmoney.com/PC_HSF10/FinanceShareholderAjax"

    # 实时行情字段映射
    QUOTE_FIELDS = "f57,f58,f84,f85,f86,f92,f103,f104,f105,f107,f108,f109,f116,f117,f125,f140,f141,f144,f145,f146,f147,f148,f149"

    # 新浪财经财务报表API
    SINA_FINANCE_URL = "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022"

    # 新浪财务数据类型映射
    SINA_SOURCE_MAP = {
        "balance": "fzb",  # 资产负债表
        "income": "lrb",   # 利润表
        "cashflow": "llb", # 现金流量表
    }

    # User-Agent 池
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        self.source_name = "eastmoney_financial"
        self.normalizer = get_normalizer()
        self.session = requests.Session()
        self.request_interval = 0.5  # 请求间隔

    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.USER_AGENTS)

    def _rate_limit(self):
        """简单的频率限制"""
        time.sleep(self.request_interval)

    def _make_request(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict]:
        """发送HTTP请求"""
        # 频率限制
        self._rate_limit()

        # 请求头
        request_headers = {
            "User-Agent": self.get_random_user_agent(),
            "Referer": "https://emweb.securities.eastmoney.com/",
        }
        if headers:
            request_headers.update(headers)

        try:
            response = requests.get(url, params=params, headers=request_headers, timeout=30)

            if response.status_code >= 400:
                logger.warning(f"财务API请求失败: HTTP {response.status_code}")
                return None

            return response.json()

        except Exception as e:
            logger.warning(f"财务API请求异常: {e}")
            return None

    def _ensure_full_code(self, code: str) -> str:
        """
        确保返回完整代码格式

        支持输入格式:
        - 000001.SZ, 600001.SH
        - SZ000001, SH600519
        - 000001, 600001 (纯数字)

        返回格式: 000001.SZ, 600001.SH
        """
        if not code:
            return code

        code = code.strip().upper()

        # 已经是标准格式
        if "." in code:
            return code

        # 处理纯数字代码
        if code.isdigit():
            first = code[0]
            if first in ["6", "5"]:
                return f"{code}.SH"
            elif first in ["0", "1", "2", "3"]:
                return f"{code}.SZ"

        # 处理 SZ/SH 前缀
        prefix_map = {"SZ": "SZ", "SH": "SH", "BJ": "BJ"}
        for prefix, market in prefix_map.items():
            if code.startswith(prefix):
                num_code = code[len(prefix):]
                return f"{num_code}.{market}"

        return code

    def _convert_to_secid(self, fs_code: str) -> str:
        """转换代码为secid格式 (0.000001 或 1.600519)"""
        if "." in fs_code:
            parts = fs_code.split(".")
            code = parts[0]
            market = parts[1]
        else:
            code = fs_code
            market = "SH" if fs_code.startswith("6") else "SZ"

        if market == "SH":
            return f"1.{code}"
        elif market == "SZ":
            return f"0.{code}"
        return f"0.{code}"

    def get_income(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取利润表数据

        使用新浪财经API获取利润表数据。

        Args:
            code: 股票代码 (000001.SZ)
            start_date: 开始日期 (YYYYMMDD) - 暂不支持
            end_date: 结束日期 (YYYYMMDD) - 暂不支持

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - ann_date: 公告日期
            - report_date: 报告期
            - revenue: 营业收入(元)
            - revenue_yoy: 营业收入同比(%)
            - net_profit: 净利润(元)
            - net_profit_yoy: 净利润同比(%)
            - gross_margin: 毛利率(%)
            - roe: 净资产收益率(%)
        """
        fs_code = self._ensure_full_code(code)
        logger.debug(f"获取利润表: {fs_code}")

        # 转换为新浪格式
        if fs_code.startswith("6"):
            sina_code = f"sh{fs_code.split('.')[0]}"
        else:
            sina_code = f"sz{fs_code.split('.')[0]}"

        params = {
            "paperCode": sina_code,
            "source": self.SINA_SOURCE_MAP["income"],
            "type": "0",
            "page": "1",
            "num": "100",
        }

        data = self._make_request(self.SINA_FINANCE_URL, params)

        if not data:
            logger.warning(f"获取利润表失败，返回空数据: {fs_code}")
            return pd.DataFrame(columns=[
                "fs_code", "ann_date", "report_date", "revenue", "revenue_yoy",
                "net_profit", "net_profit_yoy", "gross_margin", "roe"
            ])

        try:
            result = data.get("result", {})
            data_info = result.get("data", {})
            report_list = data_info.get("report_list", {})

            if not report_list:
                return pd.DataFrame(columns=[
                    "fs_code", "ann_date", "report_date", "revenue", "revenue_yoy",
                    "net_profit", "net_profit_yoy", "gross_margin", "roe"
                ])

            records = []
            for report_date, report_data in report_list.items():
                items = report_data.get("data", [])
                item_dict = {item["item_title"]: item["item_value"] for item in items}

                # 提取关键指标
                revenue = item_dict.get("营业收入", 0)
                net_profit = item_dict.get("净利润", 0)

                # 尝试获取同比数据
                revenue_yoy = 0
                net_profit_yoy = 0
                for item in items:
                    title = item.get("item_title", "")
                    if "营业收入" in title and "同比" in title:
                        revenue_yoy = item.get("item_value", 0)
                    if "净利润" in title and "同比" in title:
                        net_profit_yoy = item.get("item_value", 0)

                record = {
                    "fs_code": fs_code,
                    "ann_date": report_data.get("publish_date", "").replace("-", ""),
                    "report_date": report_date,
                    "revenue": revenue,
                    "revenue_yoy": revenue_yoy,
                    "net_profit": net_profit,
                    "net_profit_yoy": net_profit_yoy,
                    "gross_margin": 0,
                    "roe": 0,
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取利润表成功: {fs_code}, {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析利润表失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "ann_date", "report_date", "revenue", "revenue_yoy",
                "net_profit", "net_profit_yoy", "gross_margin", "roe"
            ])

    def get_balance(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取资产负债表数据

        使用新浪财经API获取资产负债表数据。

        Args:
            code: 股票代码 (000001.SZ)
            start_date: 开始日期 (YYYYMMDD) - 暂不支持
            end_date: 结束日期 (YYYYMMDD) - 暂不支持

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - ann_date: 公告日期
            - report_date: 报告期
            - total_assets: 总资产(元)
            - total_liab: 总负债(元)
            - total_equity: 股东权益(元)
            - current_assets: 流动资产(元)
            - current_liab: 流动负债(元)
        """
        fs_code = self._ensure_full_code(code)
        logger.debug(f"获取资产负债表: {fs_code}")

        # 转换为新浪格式
        if fs_code.startswith("6"):
            sina_code = f"sh{fs_code.split('.')[0]}"
        else:
            sina_code = f"sz{fs_code.split('.')[0]}"

        params = {
            "paperCode": sina_code,
            "source": self.SINA_SOURCE_MAP["balance"],
            "type": "0",
            "page": "1",
            "num": "100",
        }

        data = self._make_request(self.SINA_FINANCE_URL, params)

        if not data:
            logger.warning(f"获取资产负债表失败，返回空数据: {fs_code}")
            return pd.DataFrame(columns=[
                "fs_code", "ann_date", "report_date", "total_assets", "total_liab",
                "total_equity", "current_assets", "current_liab"
            ])

        try:
            result = data.get("result", {})
            data_info = result.get("data", {})
            report_list = data_info.get("report_list", {})

            if not report_list:
                return pd.DataFrame(columns=[
                    "fs_code", "ann_date", "report_date", "total_assets", "total_liab",
                    "total_equity", "current_assets", "current_liab"
                ])

            records = []
            for report_date, report_data in report_list.items():
                items = report_data.get("data", [])
                item_dict = {item["item_title"]: item["item_value"] for item in items}

                # 提取关键指标
                record = {
                    "fs_code": fs_code,
                    "ann_date": report_data.get("publish_date", "").replace("-", ""),
                    "report_date": report_date,
                    "total_assets": item_dict.get("资产总计", 0),
                    "total_liab": item_dict.get("负债合计", 0),
                    "total_equity": item_dict.get("股东权益合计", 0),
                    "current_assets": item_dict.get("流动资产合计", 0),
                    "current_liab": item_dict.get("流动负债合计", 0),
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取资产负债表成功: {fs_code}, {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析资产负债表失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "ann_date", "report_date", "total_assets", "total_liab",
                "total_equity", "current_assets", "current_liab"
            ])

    def get_cashflow(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取现金流量表数据

        使用新浪财经API获取现金流量表数据。

        Args:
            code: 股票代码 (000001.SZ)
            start_date: 开始日期 (YYYYMMDD) - 暂不支持
            end_date: 结束日期 (YYYYMMDD) - 暂不支持

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - ann_date: 公告日期
            - report_date: 报告期
            - operate_cashflow: 经营活动现金流(元)
            - invest_cashflow: 投资活动现金流(元)
            - finance_cashflow: 筹资活动现金流(元)
        """
        fs_code = self._ensure_full_code(code)
        logger.debug(f"获取现金流量表: {fs_code}")

        # 转换为新浪格式
        if fs_code.startswith("6"):
            sina_code = f"sh{fs_code.split('.')[0]}"
        else:
            sina_code = f"sz{fs_code.split('.')[0]}"

        params = {
            "paperCode": sina_code,
            "source": self.SINA_SOURCE_MAP["cashflow"],
            "type": "0",
            "page": "1",
            "num": "100",
        }

        data = self._make_request(self.SINA_FINANCE_URL, params)

        if not data:
            logger.warning(f"获取现金流量表失败，返回空数据: {fs_code}")
            return pd.DataFrame(columns=[
                "fs_code", "ann_date", "report_date", "operate_cashflow",
                "invest_cashflow", "finance_cashflow"
            ])

        try:
            result = data.get("result", {})
            data_info = result.get("data", {})
            report_list = data_info.get("report_list", {})

            if not report_list:
                return pd.DataFrame(columns=[
                    "fs_code", "ann_date", "report_date", "operate_cashflow",
                    "invest_cashflow", "finance_cashflow"
                ])

            records = []
            for report_date, report_data in report_list.items():
                items = report_data.get("data", [])
                item_dict = {item["item_title"]: item["item_value"] for item in items}

                # 提取关键指标
                record = {
                    "fs_code": fs_code,
                    "ann_date": report_data.get("publish_date", "").replace("-", ""),
                    "report_date": report_date,
                    "operate_cashflow": item_dict.get("经营活动产生的现金流量净额", 0),
                    "invest_cashflow": item_dict.get("投资活动产生的现金流量净额", 0),
                    "finance_cashflow": item_dict.get("筹资活动产生的现金流量净额", 0),
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取现金流量表成功: {fs_code}, {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析现金流量表失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "ann_date", "report_date", "operate_cashflow",
                "invest_cashflow", "finance_cashflow"
            ])

    def get_financial_indicator(
        self,
        code: str,
        ann_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取财务指标数据

        使用东方财富财务数据分析API获取主要财务指标。

        Args:
            code: 股票代码 (000001.SZ)
            ann_date: 公告日期 (暂不支持过滤)

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - ann_date: 公告日期
            - report_date: 报告期
            - eps: 每股收益(元)
            - roe: 净资产收益率(%)
            - gross_margin: 毛利率(%)
            - netprofit_margin: 净利率(%)
            - current_ratio: 流动比率
            - quick_ratio: 速动比率
            - debt_to_assets: 资产负债率(%)
        """
        fs_code = self._ensure_full_code(code)

        logger.debug(f"获取财务指标: {fs_code}")

        # 使用东方财富财务数据分析API
        params = {
            "type": "RPT_F10_FINANCE_MAINFINADATA",
            "sty": "APP_F10_MAINFINADATA",
            "quoteColumns": "",
            "filter": f'(SECUCODE="{fs_code}")',
            "p": "1",
            "ps": "200",
            "sr": "-1",
            "st": "REPORT_DATE",
            "source": "HSF10",
            "client": "PC",
        }

        data = self._make_request(self.FINANCE_MAIN_DATA_URL, params)

        if not data:
            logger.warning(f"获取财务指标失败，返回空数据: {fs_code}")
            return pd.DataFrame(columns=[
                "fs_code", "ann_date", "report_date", "eps", "roe",
                "gross_margin", "netprofit_margin", "current_ratio", "quick_ratio",
                "debt_to_assets"
            ])

        try:
            result = data.get("result", {})
            data_list = result.get("data", [])

            if not data_list:
                return pd.DataFrame(columns=[
                    "fs_code", "ann_date", "report_date", "eps", "roe",
                    "gross_margin", "netprofit_margin", "current_ratio", "quick_ratio",
                    "debt_to_assets"
                ])

            records = []
            for item in data_list:
                record = {
                    "fs_code": fs_code,
                    "ann_date": item.get("NOTICE_DATE", "")[:8].replace("-", "") if item.get("NOTICE_DATE") else "",
                    "report_date": item.get("REPORT_DATE", "")[:10].replace("-", "") if item.get("REPORT_DATE") else "",
                    # 盈利能力
                    "eps": item.get("EPSJB", 0),  # 每股收益(基本)
                    "roe": item.get("ROEJQ", 0),  # 净资产收益率(加权)
                    "gross_margin": item.get("XSJLL", 0),  # 销售净利率(毛利率近似)
                    "netprofit_margin": item.get("ZZCJLL", 0),  # 主营业务利润率
                    # 偿债能力
                    "current_ratio": 0,  # 流动比率 - 数据中无直接字段
                    "quick_ratio": 0,  # 速动比率 - 数据中无直接字段
                    "debt_to_assets": item.get("ZCFZL", 0),  # 资产负债率
                }
                records.append(record)

            df = pd.DataFrame(records)
            logger.info(f"获取财务指标成功: {fs_code}, {len(records)}条")
            return df

        except Exception as e:
            logger.error(f"解析财务指标失败: {e}")
            return pd.DataFrame(columns=[
                "fs_code", "ann_date", "report_date", "eps", "roe",
                "gross_margin", "netprofit_margin", "current_ratio", "quick_ratio",
                "debt_to_assets"
            ])

    def get_dividend(self, code: str) -> pd.DataFrame:
        """
        获取分红送股数据

        注意: 东方财富分红送股API暂不可用，返回空DataFrame。

        Args:
            code: 股票代码 (000001.SZ)

        Returns:
            DataFrame 包含以下字段:
            - fs_code: 股票代码
            - ann_date: 公告日期
            - divident_date: 分红日期
            - cash_div: 现金分红(元/股)
            - stock_div: 送股(股/10股)
            - stock_ratio: 送股比例
            - bonus_ratio: 分红比例
        """
        fs_code = self._ensure_full_code(code)
        logger.warning(f"分红送股 API 暂不可用，返回空数据: {fs_code}")
        return pd.DataFrame(columns=[
            "fs_code", "ann_date", "divident_date", "cash_div",
            "stock_div", "stock_ratio", "bonus_ratio"
        ])
