# mydex-deep 替代 neo-database-server 对话接口方案

## 1. 现状分析

### 1.1 我们的能力 (mydex-deep)

| 能力 | 状态 | 说明 |
|------|------|------|
| Agent 运行时 | ✅ 已有 | `deepagents` 基于 LangGraph |
| 流式输出 | ⚠️ 实验性 | `play/hello_stream.py` 已实现，生产代码未用 |
| 工具系统 | ✅ 已有 | `perp_*`, `coin_*`, `jwt_*`, `wallet_*` 等 14+ tools |
| Skill 系统 | ✅ 已有 | `src/skills/*.md` 格式 |
| JWT 解析 | ✅ 已有 | `ChatContext` + `decode_jwt.py` |
| 会话记忆 | ⚠️ 实验性 | `MemorySaver` checkpoint，但未接入生产 |

### 1.2 neo-database-server 提供的功能

| 功能 | 说明 |
|------|------|
| SSE 流式响应 | `text/event-stream` 格式 |
| 事件封装 | `{"type":"xxx","data":"<JSON>","ts":...}` |
| JWT 认证 | Privy JWT 验证 |
| 游客模式 | 限流 + IP 指纹 |
| 会话管理 | 创建/获取/删除会话 |
| 消息存储 | 持久化对话记录 |
| 代理转发 | 转发到 lite-agent-demo |
| client_action | `OPEN_TRADE_WINDOW`, `SHOW_DEPOSIT_PROMPT` 等前端指令 |

---

## 2. 核心差距

| 差距 | 当前 mydex-deep | 需要达到 |
|------|----------------|----------|
| SSE 接口 | 无 | FastAPI 实现 |
| 事件格式 | 无 | `{"type","data","ts"}` 封装 |
| tool_call 拦截 | middleware 钩子已有，但未用于 SSE | 需要 `wrap_tool_call` 拦截并发送 SSE 事件 |
| client_action | 无 | 需要在 tool 返回特定结果时触发 |
| 会话持久化 | 无 | 需要存储 messages 到数据库 |
| 游客限流 | 无 | 需要 Redis 限流 |

---

## 3. 实现方案

### 3.1 整体架构

```
客户端
  │
  ▼
┌─────────────────────────────────────┐
│  FastAPI SSE 端点                    │
│  POST /chats/sessions/{id}/stream   │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  SSE 事件转换层                      │
│  - session_start 事件               │
│  - llm_token 事件 (流式)            │
│  - tool_call_start 事件             │
│  - tool_call_complete 事件         │
│  - client_action 事件               │
│  - session_end 事件                 │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  deepagents Agent                   │
│  - stream_mode="messages"          │
│  - @wrap_tool_call 拦截工具         │
│  - runtime.stream_writer 发事件    │
└─────────────────────────────────────┘
```

### 3.2 完整的请求处理流程

```
客户端请求
  │
  ├─ Header: Authorization: Bearer <JWT>
  └─ Body: {"message": "...", "context": "{\"source\":\"/home\"}"}
              │
              ▼
┌─────────────────────────────────────┐
│  1. JWT 提取 & 验证                  │
│     - 从 Header 提取 Bearer token   │
│     - ChatContext._resolve_identity │
│     - 设置 user_id, is_authenticated │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  2. context 字段解析                  │
│     - Body.context 是 JSON 字符串    │
│     - 需要 parse 后传入 ChatContext  │
│     - 包含: source, pathname 等      │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  3. 构造 ChatContext                 │
│     ChatContext(                     │
│         jwt=提取的JWT,               │
│         context=解析后的dict转字符串  │
│     )                                │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  4. 调用 agent                       │
│     agent.invoke(                    │
│         {"messages": [...]},         │
│         context=ChatContext(...)     │
│     )                                │
└─────────────────────────────────────┘
```

### 3.3 FastAPI SSE 端点实现（完整版）

**新建文件**: `src/api/chat_stream.py`

```python
from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import time
from typing import AsyncIterator

from src.agent.run import agent, MemSaver
from src.config import ChatContext
import src.config as conf

router = APIRouter(prefix="/api", tags=["chat"])


def extract_token(chunk) -> Any:
    """从 stream chunk 中提取 token"""
    if isinstance(chunk, tuple) and len(chunk) == 2:
        return chunk[1][0]
    if isinstance(chunk, dict):
        data = chunk.get("data")
        if isinstance(data, tuple):
            return data[0]
    return None


def text_of(token) -> str:
    """从 token 提取文本内容"""
    if token is None:
        return ""
    # AIMessage 有 content 属性
    content = getattr(token, "content", None)
    if isinstance(content, str):
        return content
    # 也可能是 list
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            return first.get("text", "")
    return ""


async def event_stream(
    session_id: str,
    message: str,
    raw_context: str,  # JSON 字符串
    jwt: str = "",
) -> AsyncIterator[dict]:
    """生成 SSE 事件流"""

    # 1. session_start
    yield {
        "event": "session_start",
        "data": json.dumps({
            "type": "session_start",
            "data": json.dumps({
                "model": "mydex-deep",
                "auth_mode": "guest" if not jwt else "authenticated"
            }),
            "ts": int(time.time() * 1000)
        })
    }

    # 2. 解析 context 字段（JSON 字符串）
    try:
        context_dict = json.loads(raw_context) if raw_context else {}
    except json.JSONDecodeError:
        context_dict = {"raw": raw_context}

    # 3. 构造 ChatContext（这里会验证 JWT，设置 user_id）
    try:
        chat_context = ChatContext(
            jwt=jwt,
            context=json.dumps(context_dict),  # 转回字符串
        )
    except Exception as e:
        # JWT 解析失败，但继续以游客模式运行
        chat_context = ChatContext(
            jwt="",
            context=json.dumps(context_dict),
        )

    # 4. 准备消息
    messages = [{"role": "user", "content": message}]

    # 5. 配置 checkpoint（会话记忆）
    config = {"configurable": {"thread_id": session_id}}
    if MemSaver:
        config["configurable"]["checkpoint"] = MemSaver()

    # 6. 流式调用 agent
    try:
        async for chunk in agent.astream(
            {"messages": messages},
            config=config,
            stream_mode="messages",
            subgraphs=True,
        ):
            token = extract_token(chunk)
            if token is None:
                continue

            # 处理 tool call 开始
            tool_calls = [x for x in (getattr(token, "tool_calls", None) or []) if x.get("name")]
            if tool_calls:
                for tc in tool_calls:
                    yield {
                        "event": "tool_call_start",
                        "data": json.dumps({
                            "type": "tool_call_start",
                            "data": json.dumps({
                                "tool": tc["name"],
                                "args": tc.get("args", {}),
                                "callId": tc.get("id", "")
                            }),
                            "ts": int(time.time() * 1000)
                        })
                    }
                continue

            # 处理 tool 响应（tool message）
            if getattr(token, "type", "") == "tool":
                tool_name = getattr(token, "name", "unknown")
                tool_content = getattr(token, "content", "")
                yield {
                    "event": "tool_call_complete",
                    "data": json.dumps({
                        "type": "tool_call_complete",
                        "data": json.dumps({
                            "tool": tool_name,
                            "result": {"content": tool_content}
                        }),
                        "ts": int(time.time() * 1000)
                    })
                }
                continue

            # 处理文本输出
            text = text_of(token)
            if text:
                yield {
                    "event": "llm_token",
                    "data": json.dumps({
                        "type": "llm_token",
                        "data": json.dumps({"content": text}),
                        "ts": int(time.time() * 1000)
                    })
                }

    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({
                "type": "error",
                "data": json.dumps({"message": str(e)}),
                "ts": int(time.time() * 1000)
            })
        }

    # 7. session_end
    yield {
        "event": "session_end",
        "data": json.dumps({
            "type": "session_end",
            "data": json.dumps({"message_id": session_id}),
            "ts": int(time.time() * 1000)
        })
    }


@router.post("/chats/sessions/{session_id}/stream")
async def chat_stream(
    session_id: str,
    body: dict,
    authorization: str = Header(None),
):
    """
    SSE 流式对话接口

    请求:
    {
        "message": "用户输入",
        "context": "{\"source\":\"/home\",\"pathname\":\"/trade\"}"
    }

    响应: text/event-stream
    """
    message = body.get("message", "")
    # context 是 JSON 字符串
    raw_context = body.get("context", "")

    # 1. 从 Header 提取 JWT
    jwt = ""
    if authorization and authorization.startswith("Bearer "):
        jwt = authorization[7:]

    # 2. 返回 SSE 流
    return EventSourceResponse(
        event_stream(session_id, message, raw_context, jwt),
        media_type="text/event-stream"
    )
```

### 3.4 ChatContext 的 JWT 验证流程

`ChatContext` 在初始化时会自动：

```python
@model_validator(mode="after")
def _resolve_identity(self) -> "ChatContext":
    self.user_id = "guest"
    self.is_authenticated = False

    jwt = self.jwt.strip()
    if not jwt:
        return self  # 游客模式

    # 调用 get_userid_and_expired_time 验证 JWT
    decoded = get_userid_and_expired_time(jwt=jwt)
    if decoded["user_id"] and not decoded["is_expired"]:
        self.user_id = decoded["user_id"]
        self.is_authenticated = True

    return self
```

这意味着：
- **有有效 JWT** → `user_id` 会被设置，`is_authenticated=True`
- **无 JWT 或失效** → `user_id="guest"`，`is_authenticated=False`
- **JWT 解析错误** → `jwt_error` 会被设置，但不影响运行

### 3.5 user_id 如何传递给工具

deepagents 的 `context_schema` 会将 `ChatContext` 注入到 agent 运行时，供工具使用：

```
ChatContext.user_id → agent.runtime.context.user_id → wallet_get_assets(jwt)
```

工具可以通过 `runtime.context.user_id` 访问当前用户身份。

**示例 - wallet 工具**：
```python
@tool
def wallet_get_assets(jwt: str) -> dict:
    """查询用户钱包资产，需要 JWT"""
    # jwt 由 agent 从 context 注入
    user_id = decode_jwt(jwt).get("user_id")
    # 调用钱包 API ...
```

**关键点**：工具调用时，`jwt` 参数由 agent 根据 `context_schema` 自动填充（从 `ChatContext.jwt`），开发者不需要手动传递。

### 3.6 请求示例完整流程

**输入请求**：
```
POST /api/chats/sessions/abc123/stream
Authorization: Bearer eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIs...

{
    "message": "查一下我的仓位",
    "context": "{\"source\":\"/home\",\"pathname\":\"/trade\"}"
}
```

**处理流程**：
```
1. 提取 JWT: eyJhbGciOiJFUzI1NiIs...
2. 解析 context: {"source": "/home", "pathname": "/trade"}
3. 构造 ChatContext(jwt="eyJ...", context='{"source":"...','}')
   → user_id = "did:privy:cmmsl6t2402..."
   → is_authenticated = True
4. agent.invoke(context=ChatContext)
5. Agent 调用 wallet 工具时，自动注入 jwt
6. 流式返回 SSE 事件
```

### 3.3 deepagents Middleware 钩子方案

deepagents 支持 `AgentMiddleware` 钩子，我们可以利用这些钩子来发送 SSE 事件。

**关键钩子**：

| 钩子 | 用途 |
|------|------|
| `@before_agent` | 发送 `session_start` |
| `@wrap_tool_call` | 拦截 tool_call_start / tool_call_complete |
| `@after_model` | 发送 `llm_token` |
| `@after_agent` | 发送 `session_end` |

**示例 middleware** (`src/middleware/sse_events.py`)：

```python
from langchain.agents.middleware import before_agent, after_model, wrap_tool_call, AgentState
from langchain.agents.runtime import Runtime
import json
import time

# 全局 event_queue，用于传递事件给 SSE 层
event_queue: asyncio.Queue = None

def set_event_queue(q: asyncio.Queue):
    global event_queue
    event_queue = q

async def emit(event_type: str, data: dict):
    if event_queue:
        await event_queue.put({
            "type": event_type,
            "data": json.dumps(data),
            "ts": int(time.time() * 1000)
        })

@before_agent
async def on_session_start(state: AgentState, runtime: Runtime) -> None:
    await emit("session_start", {"model": "mydex-deep"})

@wrap_tool_call
async def on_tool_call(request, handler):
    # tool_call_start
    await emit("tool_call_start", {
        "tool": request.tool_call.get("name"),
        "args": request.tool_call.get("args", {}),
        "callId": request.tool_call.get("id", "")
    })

    # 执行工具
    result = await handler(request)

    # tool_call_complete
    await emit("tool_call_complete", {
        "tool": request.tool_call.get("name"),
        "result": result,
        "callId": request.tool_call.get("id", "")
    })

    return result

@after_model
async def on_llm_response(state: AgentState, runtime: Runtime) -> None:
    last_message = state["messages"][-1]
    # 发送 token...
```

### 3.4 client_action 触发机制

neo-database-server 通过 `client_action` 事件让前端执行特定操作（如打开交易窗口）。

**在我们的架构中**，可以在 tool 中返回特定结构来触发：

```python
# 在 tool 返回结果中包含 client_action
def perp_open_position(...):
    # ... 逻辑
    if should_trigger_ui_action:
        return {
            "ok": True,
            "client_action": {
                "type": "OPEN_TRADE_WINDOW",
                "params": {
                    "symbol": "ETH",
                    "side": "LONG",
                    "size": 1.0
                }
            }
        }
```

然后在 `after_agent` 或自定义 hook 中检测并发送 `client_action` 事件。

---

## 4. 实现步骤

### 阶段一：基础 SSE 接口

1. **新建 `src/api/chat_stream.py`**
   - FastAPI 路由 + SSE EventSourceResponse
   - **JWT 提取**：从 `Authorization: Bearer <token>` 解析
   - **context 解析**：Body.context 是 JSON 字符串，需要 `json.loads()`
   - **ChatContext 构造**：传给 agent
   - 简化版流式输出（llm_token）

2. **修改 `src/agent/run.py`**
   - 确认 `agent` 支持 `astream()`
   - 添加 MemorySaver 导出

3. **测试 SSE 流式输出**

### 阶段二：tool_call 事件拦截

4. **实现 SSE middleware** (`src/middleware/sse_events.py`)
   - `@wrap_tool_call` 拦截工具调用
   - 通过 asyncio.Queue 传递事件

5. **改造 agent 创建** (`src/agent/run.py`)
   - 注册 middleware

### 阶段三：完整功能

6. **会话管理**
   - 接入数据库存储 messages
   - 支持 session 历史

7. **client_action 机制**
   - 定义 client_action 类型
   - 在 tool 返回中支持
   - middleware 转发为 SSE 事件

8. **游客限流**（如需要）
   - Redis 限流

---

## 5. 关键文件修改

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/api/chat_stream.py` | 新建 | SSE 端点 |
| `src/middleware/sse_events.py` | 新建 | SSE 事件 middleware |
| `src/agent/run.py` | 修改 | 导出异步 agent |
| `src/config/llms.py` | 可能修改 | 添加异步配置 |
| `src/main.py` | 新建 | FastAPI 入口 |

---

## 6. 简化版参考实现

`play/hello_stream.py` 已经展示了核心流式逻辑：

```python
for chunk in agent.stream(
    {"messages": messages},
    config={"configurable": {"thread_id": thread_id}},
    stream_mode="messages",
    subgraphs=True
):
    token = chunk[1][0]
    if token is None:
        continue
    # 处理 tool_call
    tool_calls = [x for x in (getattr(token, "tool_calls", None) or []) if x.get("name")]
    if tool_calls:
        print(f"\n[DEBUG] tool_call {json.dumps(tool_calls)}")
    # 处理文本
    text = text_of(token)
    if text:
        print(text, end="", flush=True)
```

这个模式可以直接套用到 FastAPI SSE 中。

---

## 7. 结论

**我们完全可以替代 neo-database-server 的对话接口功能**。

核心优势：
- deepagents 已有完整的 Agent 能力（工具、Skill、记忆）
- LangGraph 流式模式成熟（`stream_mode="messages"`）
- JWT 解析能力已有（ChatContext）
- Middleware 钩子支持 tool_call 拦截

需要实现：
1. FastAPI SSE 端点（新建）
2. 事件封装层（将 token/tool 转换为 SSE 事件）
3. 会话持久化（接入数据库）
4. 可选：游客限流

**推荐做法**：先用 `play/hello_stream.py` 的模式实现基础 SSE，确认流式输出正常后，再逐步添加 tool_call 拦截、middleware 集成等高级功能。
