数据源
=======

finshare 支持多个数据源，自动故障切换，保证服务稳定性。

支持的 数据源
------------

.. list-table::
   :header-rows: 1

   * - 数据源
     - K线数据
     - 实时快照
     - 复权数据
     - 备注
   * - 东方财富
     - ✅
     - ✅
     - ✅
     - 主力数据源，数据最全
   * - 腾讯财经
     - ✅
     - ✅
     - ✅
     - 速度较快
   * - 新浪财经
     - ❌
     - ✅
     - ❌
     - 仅支持实时快照
   * - 通达信
     - ✅
     - ✅
     - ✅
     - 需要本地客户端
   * - BaoStock
     - ✅
     - ✅
     - ✅
     - 数据质量好

数据源优先级
-----------

finshare 默认按以下优先级尝试获取数据：

1. **东方财富** - 数据最全，支持K线和快照
2. **腾讯财经** - 速度快，支持K线和快照
3. **新浪财经** - 仅支持快照
4. **通达信** - 需要本地客户端
5. **BaoStock** - 数据质量好

当一个数据源请求失败时，会自动切换到下一个数据源。

使用特定数据源
------------

.. code-block:: python

    from finshare import EastMoneyDataSource, TencentDataSource, SinaDataSource

    # 使用东方财富
    eastmoney = EastMoneyDataSource()
    data = eastmoney.get_historical_data('000001', start='2024-01-01')
    snapshot = eastmoney.get_snapshot_data('000001.SZ')

    # 使用腾讯财经
    tencent = TencentDataSource()
    data = tencent.get_historical_data('000001', start='2024-01-01')
    snapshot = tencent.get_snapshot_data('000001.SZ')

    # 使用新浪财经（仅支持快照）
    sina = SinaDataSource()
    snapshot = sina.get_snapshot_data('000001.SZ')

多数据源管理器
------------

使用 DataSourceManager 统一管理多个数据源：

.. code-block:: python

    from finshare import get_data_manager

    # 获取数据源管理器
    manager = get_data_manager()

    # 获取历史K线（自动选择可用数据源）
    df = manager.get_historical_data('000001.SZ', start='2024-01-01')

    # 获取实时快照
    snapshot = manager.get_snapshot_data('000001.SZ')

    # 批量获取快照
    snapshots = manager.get_batch_snapshots(['000001.SZ', '600519.SH'])

数据源状态
--------

查看数据源状态和统计：

.. code-block:: python

    from finshare import get_data_manager

    manager = get_data_manager()

    # 获取数据源统计信息
    stats = manager.get_source_stats()
    for source, info in stats.items():
        print(f"{source}: 可用={info['available']}")

    # 重置数据源状态
    manager.reset_source_status()  # 重置所有
    manager.reset_source_status('eastmoney')  # 重置单个

数据源配置
---------

可以通过配置文件自定义数据源优先级和其他参数：

.. code-block:: python

    from finshare.config import config

    # 查看当前数据源优先级
    print(config.data_source.source_priority)

    # 修改优先级（需要修改源码配置文件）
    # finshare/config/settings.py
