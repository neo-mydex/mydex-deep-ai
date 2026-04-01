# Chatbot Server 调研报告

## 1. 概述

本次调研了 `neo-database-server` 的聊天机器人流式接口，以及底层 `lite-agent-demo` 的实现。

**架构关系**：

```
客户端 → neo-database-server → lite-agent-demo (实际AI处理)
```

`neo-database-server` 是一个 **Node.js/TypeScript** 项目（使用 pnpm workspaces），作为 API 网关代理，将请求转发给 `lite-agent-demo` 进行实际 AI 处理。

---

## 2. 核心技术栈

| 组件       | 技术                                       |
| -------- | ---------------------------------------- |
| Web 框架   | Express 5.2.1                            |
| 流式传输     | **SSE (Server-Sent Events)**，非 WebSocket |
| 认证       | Privy JWT                                |
| 数据库      | PostgreSQL (pg)                          |
| 缓存/限流    | Redis (ioredis)                          |
| 底层 Agent | lite-agent-demo (TypeScript)             |

---

## 3. 流式接口格式

### 3.1 端点

| 类型   | 端点                                                     | 认证                |
| ---- | ------------------------------------------------------ | ----------------- |
| 认证用户 | `POST /ai-api/chats/sessions/:sessionId/stream`        | JWT Bearer        |
| 游客   | `POST /ai-api/public-chats/sessions/:sessionId/stream` | X-Guest-Id / IP限流 |

### 3.2 请求格式

```json
{
  "message": "用户输入的问题",
  "context": "{\"source\":\"/home\"}"
}
```

请求头：

- `Authorization: Bearer <privy_jwt_token>`
- `Content-Type: application/json`

### 3.3 SSE 响应格式

**Headers**：

```
Content-Type: text/event-stream; charset=utf-8
Cache-Control: no-cache
Connection: keep-alive
```

**事件格式**：

```
data: {"type":"事件类型","data":"<内层对象序列化后的JSON string>","ts":时间戳}\n\n
```

注意：`data` 字段是**双重序列化**的字符串，客户端需要先 `JSON.parse(data)` 获取内层对象，再解析内层。

---

## 4. SSE 事件类型详解

| 事件类型                 | 含义            | 关键字段                             |
| -------------------- | ------------- | -------------------------------- |
| `session_start`      | 对话开始          | `model`                          |
| `llm_token`          | AI输出的文字片段     | `data.content`                   |
| `tool_call_start`    | 开始调用工具        | `data.tool`, `data.args`         |
| `tool_call_complete` | 工具调用完成        | `data.result.data.client_action` |
| `client_action`      | 前端指令（如打开交易窗口） | `data.client_action.type`        |
| `error`              | 错误            | `message`                        |
| `session_end`        | 对话结束          | `message_id`                     |

### 4.1 各事件数据结构

**session_start**：

```json
{
  "type": "session_start",
  "data": "{\"model\":\"lite-agent-demo\",\"auth_mode\":\"guest\"}",
  "ts": 1234567890000
}
```

**llm_token**：

```json
{
  "type": "llm_token",
  "data": "{\"content\":\"好的，\"}",
  "ts": 1234567890000
}
```

**tool_call_start**：

```json
{
  "type": "tool_call_start",
  "data": "{\"tool\":\"get_token_price\",\"content\":\"Executing...\",\"callId\":\"call_xxx\",\"args\":{...}}",
  "ts": 1234567890200
}
```

**tool_call_complete**：

```json
{
  "type": "tool_call_complete",
  "data": "{\"tool\":\"get_token_price\",\"callId\":\"call_xxx\",\"result\":{...}}",
  "ts": 1234567890600
}
```

**client_action**：

```json
{
  "type": "client_action",
  "data": "{\"client_action\":{\"type\":\"OPEN_TRADE_WINDOW\",\"params\":{...}}}",
  "ts": 1234567890650
}
```

**session_end**：

```json
{
  "type": "session_end",
  "data": "{\"message_id\":\"uuid-here\"}",
  "ts": 1234567890700
}
```

---

## 5. lite-agent-demo 架构

### 5.1 四层架构

| 层级  | 名称       | 文件              | 职责       |
| --- | -------- | --------------- | -------- |
| L1  | Engine   | `engine.ts`     | 编排、LLM循环 |
| L2  | Skills   | `skills/*.md`   | 业务流程定义   |
| L3  | Tools    | `tools/*.ts`    | 可暴露的能力   |
| L4  | Services | `services/*.ts` | 外部API客户端 |

### 5.2 核心处理流程

1. **意图分类** (`extractStructuredTurnSurfaceIntent`)
2. **结构化意图提取**：
   - `extractStructuredTransactionIntent` - swap/send/deposit
   - `extractStructuredMarketIntent` - 价格查询
   - `extractStructuredResearchIntent` - 研究请求
3. **直接执行** - 若意图完整，直接执行
4. **LLM降级** - 若无直接匹配，加载skills，组装context，调用LLM
5. **工具循环** - 最多5轮，防止无限循环

### 5.3 输入格式 (lite-agent-demo → /api/chat)

```typescript
{
  message: string;           // 用户消息
  history?: HistoryEntry[];   // 历史对话
  context?: Record<string, any>; // 上下文（钱包地址等）
  sessionId?: string;        // 会话ID
  apiToken?: string;        // 认证token
}
```

### 5.4 lite-agent-demo SSE 事件格式（简化版）

```typescript
// 直接发送给客户端的简化格式：
{"type": "text", "content": "Hello!"}
{"type": "tool_call_start", "data": {...}}
{"type": "tool_call_complete", "data": {...}}
{"type": "client_action", "data": {"client_action": {...}}}
{"type": "done"}
{"type": "error", "message": "..."}
```

**注意**：`neo-database-server` 会对这些事件进行**标准化**，添加外层包装（`type`, `data`双重序列化, `ts`）。

---

## 6. 标准化事件对照

| lite-agent-demo 原始事件                 | neo-database-server 标准化后                                            |
| ------------------------------------ | ------------------------------------------------------------------- |
| `{"type": "text", "content": "xxx"}` | `{"type":"llm_token","data":"{\"content\":\"xxx\"}","ts":...}`      |
| `{"type": "tool_call_start", ...}`   | `{"type":"tool_call_start","data":"{...}","ts":...}`                |
| `{"type": "client_action", ...}`     | `{"type":"client_action","data":"{...}","ts":...}`                  |
| `{"type": "done"}`                   | `{"type":"session_end","data":"{\"message_id\":\"...\"}","ts":...}` |

---

## 7. 内存/记忆系统

### 7.1 短期记忆 (lite-agent-demo)

- `ChatHistoryManager`: 内存 Map
- 每个 session 最多 50 条，最大 1000 个 session
- LRU 淘汰

### 7.2 长期记忆 (lite-agent-demo)

- `LiteMemoryManager`: 向量搜索
- 支持 RAG（关键词触发："之前"、"上次"、"记得"、"偏好"）

---

## 8. 游客限流机制

当触发游客限流时：

- 返回 `HTTP 200` + SSE（不是 429 错误）
- 通过 `auth_guard` 事件返回 `PLEASE_LOG_IN` client_action

---

## 9. 关键文件路径

### neo-database-server

| 文件                                                   | 用途          |
| ---------------------------------------------------- | ----------- |
| `packages/server/src/main.ts`                        | Express 入口  |
| `packages/server/src/routes/chat-stream-handlers.ts` | **SSE核心逻辑** |
| `packages/server/src/routes/chats.ts`                | 会话CRUD      |
| `packages/server/src/middleware/auth.ts`             | JWT认证       |
| `packages/server/src/middleware/guest-chat.ts`       | 游客限流        |

### lite-agent-demo

| 文件                               | 用途                        |
| -------------------------------- | ------------------------- |
| `src/demo/server.ts`             | HTTP入口 (`POST /api/chat`) |
| `src/agent/engine.ts`            | 核心Agent引擎                 |
| `src/agent/context-assembler.ts` | LLM消息组装                   |
| `src/agent/history.ts`           | 短期记忆                      |
| `src/memory/lite-manager.ts`     | 长期记忆                      |
| `src/demo/public/index.html`     | Web UI示例                  |

---

## 10. 如果要学习/复用

### 10.1 直接使用 SSE 流式接口

请求 `POST /ai-api/chats/sessions/:sessionId/stream`（需JWT），即可获得流式响应。

### 10.2 自己实现类似架构

需要实现：

1. **SSE 端点**：使用 `text/event-stream`，`res.write()` 发送事件
2. **双重序列化**：外层 `{type, data, ts}`，内层 data 是 JSON 字符串
3. **事件标准化**：将内部简化格式转换为标准格式
4. **代理转发**：可选，像 neo-database-server 一样代理到上游 Agent

### 10.3 核心差异

| 项目                  | 流式格式        | 语言         | 架构      |
| ------------------- | ----------- | ---------- | ------- |
| neo-database-server | SSE + 双重序列化 | TypeScript | API网关   |
| lite-agent-demo     | SSE + 简化格式  | TypeScript | 实际AI处理  |
| mydex-deep          | **待定**      | Python     | Agent框架 |

---

## 11. 总结

neo-database-server 的聊天接口采用 **SSE (Server-Sent Events)** 实现流式输出，事件格式采用**双重序列化**（内层 data 是 JSON 字符串）。事件类型包括 `session_start`、`llm_token`、`tool_call_start`、`tool_call_complete`、`client_action`、`session_end`。

lite-agent-demo 是实际处理 AI 对话的核心，使用四层架构（Engine → Skills → Tools → Services），支持意图识别、直接执行、LLM 降级、工具循环等能力。

如果 mydex-deep 要实现类似格式，需要：

1. 统一事件格式（建议直接采用 lite-agent-demo 的简化格式）
2. 如需 API 网关层，可参考 neo-database-server 的标准化封装
3. SSE 实现参考 `chat-stream-handlers.ts`
