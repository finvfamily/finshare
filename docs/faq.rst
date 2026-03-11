常见问题
========

基础问题
--------

Q: 需要 API Key 吗？
-------------------

A: 不需要，finshare 完全免费使用。

Q: 有调用次数限制吗？
-------------------

A: 没有硬性限制，但建议合理使用，设置适当的请求间隔。

Q: 数据从哪里获取？
-----------------

A: finshare 从多个公开数据源获取（东方财富、腾讯、新浪等），不存储数据。

Q: 支持哪些 Python 版本？
----------------------

A: 支持 Python 3.8 及以上版本。

市场数据
--------

Q: 如何获取港股数据？
------------------

A: 使用港股代码格式，如 ``00700.HK``、``09988.HK``。

.. code-block:: python

    import finshare as fs

    # 获取港股快照
    snapshot = fs.get_snapshot_data('00700.HK')
    print(f"腾讯控股: {snapshot.last_price} 港元")

    # 获取港股历史K线
    df = fs.get_historical_data('00700.HK', start='2024-01-01')

Q: 如何获取期货数据？
------------------

A: 使用期货代码，如 ``cu0``（沪铜连续）、``IF0``（沪深300股指）。

.. code-block:: python

    import finshare as fs

    # 获取期货K线
    data = fs.get_future_kline('cu0', '2024-01-01', '2024-12-31')

    # 获取期货实时快照
    snapshot = fs.get_future_snapshot('IF2409')
    print(f"最新价: {snapshot.last_price}, 持仓: {snapshot.open_interest}")

Q: 支持哪些期货交易所？
--------------------

A: 支持国内五大期货交易所：

- CFFEX（中金所）：IF、IH、IC（股指期货）
- SHFE（上期所）：CU、AL、AU、AG 等（金属期货）
- DCE（大商所）：M、Y、P 等（农产品）
- CZCE（郑商所）：SR、CF、TA 等（化工农产品）
- INE（上期能源）：SC（原油）

Q: 如何获取基金数据？
------------------

A: 使用基金相关接口。

.. code-block:: python

    import finshare as fs

    # 基金净值
    nav = fs.get_fund_nav('161039', '2024-01-01')

    # 基金列表
    funds = fs.get_fund_list()

    # ETF列表
    etfs = fs.get_etf_list()

Q: 如何获取财务数据？
------------------

A: 使用财务数据接口。

.. code-block:: python

    import finshare as fs

    # 利润表
    income = fs.get_income('600519.SH')

    # 资产负债表
    balance = fs.get_balance('600519.SH')

    # 财务指标
    indicator = fs.get_financial_indicator('600519.SH')

数据处理
--------

Q: 返回的数据格式是什么？
----------------------

A: finshare 返回统一格式的数据：

- K线数据：返回 :class:`pandas.DataFrame`
- 快照数据：返回 :class:`SnapshotData` 对象
- 基金净值：返回 ``List[FundData]``
- 财务数据：返回 :class:`pandas.DataFrame`

Q: 如何使用复权数据？
------------------

A: 使用 ``adjust`` 参数。

.. code-block:: python

    import finshare as fs

    # 前复权（推荐用于技术分析）
    df = fs.get_historical_data('600519.SH', start='2020-01-01', adjust='qfq')

    # 后复权（用于计算真实收益率）
    df = fs.get_historical_data('600519.SH', start='2020-01-01', adjust='hfq')

    # 不复权
    df = fs.get_historical_data('600519.SH', start='2020-01-01', adjust=None)

Q: 如何批量获取数据？
------------------

A: 使用批量接口或异步客户端。

.. code-block:: python

    import finshare as fs

    # 批量获取快照
    snapshots = fs.get_batch_snapshots(['000001.SZ', '600519.SH', '300750.SZ'])

    # 异步批量获取
    import asyncio
    async_manager = fs.get_async_manager()

    async def get_data():
        return await async_manager.get_batch_kline(
            ['000001.SZ', '600519.SH'],
            start='2024-01-01'
        )

    klines = asyncio.run(get_data())

高级特性
--------

Q: 如何使用缓存？
--------------

A: finshare 提供内置缓存功能。

.. code-block:: python

    from finshare.cache import cached, MemoryCache

    # 使用装饰器缓存
    @cached(ttl=60)  # 缓存60秒
    def get_data(code):
        return fs.get_snapshot_data(code)

    # 使用内存缓存类
    cache = MemoryCache(max_size=1000)
    cache.set('key', 'value', ttl=60)

Q: 如何配置数据源优先级？
----------------------

A: 修改配置文件 ``finshare/config/settings.py``。

.. code-block:: python

    from finshare.config import config

    # 查看当前优先级
    print(config.data_source.source_priority)

    # 默认优先级: ['eastmoney', 'tencent', 'sina', 'tdx', 'baostock']

Q: 如何监控数据源状态？
--------------------

A: 使用数据源管理器的统计功能。

.. code-block:: python

    from finshare import get_data_manager

    manager = get_data_manager()

    # 获取数据源统计
    stats = manager.get_source_stats()
    for source, info in stats.items():
        print(f"{source}: 可用={info['available']}")

    # 重置失败的数据源
    manager.reset_source_status()

Q: 熔断器是什么？如何使用？
------------------------

A: 熔断器用于保护系统，当数据源连续失败时自动熔断。

.. code-block:: python

    from finshare import get_circuit_breaker, CircuitBreakerConfig

    # 获取熔断器
    cb = get_circuit_breaker('eastmoney')

    # 查看状态
    print(f"状态: {cb.state}")
    print(f"失败次数: {cb.failure_count}")

错误处理
--------

Q: 请求失败了怎么办？
------------------

A: finshare 自动重试和切换数据源。

- 自动重试：最多重试 3 次
- 自动切换：主数据源失败时自动切换备用源
- 冷却机制：失败后进入冷却期

Q: 返回空数据怎么办？
------------------

A: 检查以下几点：

1. 代码格式是否正确（``000001.SZ`` 格式）
2. 日期范围是否有效
3. 数据源是否可用

.. code-block:: python

    import finshare as fs

    # 检查数据源状态
    manager = fs.get_data_manager()
    stats = manager.get_source_stats()
    print(stats)

Q: 如何报告问题？
--------------

A: 请在 GitHub Issues 页面报告问题：

https://github.com/finvfamily/finshare/issues
