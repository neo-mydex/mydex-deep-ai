# confirm_perp_transfer

## 概述

合约资金划转 action，生成 PERPS_DEPOSIT 或 PERPS_WITHDRAW 的 confirm card。

## 参数表

| 参数 | 类型 | 说明 |
|------|------|------|
| action_type | Literal["PERPS_DEPOSIT", "PERPS_WITHDRAW"] | "PERPS_DEPOSIT"=往合约转入，"PERPS_WITHDRAW"=从合约转出 |
| amount | float | 划转数量（USDC） |
| asset | str | 划转资产类型，默认 "USDC" |
| source_text | str | 用户原始表达，不影响逻辑 |

## action_type

- **`PERPS_DEPOSIT`**：往合约账户转入资金
  - 用户说"往合约存款"、"转入合约"、"充值"时使用

- **`PERPS_WITHDRAW`**：从合约账户转出资金
  - 用户说"从合约取款"、"转出合约"、"提现"时使用

## 使用示例

**往合约存入 500 USDC：**
```
action_type="PERPS_DEPOSIT", amount=500, source_text="我要往合约存款"
```

**从合约取出 300 USDC：**
```
action_type="PERPS_WITHDRAW", amount=300, source_text="从合约取款"
```
