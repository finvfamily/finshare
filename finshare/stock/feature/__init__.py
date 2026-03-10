"""
特色数据模块

提供资金流向、龙虎榜、融资融券等中国特色数据。
"""

from finshare.stock.feature.moneyflow import get_money_flow, get_money_flow_industry
from finshare.stock.feature.lhb import get_lhb, get_lhb_detail
from finshare.stock.feature.margin import get_margin, get_margin_detail

__all__ = [
    "get_money_flow",
    "get_money_flow_industry",
    "get_lhb",
    "get_lhb_detail",
    "get_margin",
    "get_margin_detail",
]
