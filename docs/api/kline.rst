K线数据
======

get_historical_data
------------------

获取股票/ETF/LOF/港股的历史K线数据。

函数签名
~~~~~~~~

.. code-block:: python

    def get_historical_data(
        code: str,
        start: str = None,
        end: str = None,
        period: str = "daily",
        adjust: str = None,
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
     - 股票代码，如 ``000001.SZ``、``600519.SH``、``00700.HK``
   * - start
     - str
     - 开始日期，格式 ``YYYY-MM-DD``
   * - end
     - str
     - 结束日期，格式 ``YYYY-MM-DD``
   * - period
     - str
     - K线周期：``daily``(日线)、``weekly``(周线)、``monthly``(月线)
   * - adjust
     - str
     - 复权类型：``qfq``(前复权)、``hfq``(后复权)、``None``(不复权)

返回值
~~~~~~

返回 :class:`pandas.DataFrame`，包含以下列：

.. list-table::
   :header-rows: 1

   * - 列名
     - 类型
     - 说明
   * - code
     - str
     - 股票代码
   * - trade_date
     - str
     - 交易日期
   * - open_price
     - float
     - 开盘价
   * - high_price
     - float
     - 最高价
   * - low_price
     - float
     - 最低价
   * - close_price
     - float
     - 收盘价
   * - volume
     - float
     - 成交量(手)
   * - amount
     - float
     - 成交额(元)

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    # 获取日线数据
    df = fs.get_historical_data(
        code='000001.SZ',
        start='2024-01-01',
        end='2024-01-31'
    )

    print(df)

输出结果：

::

            code  trade_date  open_price  high_price  low_price  close_price    volume       amount
    0  000001.SZ   2024-01-02        7.83        7.95       7.78         7.90  79011200  621889760.0
    1  000001.SZ   2024-01-03        7.90        7.98       7.85         7.92  65432100  518901456.0
    ...

获取前复权数据
~~~~~~~~~~~~~~

.. code-block:: python

    import finshare as fs

    df = fs.get_historical_data(
        code='600519.SH',
        start='2023-01-01',
        end='2024-01-31',
        adjust='qfq'  # 前复权
    )

获取周线数据
~~~~~~~~~~~~

.. code-block:: python

    import finshare as fs

    df = fs.get_historical_data(
        code='000001.SZ',
        start='2023-01-01',
        end='2024-01-31',
        period='weekly'
    )

获取港股K线
~~~~~~~~~~~~

.. code-block:: python

    import finshare as fs

    # 港股历史K线（东方财富数据源）
    df = fs.get_historical_data(
        code='00700.HK',  # 腾讯控股
        start='2024-01-01',
        end='2024-12-31'
    )
    print(df.head())

    # 港股前复权
    df_qfq = fs.get_historical_data(
        code='00700.HK',
        start='2024-01-01',
        adjust='qfq'
    )

get_minutely_data
-----------------

获取股票的分钟K线数据。

函数签名
~~~~~~~~

.. code-block:: python

    def get_minutely_data(
        code: str,
        start: str = None,
        end: str = None,
        freq: int = 5,
        adjust: str = None,
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
     - 股票代码
   * - start
     - str
     - 开始时间，格式 ``YYYY-MM-DD`` 或 ``YYYY-MM-DD HH:MM:SS``
   * - end
     - str
     - 结束时间，格式 ``YYYY-MM-DD`` 或 ``YYYY-MM-DD HH:MM:SS``
   * - freq
     - int
     - 频率：``1``、``5``、``15``、``30``、``60`` 分钟
   * - adjust
     - str
     - 复权类型：``qfq``、``hfq``、``None``

返回值
~~~~~~

返回 :class:`pandas.DataFrame`。

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    # 获取5分钟K线（当日）
    df = fs.get_minutely_data(
        code='000001.SZ',
        freq=5
    )

    # 获取指定时间范围的15分钟K线
    df = fs.get_minutely_data(
        code='000001.SZ',
        start='2024-01-15 09:30:00',
        end='2024-01-15 15:00:00',
        freq=15
    )
