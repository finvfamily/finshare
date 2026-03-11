快速开始
==========

基础用法
--------

.. code-block:: python

    import finshare as fs

    # 获取历史K线数据
    df = fs.get_historical_data('000001.SZ', start='2024-01-01', end='2024-01-31')
    print(df.head())

    # 获取实时快照
    snapshot = fs.get_snapshot_data('000001.SZ')
    print(f"最新价: {snapshot.last_price}")

    # 批量获取快照
    snapshots = fs.get_batch_snapshots(['000001.SZ', '600519.SH'])
    for code, snap in snapshots.items():
        print(f"{code}: {snap.last_price}")

股票代码格式
------------

finshare 支持多种股票代码格式：

.. code-block:: python

    # 以下格式均可使用
    '000001.SZ'   # 标准格式
    '000001'      # 纯数字（自动识别市场）
    'SZ000001'    # SZ前缀

支持的交易市场：

.. list-table::
   :header-rows: 1

   * - 市场
     - 代码后缀
     - 示例
   * - 深圳
     - .SZ
     - 000001.SZ
   * - 上海
     - .SH
     - 600519.SH
   * - 北京
     - .BJ
     - 430001.BJ
   * - 港股
     - .HK
     - 00700.HK
   * - 美股
     - .US
     - AAPL.US

港股数据
--------

finshare 支持获取港股实时行情和历史数据。

.. code-block:: python

    import finshare as fs

    # 港股实时快照（腾讯/新浪数据源）
    snapshot = fs.get_snapshot_data('00700.HK')  # 腾讯控股
    print(f"最新价: {snapshot.last_price}")
    print(f"涨跌额: {snapshot.change}")
    print(f"涨跌幅: {snapshot.change_pct}%")

    # 港股历史K线（东方财富数据源）
    df = fs.get_historical_data('00700.HK', start='2024-01-01', end='2024-12-31')
    print(df.head())

    # 批量获取港股行情
    hk_stocks = ['00700.HK', '09988.HK', '9988.HK']
    snapshots = fs.get_batch_snapshots(hk_stocks)

期货数据
--------

finshare 支持获取国内期货市场的行情数据。

**支持的交易所**：

- CFFEX（中金所）：股指期货 IF、IH、IC
- SHFE（上期所）：铜 CU、铝 AL、锌 ZN、金 AU、银 AG、原油 SC 等
- DCE（大商所）：豆粕 M、豆油 Y、棕榈油 P、铁矿石 I、螺纹钢 RB 等
- CZCE（郑商所）：白糖 SR、棉花 CF、PTA TA、甲醇 MA 等
- INE（上期能源）：原油 SC

**合约代码格式**：

- ``IF2409``：2024年9月合约
- ``IF0``：沪深300当月连续（自动匹配主力合约）
- ``CU0``：沪铜当月连续

.. code-block:: python

    import finshare as fs

    # 期货历史K线
    df = fs.get_future_kline('IF2409', '2024-01-01', '2024-12-31')
    print(df.head())

    # 期货实时快照
    snapshot = fs.get_future_snapshot('AU2409')  # 沪金2409
    print(f"最新价: {snapshot.last_price}")
    print(f"持仓量: {snapshot.open_interest}")
    print(f"成交量: {snapshot.volume}")

    # 批量获取期货行情
    futures = ['IF2409', 'CU2409', 'AU2409', 'SC2409']
    snapshots = fs.get_batch_future_snapshots(futures)
    for code, snap in snapshots.items():
        print(f"{code}: {snap.last_price}")

基金数据
--------

.. code-block:: python

    import finshare as fs

    # 基金净值数据
    nav_data = fs.get_fund_nav('161039', '2024-01-01', '2024-12-31')
    for item in nav_data:
        print(f"{item.nav_date}: nav={item.nav}, nav_acc={item.nav_acc}")

    # 基金基本信息
    info = fs.get_fund_info('161039')
    print(f"基金名称: {info.get('name')}")

    # 基金列表
    funds = fs.get_fund_list()
    print(f"共有 {len(funds)} 只基金")

    # ETF列表
    etfs = fs.get_etf_list()
    print(f"共有 {len(etfs)} 只ETF")

财务数据
--------

.. code-block:: python

    import finshare as fs

    # 利润表
    income = fs.get_income('600519.SH')
    print(income.head())

    # 资产负债表
    balance = fs.get_balance('600519.SH')
    print(balance.head())

    # 现金流量表
    cashflow = fs.get_cashflow('600519.SH')
    print(cashflow.head())

    # 财务指标
    indicator = fs.get_financial_indicator('600519.SH')
    print(indicator.head())

特色数据
--------

.. code-block:: python

    import finshare as fs

    # 个股资金流向
    money_flow = fs.get_money_flow('600519.SH')
    print(money_flow)

    # 行业资金流向
    industry_flow = fs.get_money_flow_industry()
    print(industry_flow.head())

    # 龙虎榜（最近30天）
    lhb = fs.get_lhb()
    print(lhb.head())

    # 龙虎榜明细
    lhb_detail = fs.get_lhb_detail('600519.SH')
    print(lhb_detail)

    # 融资融券（市场汇总）
    margin = fs.get_margin()
    print(margin.head())

    # 个股融资融券
    margin_stock = fs.get_margin('600519.SH')
    print(margin_stock)

证券列表
--------

.. code-block:: python

    import finshare as fs

    # A股股票列表
    stocks = fs.get_stock_list()
    print(f"共有 {len(stocks)} 只股票")

    # 股票列表筛选（上海市场）
    sh_stocks = fs.get_stock_list('sh')
    print(f"上海市场: {len(sh_stocks)} 只")

    # ETF列表
    etfs = fs.get_etf_list()

    # LOF列表
    lofs = fs.get_lof_list()

    # 期货列表
    futures = fs.get_future_list()

K线周期和复权
------------

.. code-block:: python

    import finshare as fs

    # 不同周期的K线数据
    # 日线（默认）
    daily = fs.get_historical_data('000001.SZ', start='2024-01-01', end='2024-12-31')

    # 周线
    weekly = fs.get_historical_data('000001.SZ', start='2024-01-01', end='2024-12-31', period='weekly')

    # 月线
    monthly = fs.get_historical_data('000001.SZ', start='2023-01-01', end='2024-12-31', period='monthly')

    # 复权类型
    # 前复权（推荐用于技术分析）
    qfq = fs.get_historical_data('000001.SZ', start='2024-01-01', adjust='qfq')

    # 后复权（用于计算真实收益率）
    hfq = fs.get_historical_data('000001.SZ', start='2024-01-01', adjust='hfq')

    # 不复权
    none = fs.get_historical_data('000001.SZ', start='2024-01-01', adjust=None)

使用数据源
----------

.. code-block:: python

    from finshare import EastMoneyDataSource, TencentDataSource, SinaDataSource

    # 使用东方财富（默认，数据最全）
    eastmoney = EastMoneyDataSource()
    data = eastmoney.get_historical_data('000001', start='2024-01-01')

    # 使用腾讯财经
    tencent = TencentDataSource()
    data = tencent.get_historical_data('000001', start='2024-01-01')

    # 使用新浪财经
    sina = SinaDataSource()
    snapshot = sina.get_snapshot_data('000001.SZ')

异步获取
--------

finshare 支持异步批量获取数据，提升性能。

.. code-block:: python

    import finshare as fs

    # 获取异步管理器
    async_manager = fs.get_async_manager(max_workers=10)

    # 异步获取批量K线
    import asyncio

    async def get_data():
        # 批量获取K线
        klines = await async_manager.get_batch_kline(
            ['000001.SZ', '600519.SH', '300750.SZ'],
            start='2024-01-01',
            end='2024-12-31'
        )
        for code, df in klines.items():
            print(f"{code}: {len(df)} 条数据")
        return klines

    # 运行异步函数
    results = asyncio.run(get_data())

缓存使用
--------

.. code-block:: python

    from finshare.cache import cached, MemoryCache

    # 使用装饰器缓存
    @cached(ttl=60)  # 缓存60秒
    def get_cached_data(code):
        return fs.get_snapshot_data(code)

    # 首次调用，会请求数据源
    snapshot1 = get_cached_data('000001.SZ')

    # 60秒内再次调用，直接返回缓存
    snapshot2 = get_cached_data('000001.SZ')

    # 使用内存缓存类
    cache = MemoryCache(max_size=1000)
    cache.set('key', 'value', ttl=60)
    value = cache.get('key')
