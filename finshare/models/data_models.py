from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class AdjustmentType(str, Enum):
    """复权类型"""
    NONE = "none"
    PREVIOUS = "pre"
    POST = "post"


class MarketType(str, Enum):
    """市场类型"""
    SH = "sh"
    SZ = "sz"
    BJ = "bj"
    HK = "hk"
    US = "us"


class FrequencyType(str, Enum):
    """K线频率"""
    MIN_1 = "1"
    MIN_5 = "5"
    MIN_15 = "15"
    MIN_30 = "30"
    MIN_60 = "60"
    DAILY = "d"
    WEEKLY = "w"
    MONTHLY = "m"


# ============ 分钟线数据模型 ============

class MinuteData(BaseModel):
    """
    分钟线数据

    字段说明:
    - fs_code: 股票代码 (000001.SZ)
    - trade_time: 交易时间 (YYYYMMDDHHMMSS)
    - open/high/low/close: 价格 (元)
    - volume: 成交量 (股)
    - amount: 成交金额 (元)
    """

    fs_code: str = Field(..., description="股票代码: 000001.SZ")
    trade_time: str = Field(..., description="交易时间: YYYYMMDDHHMMSS")

    # 行情数据
    open: float = Field(..., description="开盘价(元)")
    close: float = Field(..., description="收盘价(元)")
    high: float = Field(..., description="最高价(元)")
    low: float = Field(..., description="最低价(元)")

    # 量价数据
    volume: int = Field(..., description="成交量(股)")
    amount: float = Field(0.0, description="成交金额(元)")

    # 元数据
    frequency: str = Field("5", description="频率: 1/5/15/30/60")
    data_source: str = Field(default="unknown", description="数据源")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()},
        extra="ignore",
    )


class HistoricalData(BaseModel):
    """
    历史数据模型 - 安全配置版
    关键修改：
    1. 移除了所有`alias`，避免潜在的解析循环。
    2. 将易冲突的字段名（open, close, date）改为更安全的名称。
    3. 使用最简配置。
    """

    # 核心行情字段
    code: str
    trade_date: date = Field(..., description="交易日期")
    open_price: float = Field(..., description="开盘价")
    high_price: float = Field(..., description="最高价")
    low_price: float = Field(..., description="最低价")
    close_price: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")

    # 可选字段
    amount: Optional[float] = Field(None, description="成交额")
    adjust_factor: Optional[float] = Field(
        default=1.0, description="复权因子", alias="adjustment_factor"  # 添加别名
    )
    turnover_rate: Optional[float] = Field(None, description="换手率")

    # 元数据字段
    market: MarketType = Field(default=MarketType.SH, description="市场类型")
    adjustment: AdjustmentType = Field(default=AdjustmentType.NONE, description="复权类型")
    data_source: str = Field(default="unknown", description="数据来源")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    # Pydantic V2 配置 - 启用别名支持
    model_config = ConfigDict(
        # 启用别名支持
        populate_by_name=True,
        # 确保json序列化
        json_encoders={datetime: lambda v: v.isoformat(), date: lambda v: v.isoformat()},
        # 可以改为'ignore'以避免类似问题，或者保持'forbid'但确保字段对齐
        extra="ignore",
    )

    @field_validator("trade_date")
    def validate_trade_date(cls, v: date) -> date:
        """验证日期不超过今天"""
        if v > date.today():
            raise ValueError("交易日期不能晚于今天")
        return v


class SnapshotData(BaseModel):
    """
    交易快照数据模型 - 安全配置版
    """

    # 核心快照字段
    code: str
    timestamp: datetime
    last_price: float = Field(..., description="最新价")  # 改名：price -> last_price
    volume: float
    amount: float

    # 盘口字段 (可选)
    bid1_price: Optional[float] = Field(None, description="买一价")  # 改名：bid_price
    ask1_price: Optional[float] = Field(None, description="卖一价")  # 改名：ask_price
    bid1_volume: Optional[float] = Field(None, description="买一量")
    ask1_volume: Optional[float] = Field(None, description="卖一量")

    # 日内指标 (可选)
    day_high: Optional[float] = Field(None, description="当日最高")  # 改名：high
    day_low: Optional[float] = Field(None, description="当日最低")  # 改名：low
    day_open: Optional[float] = Field(None, description="开盘价")  # 改名：open

    # 市场状态
    is_trading: bool = Field(default=True, description="是否在交易中")
    prev_close: Optional[float] = Field(None, description="前收盘价")  # 改名：pre_close

    # 元数据
    market: MarketType = Field(default=MarketType.SH, description="市场类型")
    data_source: str = Field(default="unknown", description="数据来源")

    # Pydantic V2 配置
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()}, extra="forbid")

    @field_validator("timestamp")
    def validate_timestamp(cls, v: datetime) -> datetime:
        """验证时间戳不超过当前时间"""
        if v > datetime.now():
            raise ValueError("时间戳不能晚于当前时间")
        return v


class DataSourceStatus(BaseModel):
    source_name: str
    last_success_time: Optional[datetime]
    last_error_time: Optional[datetime]
    error_count: int = 0
    is_active: bool = True
    cool_down_until: Optional[datetime] = None

    @property
    def is_in_cool_down(self) -> bool:
        if not self.cool_down_until:
            return False
        return datetime.now() < self.cool_down_until
