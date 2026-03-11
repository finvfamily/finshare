.. finshare documentation master file

finshare | 专业的金融数据获取工具库
=============================================

.. image:: https://img.shields.io/github/stars/finvfamily/finshare
   :target: https://github.com/finvfamily/finshare
   :alt: GitHub stars

.. image:: https://img.shields.io/pypi/v/finshare
   :target: https://pypi.org/project/finshare/
   :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/finshare: https://p
   :targetypi.org/project/finshare/
   :alt: Python versions

.. image:: https://img.shields.io/github/license/finvfamily/finshare
   :target: https://github.com/finvfamily/finshare/blob/main/LICENSE
   :alt: License

finshare 是一个专业的金融数据获取 Python 库，支持从多个数据源获取股票、ETF、LOF、期货等金融产品的历史数据、实时行情、财务数据、特色数据等。

**完全免费**：无需 API Key，无调用次数限制

.. toctree::
   :maxdepth: 2
   :caption: 文档目录

   install
   quickstart
   data_source
   api/index
   examples/index
   faq

功能特性
--------

- **多数据源支持** - 东方财富、腾讯、新浪、通达信、BaoStock，多源自动切换
- **多市场覆盖** - A股、港股、美股、期货、基金，全面金融数据
- **自动故障切换** - 数据源失败时自动切换备用源，保证服务可用
- **高性能获取** - 支持异步批量获取，减少等待时间
- **内置缓存机制** - 减少重复请求，提升响应速度
- **统一数据格式** - 所有数据源返回统一格式，方便处理
- **企业级稳定性** - 熔断器、智能路由、健康探测、监控统计

支持的数据类型
-------------

.. list-table::
   :header-rows: 1

   * - 类别
     - 数据类型
     - 接口函数
     - 说明
   * - 股票
     - 历史K线
     - ``get_historical_data``
     - 日线、周线、月线、分钟线，支持前/后复权
   * -
     - 实时快照
     - ``get_snapshot_data``
     - 实时行情报价
   * -
     - 批量快照
     - ``get_batch_snapshots``
     - 批量获取多只股票行情
   * - 港股
     - 实时快照
     - ``get_snapshot_data``
     - 腾讯/新浪数据源
   * -
     - 历史K线
     - ``get_historical_data``
     - 东方财富数据源
   * - 期货
     - 历史K线
     - ``get_future_kline``
     - 支持所有国内期货品种
   * -
     - 实时快照
     - ``get_future_snapshot``
     - 新浪实时行情
   * -
     - 批量快照
     - ``get_batch_future_snapshots``
     - 批量获取期货行情
   * - 基金
     - 基金净值
     - ``get_fund_nav``
     - 场外基金净值数据
   * -
     - 基金信息
     - ``get_fund_info``
     - 基金基本信息
   * -
     - 基金列表
     - ``get_fund_list``
     - 全部基金列表
   * - 财务数据
     - 利润表
     - ``get_income``
     - 营业收入、净利润等
   * -
     - 资产负债表
     - ``get_balance``
     - 总资产、负债等
   * -
     - 现金流量表
     - ``get_cashflow``
     - 经营/投资/筹资现金流
   * -
     - 财务指标
     - ``get_financial_indicator``
     - EPS、ROE、毛利率等
   * - 特色数据
     - 资金流向
     - ``get_money_flow``
     - 个股资金流向
   * -
     - 行业资金流向
     - ``get_money_flow_industry``
     - 各行业资金流向
   * -
     - 龙虎榜
     - ``get_lhb``
     - 历史龙虎榜数据
   * -
     - 龙虎榜明细
     - ``get_lhb_detail``
     - 营业部买卖明细
   * -
     - 融资融券
     - ``get_margin``
     - 市场/个股融资融券
   * -
     - 融资融券明细
     - ``get_margin_detail``
     - 个股融资融券明细
   * - 证券列表
     - 股票列表
     - ``get_stock_list``
     - A股全部股票
   * -
     - ETF列表
     - ``get_etf_list``
     - 全部ETF基金
   * -
     - LOF列表
     - ``get_lof_list``
     - 全部LOF基金
   * -
     - 期货列表
     - ``get_future_list``
     - 期货合约列表

快速开始
--------

安装::

    pip install finshare

使用::

    import finshare as fs

    # 获取历史K线数据
    df = fs.get_historical_data('000001.SZ', start='2024-01-01', end='2024-01-31')
    print(df.head())

    # 获取实时快照
    snapshot = fs.get_snapshot_data('000001.SZ')
    print(f"最新价: {snapshot.last_price}")

    # 批量获取行情
    snapshots = fs.get_batch_snapshots(['000001.SZ', '600519.SH'])

高级特性
--------

.. list-table::
   :header-rows: 1

   * - 模块
     - 功能
     - 说明
   * - 缓存系统
     - 内存/Redis缓存
     - 支持TTL配置，减少重复请求
   * - 异步客户端
     - AsyncDataSourceManager
     - 批量异步获取，提升性能
   * - 熔断器
     - CircuitBreaker
     - 故障自动熔断，保护系统
   * - 智能路由
     - SmartRouter
     - 按数据类型偏好路由
   * - 监控统计
     - Monitor
     - 请求统计、性能分析

.. note::

   本项目完全由 AI (Claude) 实现，展示了 AI 在软件工程领域的强大能力。

.. include:: ../README.md
   :parser: myst_parser.sphinx_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
