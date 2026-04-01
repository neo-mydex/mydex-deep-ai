"""FastAPI SSE 对话接口

实现 neo-database-server 风格的流式对话接口。

端点: POST /api/chats/sessions/{session_id}/stream
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from typing import AsyncIterator, Any

from fastapi import FastAPI, Header
from sse_starlette.sse import EventSourceResponse
import json
import time

from src.agent.run import agent
from src.config import ChatContext


app = FastAPI(title="mydex-deep Chat API")


def text_of(token: Any) -> str:
    """从 AIMessage token 提取文本"""
    if token is None:
        return ""
    content = getattr(token, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            x if isinstance(x, str) else x.get("text", "")
            for x in content
            if isinstance(x, (str, dict))
        )
    return ""


def extract_token(chunk: Any) -> Any:
    """从 stream chunk 提取 token

    chunk 格式: ((), (AIMessageChunk,)) 或 ((), (ToolMessage,))
    """
    if isinstance(chunk, tuple) and len(chunk) == 2:
        second = chunk[1]
        # second 应该是 tuple 或 list
        if isinstance(second, (list, tuple)) and len(second) > 0:
            return second[0]
        # 也可能是直接的消息对象
        if hasattr(second, 'content') or hasattr(second, 'tool_calls'):
            return second
    # 直接返回
    return chunk


def make_sse_event(event_type: str, data: Any) -> str:
    """生成 SSE 事件 JSON 字符串（直接序列化，不双重编码）"""
    return json.dumps(
        {"type": event_type, "data": data, "ts": int(time.time() * 1000)},
        ensure_ascii=False,
    )


async def event_stream(
    session_id: str,
    message: str,
    raw_context: str,
    jwt: str,
) -> AsyncIterator[dict]:
    """生成 SSE 事件流"""
    # 1. session_start
    yield {
        "event": "session_start",
        "data": make_sse_event(
            "session_start",
            {"model": "mydex-deep", "auth_mode": "guest" if not jwt else "authenticated"},
        ),
    }

    # 2. 解析 context（必须是对象）
    if not isinstance(raw_context, dict):
        raise ValueError(f"context must be a dict, got {type(raw_context).__name__}: {raw_context}")
    context_dict = raw_context

    # 3. 构造 ChatContext（JWT 验证在这里完成）
    # context 对象的结构：{"jwt": "...", "other": {"evm_address": "..."}}
    # other 字段需要序列化
    try:
        other_json = json.dumps(context_dict.get("other", {}))
        chat_ctx = ChatContext(
            jwt=context_dict.get("jwt", jwt) or jwt,
            other=other_json,
        )
    except Exception:
        chat_ctx = ChatContext(jwt=jwt, other="{}")

    # 4. 准备消息
    messages = [{"role": "user", "content": message}]

    # 5. 配置
    config = {"configurable": {"thread_id": session_id}}

    # 6. 流式调用 agent
    try:
        async for chunk in agent.astream(
            {"messages": messages},
            config=config,
            context=chat_ctx,
            stream_mode="messages",
            subgraphs=True,
        ):
            token = extract_token(chunk)
            if token is None:
                continue

            # 处理 tool_call 开始（AIMessageChunk 有 tool_calls）
            tool_calls = [x for x in (getattr(token, "tool_calls", None) or []) if x.get("name")]
            if tool_calls:
                for tc in tool_calls:
                    yield {
                        "event": "tool_call_start",
                        "data": make_sse_event(
                            "tool_call_start",
                            {
                                "tool": tc["name"],
                                "args": tc.get("args", {}),
                                "callId": tc.get("id", ""),
                            },
                        ),
                    }
                continue

            # 处理 tool 响应（ToolMessage 有 name 属性）
            if hasattr(token, "name") and hasattr(token, "content") and getattr(token, "name", None):
                yield {
                    "event": "tool_call_complete",
                    "data": make_sse_event(
                        "tool_call_complete",
                        {
                            "tool": getattr(token, "name"),
                            "result": {"content": getattr(token, "content", "")},
                        },
                    ),
                }
                continue

            # 处理文本输出
            text = text_of(token)
            if text:
                yield {
                    "event": "llm_token",
                    "data": make_sse_event("llm_token", {"content": text}),
                }

    except Exception as e:
        import traceback
        traceback.print_exc()
        yield {"event": "error", "data": make_sse_event("error", {"message": repr(e)})}

    # 7. session_end
    yield {
        "event": "session_end",
        "data": make_sse_event("session_end", {"message_id": session_id}),
    }


@app.post("/api/chats/sessions/{session_id}/stream")
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
        "context": "{\"source\":\"/home\"}"
    }

    响应: text/event-stream

    事件类型:
    - session_start: 对话开始
    - llm_token: AI 输出片段
    - tool_call_start: 工具调用开始
    - tool_call_complete: 工具调用完成
    - session_end: 对话结束
    - error: 错误
    """
    message = body.get("message", "")
    # context 可以是 dict 对象（推荐）或 JSON 字符串（兼容）
    raw_context = body.get("context", {})
    jwt_from_header = authorization[7:] if (authorization and authorization.startswith("Bearer ")) else ""
    # 请求体的 jwt 优先，其次是 header
    jwt = body.get("jwt", jwt_from_header or "")

    return EventSourceResponse(
        event_stream(session_id, message, raw_context, jwt),
        media_type="text/event-stream",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
