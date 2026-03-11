期货数据
========

finshare 支持获取国内期货市场的历史K线和实时行情数据。

get_future_kline
----------------

获取期货历史K线数据。

函数签名
~~~~~~~~

.. code-block:: python

    def get_future_kline(
        code: str,
        start_date: str = None,
        end_date: str = None,
        adjustment: str = "none",
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
     - 期货合约代码，如 ``IF2409``、``CU0``、``AU2409``
   * - start_date
     - str
     - 开始日期，格式 ``YYYY-MM-DD``
   * - end_date
     - str
     - 结束日期，格式 ``YYYY-MM-DD``
   * - adjustment
     - str
     - 复权类型（期货不支持，默认none）

返回值
~~~~~~

返回 ``List[HistoricalData]``，每个元素包含以下属性：

.. list-table::
   :header-rows: 1

   * - 属性
     - 类型
     - 说明
   * - code
     - str
     - 期货合约代码
   * - trade_date
     - date
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

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    # 获取股指期货K线
    data = fs.get_future_kline('IF2409', '2024-01-01', '2024-07-17')

    for item in data:
        print(f"{item.trade_date}: 开盘={item.open_price}, 收盘={item.close_price}")

输出结果：

::

    2024-01-02: 开盘=3421.0, 收盘=3450.0
    2024-01-03: 开盘=3450.0, 收盘=3480.0
    ...

支持的交易所和品种
~~~~~~~~~~~~~~~~

**CFFEX（中金所）** - 股指期货：

.. list-table::
   :header-rows: 1

   * - 合约
     - 品种
     - 示例
   * - IF
     - 沪深300股指
     - IF2409, IF0
   * - IH
     - 上证50股指
     - IH2409, IH0
   * - IC
     - 中证500股指
     - IC2409, IC0

**SHFE（上期所）** - 金属/能源：

.. list-table::
   :header-rows: 1

   * - 合约
     - 品种
     - 示例
   * - CU
     - 沪铜
     - CU2409, CU0
   * - AL
     - 沪铝
     - AL2409, AL0
   * - ZN
     - 沪锌
     - ZN2409, ZN0
   * - PB
     - 沪铅
     - PB2409, PB0
   * - NI
     - 沪镍
     - NI2409, NI0
   * - AU
     - 沪金
     - AU2409, AU0
   * - AG
     - 沪银
     - AG2409, AG0
   * - RU
     - 天然橡胶
     - RU2409, RU0
   * - SC
     - 原油
     - SC2409, SC0

**DCE（大商所）** - 农产品/化工：

.. list-table::
   :header-rows: 1

   * - 合约
     - 品种
     - 示例
   * - A
     - 豆一
     - A2409, A0
   * - B
     - 豆二
     - B2409, B0
   * - M
     - 豆粕
     - M2409, M0
   * - Y
     - 豆油
     - Y2409, Y0
   * - P
     - 棕榈油
     - P2409, P0
   * - J
     - 焦炭
     - J2409, J0
   * - JM
     - 焦煤
     - JM2409, JM0
   * - I
     - 铁矿石
     - I2409, I0
   * - RB
     - 螺纹钢
     - RB2409, RB0
   * - HC
     - 热卷
     - HC2409, HC0

**CZCE（郑商所）** - 农产品/化工：

.. list-table::
   :header-rows: 1

   * - 合约
     - 品种
     - 示例
   * - SR
     - 白糖
     - SR2409, SR0
   * - CF
     - 棉花
     - CF2409, CF0
   * - TA
     - PTA
     - TA2409, TA0
   * - MA
     - 甲醇
     - MA2409, MA0
   * - FG
     - 玻璃
     - FG2409, FG0
   * - RM
     - 菜粕
     - RM2409, RM0
   * - AP
     - 苹果
     - AP2409, AP0

**INE（上期能源）**：

.. list-table::
   :header-rows: 1

   * - 合约
     - 品种
     - 示例
   * - SC
     - 原油
     - SC2409, SC0

连续合约说明
~~~~~~~~~~~~

使用 ``0`` 获取主力连续合约：

- ``IF0`` - 沪深300当月连续
- ``IF1`` - 沪深300下月连续
- ``CU0`` - 沪铜当月连续
- ``AU0`` - 沪金当月连续

get_future_snapshot
-------------------

获取期货实时快照。

函数签名
~~~~~~~~

.. code-block:: python

    def get_future_snapshot(code: str)

返回值
~~~~~~

返回 ``FutureSnapshotData`` 对象，包含以下属性：

.. list-table::
   :header-rows: 1

   * - 属性
     - 类型
     - 说明
   * - code
     - str
     - 合约代码
   * - last_price
     - float
     - 最新价
   * - change
     - float
     - 涨跌额
   * - change_pct
     - float
     - 涨跌幅(%)
   * - volume
     - float
     - 成交量(手)
   * - open_interest
     - float
     - 持仓量(手)
   * - amount
     - float
     - 成交额(元)
   * - bid1_price
     - float
     - 买一价
   * - ask1_price
     - float
     - 卖一价
   * - day_open
     - float
     - 开盘价
   * - day_high
     - float
     - 最高价
   * - day_low
     - float
     - 最低价
   * - prev_close
     - float
     - 昨结算价

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    # 获取期货快照
    snapshot = fs.get_future_snapshot('IF2409')

    print(f"合约: {snapshot.code}")
    print(f"最新价: {snapshot.last_price}")
    print(f"涨跌额: {snapshot.change}")
    print(f"涨跌幅: {snapshot.change_pct}%")
    print(f"持仓量: {snapshot.open_interest}")
    print(f"成交量: {snapshot.volume}")

输出结果：

::

    合约: IF2409
    最新价: 3450.0
    涨跌额: 30.0
    涨跌幅: +0.88%
    持仓量: 123456.0
    成交量: 98765.0

get_batch_future_snapshots
--------------------------

批量获取期货实时快照。

函数签名
~~~~~~~~

.. code-block:: python

    def get_batch_future_snapshots(codes: list)

返回值
~~~~~~

返回 ``Dict[str, FutureSnapshotData]``。

使用示例
~~~~~~~~

.. code-block:: python

    import finshare as fs

    # 批量获取期货快照
    results = fs.get_batch_future_snapshots(['IF2409', 'CU2409', 'AU2409', 'SC2409'])

    for code, snapshot in results.items():
        print(f"{code}: {snapshot.last_price} ({snapshot.change_pct:+.2f}%)")

输出结果：

::

    IF2409: 3450.0 (+0.88%)
    CU2409: 78500.0 (-1.20%)
    AU2409: 580.0 (+0.50%)
    SC2409: 620.0 (-2.15%)
