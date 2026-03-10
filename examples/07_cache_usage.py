"""
示例 7: 缓存与稳定性

演示如何使用缓存装饰器和稳定性保障功能。
"""

import time
import finshare as fs


def main():
    """运行缓存与稳定性示例"""

    fs.logger.info("=" * 60)
    fs.logger.info("finshare 缓存与稳定性示例")
    fs.logger.info("=" * 60)

    # 1. 缓存示例
    fs.logger.info("\n=== 缓存示例 ===")

    # 创建缓存实例
    cache = fs.MemoryCache(max_size=100)

    # 基本缓存操作
    fs.logger.info("\n1. 基本缓存操作:")
    cache.set("key1", "value1", ttl=60)
    fs.logger.info(f"  设置缓存: key1 = value1 (TTL=60s)")

    value = cache.get("key1")
    fs.logger.info(f"  获取缓存: key1 = {value}")

    fs.logger.info(f"  缓存存在: {cache.exists('key1')}")
    fs.logger.info(f"  缓存大小: {cache.size()}")

    # 使用缓存装饰器
    fs.logger.info("\n2. 使用缓存装饰器:")

    call_count = 0

    @fs.cached(ttl=60, key_prefix="stock_")
    def get_stock_price(code):
        """模拟获取股票价格"""
        nonlocal call_count
        call_count += 1
        # 模拟API调用
        return {"code": code, "price": 10.5 + call_count}

    # 第一次调用
    result1 = get_stock_price("000001.SZ")
    fs.logger.info(f"  第一次调用: {result1}, call_count={call_count}")

    # 第二次调用（命中缓存）
    result2 = get_stock_price("000001.SZ")
    fs.logger.info(f"  第二次调用（缓存）: {result2}, call_count={call_count}")

    # 清除缓存后再次调用
    get_stock_price.clear_cache()
    result3 = get_stock_price("000001.SZ")
    fs.logger.info(f"  清除缓存后调用: {result3}, call_count={call_count}")

    # TTL配置
    fs.logger.info("\n3. TTL配置:")
    ttl_config = fs.get_ttl_config()
    fs.logger.info(f"  实时行情 TTL: {ttl_config.snapshot_ttl}s")
    fs.logger.info(f"  日线数据 TTL: {ttl_config.daily_ttl}s")
    fs.logger.info(f"  财务数据 TTL: {ttl_config.financial_ttl}s")

    # 2. 稳定性保障示例
    fs.logger.info("\n=== 稳定性保障示例 ===")

    # 熔断器
    fs.logger.info("\n1. 熔断器:")
    config = fs.CircuitBreakerConfig(failure_threshold=3, timeout=5)
    breaker = fs.CircuitBreaker("test_api", config)

    fs.logger.info(f"  初始状态: {breaker.state.value}")

    # 模拟失败
    breaker.record_failure()
    breaker.record_failure()
    fs.logger.info(f"  2次失败后: {breaker.state.value}")

    breaker.record_failure()  # 触发熔断
    fs.logger.info(f"  3次失败后: {breaker.state.value}")
    fs.logger.info(f"  是否可用: {breaker.is_available()}")

    # 智能路由
    fs.logger.info("\n2. 智能路由:")
    router = fs.SmartRouter()

    snapshot_source = router.get_preferred_source(fs.DataType.SNAPSHOT)
    daily_source = router.get_preferred_source(fs.DataType.DAILY)

    fs.logger.info(f"  实时快照首选: {snapshot_source.value if snapshot_source else 'None'}")
    fs.logger.info(f"  日线数据首选: {daily_source.value if daily_source else 'None'}")

    # 记录请求统计
    router.record_request(fs.SourceType.EASTMONEY, fs.DataType.SNAPSHOT, True, 0.5)
    router.record_request(fs.SourceType.TENCENT, fs.DataType.SNAPSHOT, False, 1.0)

    stats = router.get_source_stats()
    fs.logger.info(f"  请求统计: {stats}")

    # 监控
    fs.logger.info("\n3. 监控系统:")
    monitor = fs.Monitor()

    # 记录请求
    monitor.record_request("eastmoney", True, 0.5)
    monitor.record_request("eastmoney", True, 0.3)
    monitor.record_request("tencent", False, 1.0, "timeout")

    stats = monitor.get_stats()
    fs.logger.info(f"  请求统计: {stats}")

    health = monitor.get_health_status()
    fs.logger.info(f"  健康状态: {health}")

    # 4. 提示
    fs.logger.info("\n" + "=" * 60)
    fs.logger.info("💡 提示:")
    fs.logger.info("  - 缓存减少重复API调用，提升性能")
    fs.logger.info("  - 熔断器防止故障级联传播")
    fs.logger.info("  - 智能路由自动选择最佳数据源")
    fs.logger.info("  - 监控系统实时掌握数据源状态")


if __name__ == "__main__":
    main()
