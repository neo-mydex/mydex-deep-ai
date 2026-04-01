# Hyperliquid Info API 只读接入说明

> **核心原则**：只读取数据（Query），不构造交易（不碰私钥）。
> 
> 官方参考：
> 
> - Hyperliquid Info endpoint: `https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint`

---

## 1. 环境准备

### 1.1 官方 SDK (推荐)

这是最简单的方式，SDK 已经封装好了所有 HTTP 请求。

```bash
# Python
pip install hyperliquid-python-sdk

# TypeScript / Node.js
npm install hyperliquid-typescript-sdk
```

### 1.2 直接使用 HTTPS (最原始)

如果不方便引入 SDK，可以直接请求以下 Endpoint。

* **主网 (Mainnet)**:
  * `https://api.hyperliquid.xyz/info`
* **测试网 (Testnet)**:
  * `https://api.hyperliquid-testnet.xyz/info`

**请求方式**：`POST`
**Content-Type**: `application/json`

---

## 2. 核心概念映射 (Cheat Sheet)

在调用 API 前，请熟记这几个对应关系，这是业务理解的基石：

| 你想干啥            | API 方法名 (Action)                                                | SDK 函数 (Python)                         | 关键返回字段                                   |
|:--------------- |:--------------------------------------------------------------- |:--------------------------------------- |:---------------------------------------- |
| **查用户余额/保证金**   | `clearinghouseState`                                            | `info.perpetuals_clearinghouse_state()` | `marginSummary.accountValue`             |
| **查用户仓位**       | `clearinghouseState`                                            | `info.perpetuals_clearinghouse_state()` | `assetPositions[].position`              |
| **查用户杠杆/保证金模式** | **MyDex Backend** `GET /perps-api/info/get-user-margin-setting` | 无官方 SDK，对接我方 BFF                        | `isCross`, `leverage`                    |
| **查行情/标记价**     | `allMids`                                                       | `info.all_mids()`                       | `{ "BTC": "44000.5" }`                   |
| **查合约元数据**      | `meta`                                                          | `info.meta()`                           | `universe[].name` (BTC, ETH)             |
| **查用户未成交订单**    | `openOrders` / `frontendOpenOrders`                             | SDK 可直接调用对应 info 方法                     | `oid`, `coin`, `reduceOnly`, `triggerPx` |
| **查 K 线数据**     | `candleSnapshot`                                                | `info.candle_snapshot()`                | `t`, `o`, `h`, `l`, `c`                  |
| **查订单状态**       | `orderStatus`                                                   | `info.query_order_by_oid()`             | `order.status`                           |

---

## 3. 必备 API 详解 (直接复制可用)

### 3.1 获取用户账户状态与可用保证金 (Clearinghouse State)

**用途**：判断用户是否有钱开仓，用于风控检查，同时读取仓位与账户状态。

* **HTTP Request**:
  
  ```json
  {
  "method": "POST",
  "url": "https://api.hyperliquid.xyz/info",
  "headers": { "Content-Type": "application/json" },
  "body": {
  "type": "clearinghouseState",
  "user": "0xUserEvmAddressHere"
  }
  }
  ```

* **SDK 调用 (Python)**:
  
  ```python
  from hyperliquid.info import Info
  from hyperliquid.utils import constants
  ```

info = Info(constants.MAINNET_API_URL, skip_ws=True)

user_address = "0xUserEvmAddressHere"
state = info.perpetuals_clearinghouse_state(user_address)

# 用户总账户价值 (USDC)

total_account_value = float(state["marginSummary"]["accountValue"])

# 用户可提取 / 可用保证金 (USDC)

# 官方 clearinghouseState 返回字段是 withdrawable

available_margin = float(state["withdrawable"])

print(f"总资产: {total_account_value}, 可用保证金: {available_margin}")

```
*   **对齐官方文档的注意点**:
    *   `clearinghouseState` 的常见顶层字段包括：
        *   `marginSummary`
        *   `crossMarginSummary`
        *   `crossMaintenanceMarginUsed`
        *   `withdrawable`
        *   `assetPositions`
        *   `time`
    *   如果你要判断“现在还能不能开仓”，优先使用 `withdrawable`
    *   官方文档特别强调：要传**真实账户地址**，不要误传 agent wallet 地址，否则很容易拿到空结果

---

### 3.2 获取用户仓位信息 (Position)
**用途**：生成“仓位卡片”，展示当前持仓盈亏。

*   **HTTP Request**: (同上，也是 `clearinghouseState`)
*   **SDK 调用 (Python)**:
```python
# 接上面的 state 变量
positions = state.get("assetPositions", [])

if positions:
    for pos_data in positions:
        pos = pos_data["position"]
        print(f"币种: {pos['coin']}")
        print(f"仓位大小: {pos['szi']}")      # 注意：这是合约张数，有正负（正多负空）
        print(f"开仓价: {pos['entryPx']}")
        print(f"杠杆: {pos['leverage']['value']}")
        print(f"未实现盈亏: {pos['unrealizedPnl']}")
        print(f"强平价: {pos['liquidationPx']}")
else:
    print("用户没有仓位")
```

---

### 3.3 获取合约元数据与行情 (Meta & Mids)

**用途**：获取支持的币种列表、当前标记价格（用于计算 TPSL 或 PnL）。

* **HTTP Request (获取所有币种当前价格)**:
  
  ```json
  {
  "type": "allMids"
  }
  ```

* **SDK 调用 (Python)**:
  
  ```python
  # 1. 获取支持的合约列表 (BTC, ETH 等)
  meta = info.meta()
  supported_assets = [asset["name"] for asset in meta["universe"]]
  print("支持的资产:", supported_assets)
  ```

# 2. 获取所有币种当前标记价

mids = info.all_mids()
btc_price = float(mids["BTC"])
eth_price = float(mids["ETH"])
print(f"BTC 当前价格: {btc_price}")

```
---

### 3.4 获取用户未成交订单 (Open Orders)
**用途**：判断某个 coin 是否已有挂单、是否已有 TPSL、是否会和新的开仓动作冲突。

官方 Info endpoint 提供两种查询：

- `openOrders`
  - 更基础
- `frontendOpenOrders`
  - 前端友好字段更多，通常更适合产品逻辑和 AI 编排

*   **HTTP Request (`openOrders`)**:
```json
{
  "type": "openOrders",
  "user": "0xUserEvmAddressHere"
}
```

* **HTTP Request (`frontendOpenOrders`)**:
  
  ```json
  {
  "type": "frontendOpenOrders",
  "user": "0xUserEvmAddressHere"
  }
  ```

* **典型可用字段**:
  
  * `coin`
  * `oid`
  * `reduceOnly`
  * `isTrigger`
  * `triggerPx`
  * `limitPx`
  * `orderType`
  * `timestamp`

* **使用建议**:
  
  * 要做 AI 编排、TPSL 检查、避免重复挂单，优先用 `frontendOpenOrders`
  * 如果你只关心是否存在未成交订单，用 `openOrders` 也可以

---

### 3.5 获取用户杠杆与保证金模式 (MyDex Backend)

**用途**：查询某个币种当前的杠杆倍数，以及该币种当前使用的是全仓还是逐仓。这个接口不是 Hyperliquid 官方 `/info`，而是我方后端聚合后的只读接口。

* **HTTP Request**:
  
  ```json
  {
  "method": "GET",
  "url": "https://<your-backend-domain>/perps-api/info/get-user-margin-setting?walletAddress=0xUserEvmAddressHere&coin=BTC"
  }
  ```

* **Query 参数**:
  
  * `walletAddress`: 用户 EVM 地址
  * `coin`: 币种代码，例如 `BTC`、`ETH`

* **响应体（我方后端标准包裹）**:
  
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

* **字段说明**:
  
  * `isCross = true`：全仓模式（Cross）
  * `isCross = false`：逐仓模式（Isolated）
  * `leverage`：当前杠杆倍数

* **适用场景**:
  
  * AI Agent 在生成开仓卡片前，先读取当前币种的保证金模式和杠杆
  * 判断是否需要先执行“更新杠杆 / 切换全仓逐仓”
  * 回显用户当前仓位配置，而不是只展示计划中的配置

* **Node.js 最小示例**:
  
  ```typescript
  async function getUserMarginSetting(walletAddress: string, coin: string) {
  const url = new URL("https://<your-backend-domain>/perps-api/info/get-user-margin-setting");
  url.searchParams.set("walletAddress", walletAddress);
  url.searchParams.set("coin", coin);
  
  const response = await fetch(url.toString(), {
  method: "GET",
  headers: { "Accept": "application/json" },
  });
  if (!response.ok) throw new Error("Failed to fetch user margin setting");
  
  const result = await response.json();
  return result.data;
  }
  ```

> 注意：当前 app 内部也通过这个后端接口读取数据，对应实现位置：
> 
> - `core/network/src/main/java/io/mydex/network/source/CEXApiController.kt`
> - `core/network/src/main/java/io/mydex/network/model/dto/UserMarginSettingDTO.kt`

---

### 3.6 获取 K 线数据 (Candles)

**用途**：AI Agent 分析趋势，或前端展示图表。

* **HTTP Request**:
  
  ```json
  {
  "type": "candleSnapshot",
  "req": {
  "coin": "BTC",
  "interval": "1m", 
  "startTime": 1700000000000
  }
  }
  ```

* **参数说明**:
  
  * `coin`: 币种 (BTC/ETH)
  * `interval`: 官方支持：
    * `1m`, `3m`, `5m`, `15m`, `30m`
    * `1h`, `2h`, `4h`, `8h`, `12h`
    * `1d`, `3d`, `1w`, `1M`
  * `startTime`: 毫秒级时间戳

* **官方限制**:
  
  * 仅提供最近 `5000` 根 candles

* **SDK 调用 (Python)**:
  
  ```python
  import time
  ```

end_time = int(time.time() * 1000)
start_time = end_time - (24 * 60 * 60 * 1000) # 过去24小时

candles = info.candle_snapshot("BTC", "5m", start_time)
for candle in candles:
    # candle[0]=time, [1]=open, [2]=high, [3]=low, [4]=close, [5]=volume
    print(f"时间: {candle[0]}, 收盘价: {candle[4]}")

```
---

## 4. 前端/Node.js 同事的“最小可行”示例 (TypeScript)

如果你在用 Next.js 或 Node.js，这是一个简单的 Fetch 封装：

```typescript
const HYPERLIQUID_API = "https://api.hyperliquid.xyz/info";

async function fetchHyperliquidInfo(type: string, payload?: any) {
  const response = await fetch(HYPERLIQUID_API, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, ...payload }),
  });
  if (!response.ok) throw new Error("Network response was not ok");
  return response.json();
}

// 使用示例：获取用户保证金
async function getUserMargin(userAddress: string) {
  const data = await fetchHyperliquidInfo("clearinghouseState", { user: userAddress });
  return {
    marginSummary: data.marginSummary,
    withdrawable: data.withdrawable,
    assetPositions: data.assetPositions,
  };
}

// 使用示例：获取用户当前未成交订单
async function getFrontendOpenOrders(userAddress: string) {
  return fetchHyperliquidInfo("frontendOpenOrders", { user: userAddress });
}

// 使用示例：获取用户当前杠杆/保证金模式（通过我方后端）
async function getUserMarginSettingFromBackend(userAddress: string, coin: string) {
  const url = new URL("https://<your-backend-domain>/perps-api/info/get-user-margin-setting");
  url.searchParams.set("walletAddress", userAddress);
  url.searchParams.set("coin", coin);

  const response = await fetch(url.toString());
  if (!response.ok) throw new Error("Failed to fetch margin setting");

  const result = await response.json();
  return result.data;
}

// 使用示例：获取 BTC 价格
async function getBTCPrice() {
  const data = await fetchHyperliquidInfo("allMids");
  return data.BTC;
}
```

---

## 5. 给同事的避坑 Checklist ✅

1. **关于 Size (szi)**：API 返回的仓位大小 `szi` 是**有符号浮点数**。正数 = 多仓，负数 = 空仓。
2. **关于价格**：`allMids` 返回的价格是**标记价格 (Mark Price)**，不是最新成交价，用于计算强平。
3. **关于 Asset ID**：API 内部用数字 ID (BTC=0, ETH=1)，但 `meta` 和 `allMids` 通常用 Symbol (BTC)，**尽量用 Symbol 交互，不要硬编码 ID**。
4. **关于地址**：官方文档明确要求使用**实际账户地址**（master / subaccount 对应的真实地址），不要误传 agent wallet 地址。
5. **关于可用保证金**：如果你的目的是真正判断“还能不能开仓”，优先看 `withdrawable`，不要假设存在 `freeMargin` 字段。
6. **关于 open orders**：AI / 产品逻辑更推荐 `frontendOpenOrders`，因为它对 TPSL 和前端展示更友好。
7. **关于 Rate Limit**：这是公共 API，虽然没有严格公布限制，但不要在前端循环高频请求（< 1 req/sec 是更稳妥的做法）。
8. **关于 Decimal**：所有数值都是字符串或浮点数，**计算金额时务必注意精度**（USDC 是 6 位，但 API 返回的是 human-readable 的数字）。
9. **关于杠杆/保证金模式**：`clearinghouseState` 不能直接替代“当前币种杠杆设置”查询；如需拿到当前 `isCross` 和 `leverage`，请调用我方后端 `GET /perps-api/info/get-user-margin-setting`。

---
