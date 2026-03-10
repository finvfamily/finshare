"""
示例 4: 财务数据获取

演示如何获取股票财务数据：利润表、资产负债表、现金流量表、财务指标。
"""

import finshare as fs


def main():
    """运行财务数据获取示例"""

    fs.logger.info("=" * 60)
    fs.logger.info("finshare 财务数据获取示例")
    fs.logger.info("=" * 60)

    code = "000001.SZ"  # 平安银行

    # 1. 获取利润表
    fs.logger.info(f"\n获取 {code} 利润表...")
    try:
        df_income = fs.get_income(code)
        if not df_income.empty:
            fs.logger.info(f"✓ 成功获取 {len(df_income)} 条利润表数据")
            fs.logger.info(f"最新财报日期: {df_income['report_date'].iloc[0]}")
            revenue = float(df_income['revenue'].iloc[0]) if df_income['revenue'].iloc[0] else 0
            net_profit = float(df_income['net_profit'].iloc[0]) if df_income['net_profit'].iloc[0] else 0
            fs.logger.info(f"营业收入: {revenue:,.0f} 元")
            fs.logger.info(f"净利润: {net_profit:,.0f} 元")
        else:
            fs.logger.warning("未获取到利润表数据")
    except Exception as e:
        fs.logger.error(f"获取利润表失败: {e}")

    # 2. 获取资产负债表
    fs.logger.info(f"\n获取 {code} 资产负债表...")
    try:
        df_balance = fs.get_balance(code)
        if not df_balance.empty:
            fs.logger.info(f"✓ 成功获取 {len(df_balance)} 条资产负债表数据")
            fs.logger.info(f"最新财报日期: {df_balance['report_date'].iloc[0]}")
            total_assets = float(df_balance['total_assets'].iloc[0]) if df_balance['total_assets'].iloc[0] else 0
            total_liab = float(df_balance['total_liab'].iloc[0]) if df_balance['total_liab'].iloc[0] else 0
            total_equity = float(df_balance['total_equity'].iloc[0]) if df_balance['total_equity'].iloc[0] else 0
            fs.logger.info(f"总资产: {total_assets:,.0f} 元")
            fs.logger.info(f"总负债: {total_liab:,.0f} 元")
            fs.logger.info(f"股东权益: {total_equity:,.0f} 元")
        else:
            fs.logger.warning("未获取到资产负债表数据")
    except Exception as e:
        fs.logger.error(f"获取资产负债表失败: {e}")

    # 3. 获取现金流量表
    fs.logger.info(f"\n获取 {code} 现金流量表...")
    try:
        df_cashflow = fs.get_cashflow(code)
        if not df_cashflow.empty:
            fs.logger.info(f"✓ 成功获取 {len(df_cashflow)} 条现金流量表数据")
            fs.logger.info(f"最新财报日期: {df_cashflow['report_date'].iloc[0]}")
            operate_cf = float(df_cashflow['operate_cashflow'].iloc[0]) if df_cashflow['operate_cashflow'].iloc[0] else 0
            invest_cf = float(df_cashflow['invest_cashflow'].iloc[0]) if df_cashflow['invest_cashflow'].iloc[0] else 0
            finance_cf = float(df_cashflow['finance_cashflow'].iloc[0]) if df_cashflow['finance_cashflow'].iloc[0] else 0
            fs.logger.info(f"经营活动现金流: {operate_cf:,.0f} 元")
            fs.logger.info(f"投资活动现金流: {invest_cf:,.0f} 元")
            fs.logger.info(f"筹资活动现金流: {finance_cf:,.0f} 元")
        else:
            fs.logger.warning("未获取到现金流量表数据")
    except Exception as e:
        fs.logger.error(f"获取现金流量表失败: {e}")

    # 4. 获取财务指标
    fs.logger.info(f"\n获取 {code} 财务指标...")
    try:
        df_indicator = fs.get_financial_indicator(code)
        if not df_indicator.empty:
            fs.logger.info(f"✓ 成功获取 {len(df_indicator)} 条财务指标数据")
            latest = df_indicator.iloc[0]
            fs.logger.info(f"最新财报日期: {latest['report_date']}")
            fs.logger.info(f"每股收益(EPS): {latest['eps']:.2f} 元")
            fs.logger.info(f"净资产收益率(ROE): {latest['roe']:.2f}%")
            fs.logger.info(f"资产负债率: {latest['debt_to_assets']:.2f}%")
        else:
            fs.logger.warning("未获取到财务指标数据")
    except Exception as e:
        fs.logger.error(f"获取财务指标失败: {e}")

    # 5. 提示
    fs.logger.info("\n" + "=" * 60)
    fs.logger.info("💡 提示:")
    fs.logger.info("  - fs_code 字段格式 (000001.SZ)")
    fs.logger.info("  - 更多财务数据可使用 finshare.stock.financial 模块")


if __name__ == "__main__":
    main()
