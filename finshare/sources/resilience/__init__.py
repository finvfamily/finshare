"""
Resilience Module - 数据源弹性模块

提供:
- smart_cooldown: 智能冷却分级机制
- retry_handler: 请求重试+指数退避
- health_probe: 自动健康探测
- circuit_breaker: 熔断器模式
- smart_router: 智能路由
- monitor: 监控统计
"""

# 智能冷却
from finshare.sources.resilience.smart_cooldown import SmartCooldown, cooldown_manager

# 重试处理
from finshare.sources.resilience.retry_handler import RetryHandler, retry_handler

# 健康探测
from finshare.sources.resilience.health_probe import HealthProbe, health_probe

# 熔断器
from finshare.sources.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    circuit_breaker,
    CircuitBreakerOpenError,
    get_circuit_breaker,
    get_all_circuit_breakers,
    reset_circuit_breaker,
)

# 智能路由
from finshare.sources.resilience.smart_router import (
    DataType,
    SourceType,
    SourcePreference,
    SmartRouter,
    DEFAULT_PREFERENCES,
    get_router,
    set_router,
)

# 监控
from finshare.sources.resilience.monitor import (
    Monitor,
    RequestStats,
    TimeWindowStats,
    get_monitor,
    set_monitor,
)

__all__ = [
    # Smart Cooldown
    "SmartCooldown",
    "cooldown_manager",
    # Retry Handler
    "RetryHandler",
    "retry_handler",
    # Health Probe
    "HealthProbe",
    "health_probe",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "circuit_breaker",
    "CircuitBreakerOpenError",
    "get_circuit_breaker",
    "get_all_circuit_breakers",
    "reset_circuit_breaker",
    # Smart Router
    "DataType",
    "SourceType",
    "SourcePreference",
    "SmartRouter",
    "DEFAULT_PREFERENCES",
    "get_router",
    "set_router",
    # Monitor
    "Monitor",
    "RequestStats",
    "TimeWindowStats",
    "get_monitor",
    "set_monitor",
]
