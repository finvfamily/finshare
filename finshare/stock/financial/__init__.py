"""
Financial Module - 财务数据模块

提供:
- get_income: 利润表
- get_balance: 资产负债表
- get_cashflow: 现金流量表
- get_financial_indicator: 财务指标
- get_dividend: 分红送股
"""

from finshare.stock.financial.client import FinancialClient
from finshare.stock.financial.income import get_income
from finshare.stock.financial.balance import get_balance
from finshare.stock.financial.cashflow import get_cashflow
from finshare.stock.financial.indicator import get_financial_indicator
from finshare.stock.financial.dividend import get_dividend

# 全局财务客户端
_financial_client = None


def get_financial_client() -> FinancialClient:
    """获取财务数据客户端（单例）"""
    global _financial_client
    if _financial_client is None:
        _financial_client = FinancialClient()
    return _financial_client


__all__ = [
    "FinancialClient",
    "get_financial_client",
    "get_income",
    "get_balance",
    "get_cashflow",
    "get_financial_indicator",
    "get_dividend",
]
