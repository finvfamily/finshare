"""
finshare Config Module

配置管理模块
"""

import os


class SmartCooldownConfig:
    """智能冷却配置"""

    def __init__(self):
        # 冷却策略（秒）
        self.cooldown_timeout = 30              # 超时错误
        self.cooldown_connection_error = 60     # 连接错误
        self.cooldown_rate_limit = 300        # 429限流 (5分钟)
        self.cooldown_forbidden = 600         # 403禁止 (10分钟)
        self.cooldown_service_unavailable = 300  # 503服务不可用 (5分钟)
        self.cooldown_default = 300            # 默认冷却 (5分钟)

        # 连续失败累积
        self.max_failure_multiplier = 5.0       # 最大累积倍率


class RetryConfig:
    """重试配置"""

    def __init__(self):
        self.max_retries = 3                   # 最大重试次数
        self.retry_base_delay = 10.0           # 基础延迟（秒）
        self.retry_max_delay = 60.0            # 最大延迟（秒）
        self.retry_backoff_factor = 2.0        # 指数退避因子


class HealthProbeConfig:
    """健康探测配置"""

    def __init__(self):
        self.probe_interval = 300            # 探测间隔（秒），默认5分钟
        self.probe_timeout = 10               # 探测超时（秒）
        self.success_threshold = 1             # 连续成功次数阈值


class LoggingConfig:
    """日志配置"""

    def __init__(self):
        self.log_dir = os.path.join(os.path.expanduser("~"), ".finshare", "logs")
        self.log_level = "INFO"
        self.log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        self.rotation = "10 MB"
        self.retention = "30 days"
        self.enable_remote_logging = False
        self.remote_log_url = None


class DataSourceConfig:
    """数据源配置"""

    def __init__(self):
        self.source_priority = ["eastmoney", "tencent", "sina", "tdx", "baostock"]
        self.timeout = 30
        self.request_timeout = 30  # 请求超时时间（秒）
        self.retry_times = 3
        self.request_interval = 0.1  # 请求间隔（秒）
        self.max_workers = 5  # 最大并发数
        # 旧版配置，保留兼容（已废弃，使用 SmartCooldownConfig）
        self.failure_cooldown_hours = 24  # 数据源失败后的冷却时间（小时）


class Config:
    """全局配置"""

    def __init__(self):
        self.timeout = 30
        self.logging = LoggingConfig()
        self.data_source = DataSourceConfig()
        self.smart_cooldown = SmartCooldownConfig()
        self.retry = RetryConfig()
        self.health_probe = HealthProbeConfig()

    def get(self, key, default=None):
        """获取配置项"""
        return getattr(self, key, default)


# 全局配置实例
config = Config()

__all__ = [
    "Config",
    "config",
    "SmartCooldownConfig",
    "RetryConfig",
    "HealthProbeConfig",
]
