财务数据
=========

finshare 提供获取上市公司财务数据的功能，包括利润表、资产负债表、现金流量表、财务指标等。

数据来源：新浪财经、东方财富

get_income
----------

获取利润表数据。

函数签名
~~~~~~~~

.. code-block:: python

    def get_income(
        code: str,
        start_date: str = None,
        end_date: str = None,
    )

参数说明
~~~~~~~~

.. list-table::
   :header-rows: 1

   * - 参数
     - 类型
     - 说明
   * - code
     - str
     - 股票代码，如 ``600519.SH``
   * - start_date
     - str
     - 开始日期（暂不支持）
   * - end_date
     - str
     - 结束日期（暂不支持）

返回值
~~~~~~

返回 :class:`pandas.DataFrame`，包含以下列：

.. list-table::
   :header-rows: 1

   * - 列名
     - 说明
   * - fs_code
     - 股票代码
   * - ann_date
     - 公告日期
   * - report_date
     - 报告期
   * - revenue
     - 营业收入(元)
   * - revenue_yoy
     - 营业收入同比(%)
   * - net_profit
     - 净利润(元)
   * - net_profit_yoy
     - 净利润同比(%)
   * - gross_margin
     - 毛利率(%)
   * - roe
     - 净资产收益率(%)

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    # 获取利润表
    df = fs.get_income('600519.SH')
    print(df.head())

输出结果：

::

         fs_code  ann_date  report_date    revenue  revenue_yoy  net_profit  net_profit_yoy  gross_margin    roe
    0  600519.SH  20240830    20240630  1234567890       15.23    456789012        12.35        52.18    25.63
    ...

get_balance
-----------

获取资产负债表数据。

函数签名
~~~~~~~~

.. code-block:: python

    def get_balance(
        code: str,
        start_date: str = None,
        end_date: str = None,
    )

返回值
~~~~~~

返回 :class:`pandas.DataFrame`，包含以下列：

.. list-table::
   :header-rows: 1

   * - 列名
     - 说明
   * - fs_code
     - 股票代码
   * - ann_date
     - 公告日期
   * - report_date
     - 报告期
   * - total_assets
     - 总资产(元)
   * - total_liab
     - 总负债(元)
   * - total_equity
     - 股东权益(元)
   * - current_assets
     - 流动资产(元)
   * - current_liab
     - 流动负债(元)

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    df = fs.get_balance('600519.SH')
    print(df.head())

输出结果：

::

         fs_code  ann_date  report_date  total_assets  total_liab  total_equity  current_assets  current_liab
    0  600519.SH  20240830    20240630  123456789012  56789123456  66667890123456  234567890123  12345678901
    ...

get_cashflow
------------

获取现金流量表数据。

函数签名
~~~~~~~~

.. code-block:: python

    def get_cashflow(
        code: str,
        start_date: str = None,
        end_date: str = None,
    )

返回值
~~~~~~

返回 :class:`pandas.DataFrame`，包含以下列：

.. list-table::
   :header-rows: 1

   * - 列名
     - 说明
   * - fs_code
     - 股票代码
   * - ann_date
     - 公告日期
   * - report_date
     - 报告期
   * - operate_cashflow
     - 经营活动现金流(元)
   * - invest_cashflow
     - 投资活动现金流(元)
   * - finance_cashflow
     - 筹资活动现金流(元)

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    df = fs.get_cashflow('600519.SH')
    print(df.head())

get_financial_indicator
-----------------------

获取财务指标数据。

函数签名
~~~~~~~~

.. code-block:: python

    def get_financial_indicator(
        code: str,
        ann_date: str = None,
    )

返回值
~~~~~~

返回 :class:`pandas.DataFrame`，包含以下列：

.. list-table::
   :header-rows: 1

   * - 列名
     - 说明
   * - fs_code
     - 股票代码
   * - ann_date
     - 公告日期
   * - report_date
     - 报告期
   * - eps
     - 每股收益(元)
   * - roe
     - 净资产收益率(%)
   * - gross_margin
     - 毛利率(%)
   * - netprofit_margin
     - 净利率(%)
   * - current_ratio
     - 流动比率
   * - quick_ratio
     - 速动比率
   * - debt_to_assets
     - 资产负债率(%)

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    df = fs.get_financial_indicator('600519.SH')
    print(df.head())

输出结果：

::

         fs_code  ann_date  report_date    eps    roe  gross_margin  netprofit_margin  current_ratio  quick_ratio  debt_to_assets
    0  600519.SH  20240830    20240630   52.18   25.63        52.18             31.25           1.82         1.45           28.5
    ...

get_dividend
------------

获取分红送转数据。

.. note::

   注意：分红送股 API 目前暂不可用，返回空数据。

函数签名
~~~~~~~~

.. code-block:: python

    def get_dividend(code: str)

返回值
~~~~~~

返回 :class:`pandas.DataFrame`，包含以下列（目前返回空）：

.. list-table::
   :header-rows: 1

   * - 列名
     - 说明
   * - fs_code
     - 股票代码
   * - ann_date
     - 公告日期
   * - divident_date
     - 分红日期
   * - cash_div
     - 现金分红(元/股)
   * - stock_div
     - 送股(股/10股)
   * - stock_ratio
     - 送股比例
   * - bonus_ratio
     - 分红比例
