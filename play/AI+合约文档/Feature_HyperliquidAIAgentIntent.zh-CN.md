# Hyperliquid AI Agent 意图 JSON 交接文档

> 参考文档：
> 
> - `docs/hyperliquid-ai-agent-integration.md`
> - `docs/hyperliquid-info-api-direct.md`
> - Hyperliquid API: `https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint`
> 
> 目标：给 AI Agent 同事一套可直接复用的 Hyperliquid 合约意图 JSON 模板，并明确哪些字段只是 NLP 解析结果，哪些字段可以直接对接执行层。
> 
> 约定：
> 
> - `confidence` 是**可选元数据**
> - 仅供 AI 意图解析 / 编排层使用
> - 不属于 Hyperliquid API 字段
> - 不进入最终执行层参数

---

## 1. 两层协议约定

建议把 AI 输出分成两层：

- **Simple Mode**
  - 给 NLP / Agent 编排层使用
  - 强调“用户想做什么”
  - 还不直接等同于 app 执行参数
- **Advanced Mode**
  - 给执行器使用
  - 尽量贴近当前 app 的实际意图结构
  - 当前 app 的主要执行意图见：
    - `PerpAssetsIntent.UpdateLeverage`
    - `PerpAssetsIntent.OpenOrder`
    - `PerpAssetsIntent.ClosePosition`
    - `PerpAssetsIntent.SetTpsl`
  - 代码位置：`app/src/main/java/io/mydex/app/feature/assets/perps/PerpAssetsViewModel.kt:1329`

---

## 1.1 下单前必须先做的只读查询

在生成 `OPEN_LONG` / `OPEN_SHORT` 执行计划前，建议 AI 或编排层先做这 4 类只读查询：

1. **查用户当前仓位**
   - Hyperliquid 官方：`POST https://api.hyperliquid.xyz/info`
   - `type = clearinghouseState`
   - 作用：
     - 读取 `withdrawable`，判断当前是否还有可用保证金
     - 判断该 coin 是否已有持仓
     - 判断持仓方向和仓位大小
     - 读取 `marginUsed`、`entryPx`、`unrealizedPnl` 等信息
2. **查用户当前杠杆与保证金模式**
   - 接口：`GET /perps-api/info/get-user-margin-setting`
   - 作用：
     - 判断当前 `isCross`
     - 判断当前 `leverage`
     - 判断是否需要先做 `UPDATE_LEVERAGE`
3. **查用户当前未成交订单**
   - Hyperliquid 官方：`POST https://api.hyperliquid.xyz/info`
   - `type = frontendOpenOrders`
   - 作用：
     - 判断该 coin 是否已有挂单
     - 判断是否已有 TPSL 挂单
     - 避免重复下单 / 重复设置 TPSL
4. **查当前市场价格**
   - Hyperliquid 官方：`POST https://api.hyperliquid.xyz/info`
   - `type = allMids`
   - 作用：
     - 获取 `markPrice`
     - 用于 `size` 换算
     - 用于校验 TP / SL 合理性

> 约定：**除 `get-user-margin-setting` 外，其余查询优先直接走 Hyperliquid 官方只读 API。**

---

## 1.2 我们当前只支持 one-way 仓位

当前 AI 执行器和 app 都按 **one-way position** 设计，不支持 hedge mode 的“同币种同时多空双向持仓”。

因此在生成开仓意图前，需要遵守以下规则：

- 同一币种只允许有一个净方向仓位
- 如果已有 `BTC` 多仓：
  - 不应再直接生成新的 `OPEN_SHORT`
  - 应先提示用户平仓，或走明确的反手 / 平仓逻辑
- 如果已有 `BTC` 空仓：
  - 不应再直接生成新的 `OPEN_LONG`
- 如读取到的仓位类型不是 `oneWay`，AI 侧应视为**当前不支持的账户状态**

这点和 Hyperliquid 的原始能力不同；这是**当前我方产品实现约束**。

---

## MODE说明！！！

<mark>AI只返回Advance mode给到前端</mark>

## 新增存款/取款

> 需要前端自己检查可用余额

```json
{
    "action": "PERPS_DEPOSIT",
    "amount": 500, # 表示存500个asset
    "asset": "USDC", # 默认就是USDC，说U就是USDC，说ETH就是ETH
}
```

```json
{
    "action": "PERPS_WITHDRAW",
    "amount": 500, # 表示存500个asset
    "asset": "USDC", # 写死就是USDC，不能取别的
}
```

## 2. OPEN_LONG（单笔开多/补仓）

> meta字段只有source text和agent requestid 必须有，其他的不做强制要求，只做备注

### 2.1 Simple Mode

```json
{
  "action": "OPEN_LONG",
  "coin": "BTC",
  "leverage": 20,
  "usdc_size": 1000,
  "margin_mode": "cross",
  "order_type": "market",
  "tp": 72000,
  "sl": 66500,
  "confidence": 0.97,
  "source_text": "做多 BTC 20x 1000u，止盈 72000，止损 66500"
}
```

### 2.2 Advanced Mode

```json
{
  "action": "OPEN_LONG",
  "execution_plan": [
    {
      "intent": "UPDATE_LEVERAGE",
      "coin": "BTC",
      "leverage": 20,
      "isCross": true
    },
    {
      "intent": "OPEN_ORDER",
      "coin": "BTC",
      "isBuy": true,
      "size": "0.2921",
      "markPrice": 68450.5,
      "orderType": "market",
      "limitPrice": null,
      "tpPrice": "72000",
      "slPrice": "66500"
    },
    { # 如果是补仓的话
      "intent": "OPEN_ORDER",
      "coin": "BTC",
      "isBuy": true,
      "size": "0.2921",
      "markPrice": 68450.5,
      "orderType": "market",
      "limitPrice": null,
      "tpPrice": "72000",
      "slPrice": "66500"
    }
  ],
  "meta": {
    "input_usdc_size": 1000,
    "size_calc_basis": "size = usdc_size * leverage / markPrice",
    "source_text": "做多 BTC 20x 1000u，止盈 72000，止损 66500",
    "agent_request_id": "hl-open-long-20260324-001"
  }
}
```

---

## 3. OPEN_SHORT（单笔开空）

### 3.1 Simple Mode

```json
{
  "action": "OPEN_SHORT",
  "coin": "ETH",
  "leverage": 10,
  "usdc_size": 500,
  "margin_mode": "isolated",
  "order_type": "limit",
  "limit_price": 3650,
  "tp": 3450,
  "sl": 3720,
  "confidence": 0.95,
  "source_text": "ETH 10x 限价 3650 开空 500u，止盈 3450，止损 3720"
}
```

### 3.2 Advanced Mode

```json
{
  "action": "OPEN_SHORT",
  "execution_plan": [
    {
      "intent": "UPDATE_LEVERAGE",
      "coin": "ETH",
      "leverage": 10,
      "isCross": false
    },
    {
      "intent": "OPEN_ORDER",
      "coin": "ETH",
      "isBuy": false,
      "size": "1.3698",
      "markPrice": 3650.0,
      "orderType": "limit",
      "limitPrice": 3650.0,
      "tpPrice": "3450",
      "slPrice": "3720"
    }
  ],
  "meta": {
    "input_usdc_size": 500,
    "margin_mode": "isolated", # 逐仓，没说就给null
    "source_text": "ETH 10x 限价 3650 开空 500u",
    "agent_request_id": "hl-open-short-20260324-001"
  }
}
```

---

## 4. CLOSE_POSITION（平仓）

### 4.1 Simple Mode

```json
{
  "action": "CLOSE_POSITION",
  "asset": "BTC",
  "close_mode": "full",
  "confidence": 0.99,
  "source_text": "把 BTC 仓位全平掉"
}
```

### 4.2 Advanced Mode（平/批量平）

```json
{
  "action": "CLOSE_POSITION",
  "execution_plan": [
    {
      "intent": "CLOSE_POSITION",
      "coin": "BTC",
      "size": "0.2921", # 头寸（（杠杆*保证金）/markPrice）
      "isLong": true,
      "markPrice": 68720.2, # 想要平仓的目标价格
      "close_ratio": 1 # 表示百分百平仓
    }，
    # 其实每一个coin只能有一个多/空
    {...如果有第二笔}，
    {...如果有第三笔}
  ],
  "meta": {
    "source_text": "把 BTC 仓位全平掉",
    "agent_request_id": "hl-close-full-20260324-001"
  }
}
```

### 4.3 Advanced Mode（一笔的部分平仓）

> 卡片格式同上，只改了close_ratio < 1

```json
{
  "action": "CLOSE_POSITION",
  "execution_plan": [
    {
      "intent": "CLOSE_POSITION",
      "coin": "BTC",
      "size": "0.1000",
      "isLong": true,
      "markPrice": 68720.2,
      "close_ratio": 0.34, # 平仓的百分比
    }
  ],
  "meta": {
    "source_text": "平掉三分之一 BTC 多仓",
    "agent_request_id": "hl-close-partial-20260324-001"
  }
}
```

---

## 5. SET_TPSL（设置止盈止损）

### 5.1 Simple Mode

```json
{
  "action": "SET_TPSL",
  "asset": "BTC",
  "tp": 72000,
  "sl": 66500,
  "confidence": 0.98,
  "source_text": "BTC 仓位止盈 72000，止损 66500"
}
```

### 5.2 Advanced Mode

```json
{
  "action": "SET_TPSL",
  "execution_plan": [
    {
      "intent": "SET_TPSL",
      "coin": "BTC",
      "size": "0.2921",
      "tpPrice": "72000",
      "slPrice": "66500",
      "existingTpOid": 0,
      "existingSlOid": 0
    }
  ],
  "meta": {
    "source_text": "BTC 仓位止盈 72000，止损 66500",
    "agent_request_id": "hl-set-tpsl-20260324-001"
  }
}
```

如果是更新已有 TPSL，可以把旧订单号一起传入：

```json
{
  "action": "SET_TPSL",
  "execution_plan": [
    {
      "intent": "SET_TPSL",
      "coin": "BTC",
      "size": "0.2921",
      "tpPrice": "72500",
      "slPrice": "66800",
      "existingTpOid": 18273645,
      "existingSlOid": 18273646
    }
  ]
}
```

---

## 6. VIEW_POSITION（查看仓位）

### 6.1 Simple Mode

```json
{
  "action": "VIEW_POSITION",
  "asset": "BTC",
  "source_text": "看看我 BTC 仓位"
}
```

### 6.2 Advanced Mode

```json
{
  "action": "VIEW_POSITION",
  "query": {
    "user_address": "0x1234567890abcdef1234567890abcdef12345678",
    "asset": "BTC",
    "include_open_orders": true,
    "include_tpsl": true
  },
  "meta": {
    "agent_request_id": "hl-view-position-20260324-001"
  }
}
```

---

## 6.1 只读查询接口补充（AI 编排层建议直接接入）

### A. 查询用户当前杠杆与保证金模式（MyDex Backend）

接口：

```http
GET /perps-api/info/get-user-margin-setting?walletAddress=0xUserEvmAddressHere&coin=BTC
```

示例响应：

```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "walletAddress": "0xUserEvmAddressHere",
    "coin": "BTC",
    "isCross": true,
    "leverage": 20
  }
}
```

用途：

- 判断当前是不是全仓
- 判断当前杠杆是否已满足用户意图
- 决定是否要先发 `UPDATE_LEVERAGE`

### B. 查询用户某个币种的实时仓位

Hyperliquid 官方接口：

```json
{
  "type": "clearinghouseState",
  "user": "0xUserEvmAddressHere"
}
```

从返回的 `assetPositions` 中筛选：

```json
{
  "type": "oneWay",
  "position": {
    "coin": "BTC",
    "szi": "0.2921",
    "entryPx": "68450.5",
    "markPrice": "68720.2",
    "marginUsed": "1000",
    "positionValue": "20000",
    "unrealizedPnl": "78.92",
    "returnOnEquity": "0.07892",
    "liquidationPx": "65000",
    "leverage": {
      "type": "cross",
      "value": 20
    }
  }
}
```

用途：

- 判断当前是否还有可用保证金（优先看 `withdrawable`）
- 判断某个币种当前是否已有仓位
- 判断方向：
  - `szi > 0` = 多仓
  - `szi < 0` = 空仓
- 判断仓位类型是否为 `oneWay`
- 生成仓位卡片
- 为 `CLOSE_POSITION` / `SET_TPSL` 提供输入参数

注意：

- 需要传入用户真实账户地址
- 不要误传 agent wallet 地址，否则可能查到空结果
- 如果目的是判断“现在还能不能开仓”，优先使用 `withdrawable`

### C. 查询用户当前未成交订单

Hyperliquid 官方接口：

```http
POST https://api.hyperliquid.xyz/info
```

请求体建议使用 `frontendOpenOrders`，因为它比 `openOrders` 多前端友好字段，更适合 AI 编排：

```json
{
  "type": "frontendOpenOrders",
  "user": "0xUserEvmAddressHere"
}
```

示例响应：

```json
[
  {
    "coin": "BTC",
    "oid": 18273645,
    "isPositionTpsl": true,
    "isTrigger": true,
    "side": "A",
    "triggerPx": "72000",
    "limitPx": "0",
    "origSz": "0.2921",
    "sz": "0.2921",
    "reduceOnly": true,
    "orderType": "Take Profit Market",
    "triggerCondition": "tp",
    "timestamp": 1774000000000
  }
]
```

用途：

- 判断该 coin 是否已有未成交主单
- 判断是否已有 TP / SL 单
- 避免重复开仓
- 更新 TPSL 时带上 `existingTpOid` / `existingSlOid`

### D. 查询实时价格

Hyperliquid 官方接口：

```json
{
  "type": "allMids"
}
```

用途：

- 获取 `markPrice`
- 计算 `size`
- 校验 TP / SL

---

## 7. 与当前 app 执行层的字段对应关系

### 7.1 开仓

当前 app 下单意图结构：

```json
{
  "coin": "BTC",
  "isBuy": true,
  "size": "0.2921",
  "markPrice": 68450.5,
  "orderType": "market",
  "limitPrice": null,
  "tpPrice": "72000",
  "slPrice": "66500"
}
```

对应代码：`app/src/main/java/io/mydex/app/feature/assets/perps/PerpAssetsViewModel.kt:1359`

### 7.2 杠杆

当前 app 杠杆是单独更新的，不包含在 `OPEN_ORDER` 里：

```json
{
  "coin": "BTC",
  "leverage": 20,
  "isCross": true
}
```

对应代码：`app/src/main/java/io/mydex/app/feature/assets/perps/PerpAssetsViewModel.kt:1370`

### 7.3 平仓

```json
{
  "coin": "BTC",
  "size": "0.2921",
  "isLong": true,
  "markPrice": 68720.2,
  "isFullClose": true
}
```

对应代码：`app/src/main/java/io/mydex/app/feature/assets/perps/PerpAssetsViewModel.kt:1376`

### 7.4 TPSL

```json
{
  "coin": "BTC",
  "size": "0.2921",
  "tpPrice": "72000",
  "slPrice": "66500",
  "existingTpOid": 0,
  "existingSlOid": 0
}
```

对应代码：`app/src/main/java/io/mydex/app/feature/assets/perps/PerpAssetsViewModel.kt:1343`

---

## 8. AI 同事执行前检查清单

### 8.1 意图解析层

- `action` 必须明确，不要返回模糊意图
- `asset` 必须统一成 Hyperliquid coin code，例如 `BTC`、`ETH`
- `margin_mode` 只允许：
  - `cross`
  - `isolated`
- `order_type` 只允许：
  - `market`
  - `limit`
- `tp/sl` 可以为空，但不能出现方向上明显错误的价格

### 8.2 交易参数层

- `usdc_size` 是用户投入的保证金，不是合约张数
- 执行前必须把 `usdc_size` 换算成 `size`
- `size` 必须根据 `szDecimal` 做 round
- `markPrice` 必须来自最新市场数据，不能长期缓存
- 限价单必须同时满足：
  - `orderType = "limit"`
  - `limitPrice != null`
- 市价单在当前 app 中实际会被转成：
  - `IOC`
  - 带滑点保护的 limit 价格
  - 参考实现：`app/src/main/java/io/mydex/app/feature/assets/perps/PerpAssetsViewModel.kt:889`

### 8.3 杠杆与模式

- 开仓前先查 `get-user-margin-setting`
- 杠杆不是下单字段，而是单独的 `UPDATE_LEVERAGE`
- 如果用户明确说了 `20x`，执行器应先更新杠杆，再下单
- `cross` / `isolated` 也应在杠杆更新阶段确认
- 如果当前 `isCross / leverage` 已和目标一致，可以跳过 `UPDATE_LEVERAGE`

### 8.4 TPSL

- 设置 TPSL 前先查 `frontendOpenOrders`
- TP/SL 应使用字符串形式传入，和当前 app 保持一致
- TP/SL 本质是独立的 reduce-only trigger order
- 开多时：
  - 主单 `isBuy = true`
  - TP/SL 子单方向应相反
- 开空时：
  - 主单 `isBuy = false`
  - TP/SL 子单方向应相反
- 如果是修改已有 TPSL，优先传 `existingTpOid` / `existingSlOid`

### 8.5 风控

- 开仓前先查 `clearinghouseState`
- 下单前检查账户保证金是否充足
- 保证金检查优先使用 `withdrawable`，不要只看 `marginSummary.accountValue`
- 开仓前检查该币种是否已有仓位
- 如果已有同币种仓位，先判断是否 still `oneWay`
- 如果已有同币种反向仓位，不要直接再开新方向仓位
- 如果已有同币种同向仓位，需明确是否允许“加仓”；若产品未定义，则默认阻止并提示确认
- 如果该 coin 已有未成交主单，默认不要重复开新单
- 平仓前检查当前仓位是否存在
- 部分平仓时检查 `close_size <= current_position_size`
- TP/SL 必须满足基本价格逻辑：
  - 多仓：`tp > entry`，`sl < entry`
  - 空仓：`tp < entry`，`sl > entry`
- 如果从 `assetPositions[].type` 读到的不是 `oneWay`，当前 AI 执行器应视为不支持
- 需要保留：
  - `source_text`
  - `confidence`
  - `agent_request_id`
    便于审计、回放和问题排查

### 8.6 OPEN_LONG / OPEN_SHORT 专项检查

在生成开仓执行计划前，建议严格按下面顺序检查：

1. 调 Hyperliquid `clearinghouseState`
   - 确认传入的是用户真实账户地址
   - 读取 `withdrawable`
   - 读取该 coin 当前仓位
   - 检查是否已有持仓
   - 检查仓位类型是否为 `oneWay`
2. 调 `get-user-margin-setting`
   - 读取当前 `isCross`
   - 读取当前 `leverage`
   - 判断是否需要 `UPDATE_LEVERAGE`
3. 调 Hyperliquid `frontendOpenOrders`
   - 检查是否已有未成交主单
   - 检查是否已有旧的 TPSL 单
4. 调 `allMids`
   - 获取当前 `markPrice`
   - 用于 `size` 换算和 TP/SL 校验
5. 生成执行计划
   - 如需调整杠杆：`UPDATE_LEVERAGE`
   - 再执行：`OPEN_ORDER`

默认阻止下单的情况：

- `withdrawable` 不足
- 同币种已有反向仓位
- 仓位类型不是 `oneWay`
- 已存在同币种未成交主单
- `size` 无法按精度合法化
- `tp/sl` 与方向不匹配

补充说明：

- 当前文档约定中，只有 `get-user-margin-setting` 继续走我方后端
- 用户仓位、未成交订单、市场价格都优先直接走 Hyperliquid 官方只读接口

---

## 9. 推荐落地方式

- **如果 AI 只负责理解用户意图**：输出 **Simple Mode**
- **如果 AI 直接对接执行器**：输出 **Advanced Mode**
- **如果执行器就是当前 Android app 这套结构**：
  - 开仓统一拆成 `UPDATE_LEVERAGE + OPEN_ORDER`
  - 平仓走 `CLOSE_POSITION`
  - 修改止盈止损走 `SET_TPSL`
  - 查询仓位走 `VIEW_POSITION`

---

## 10. 一句话结论

给 AI 同事的最稳妥约定是：

- 上游 NLP 用 **Simple Mode**
- 下游执行器用 **Advanced Mode**
- 不要把 `usdc_size` 直接当成 Hyperliquid 的 `size`
- 不要把杠杆直接塞进下单动作里
