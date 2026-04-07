"""测试 fastapi_server 的 SSE 流式输出"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from src.agent.fastapi_server import (
    app,
    text_of,
    extract_token,
    make_sse_event,
)
from src.agent.run import agent


class TestTextOf:
    """测试 text_of 函数"""

    def test_text_of_none(self):
        assert text_of(None) == ""

    def test_text_of_string_content(self):
        """字符串 content"""
        mock_token = MagicMock()
        mock_token.content = "你好"
        assert text_of(mock_token) == "你好"

    def test_text_of_list_content(self):
        """列表 content"""
        mock_token = MagicMock()
        mock_token.content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": " World"},
        ]
        assert text_of(mock_token) == "Hello World"


class TestExtractToken:
    """测试 extract_token 函数"""

    def test_extract_token_none(self):
        assert extract_token(None) is None

    def test_extract_token_tuple_format(self):
        """hello_stream.py 格式: (ns, [token])"""
        mock_token = MagicMock()
        mock_token.content = "test"
        chunk = ("messages", [mock_token])
        result = extract_token(chunk)
        assert result is mock_token

    def test_extract_token_dict_format(self):
        """dict 格式 - 当前实现不处理这个，返回原值"""
        mock_token = MagicMock()
        mock_token.content = "test"
        chunk = {"data": mock_token}
        result = extract_token(chunk)
        # 当前实现对 dict 格式直接返回
        assert result == chunk


class TestMakeSseEvent:
    """测试 make_sse_event 函数"""

    def test_make_sse_event_simple(self):
        result = make_sse_event("llm_token", {"content": "你好"})
        parsed = json.loads(result)
        assert parsed["type"] == "llm_token"
        assert parsed["data"]["content"] == "你好"
        assert "ts" in parsed

    def test_make_sse_event_chinese(self):
        """测试中文不转义"""
        result = make_sse_event("llm_token", {"content": "你好"})
        # ensure_ascii=False 应该是直接输出中文
        assert "你好" in result
        # 而不是 \u4f60\u597d


class TestAgentStreaming:
    """测试 agent 流式调用"""

    def test_agent_has_astream(self):
        """确认 agent 有 astream 方法"""
        assert hasattr(agent, "astream")

    def test_agent_streaming_simple(self):
        """简单测试 agent.stream 能正常工作"""
        messages = [{"role": "user", "content": "说一个简短的笑"}]

        tokens = []
        tool_calls = []

        for chunk in agent.stream(
            {"messages": messages},
            config={"configurable": {"thread_id": "test-thread"}},
            stream_mode="messages",
            subgraphs=True,
        ):
            token = extract_token(chunk)
            if token is None:
                continue

            # 检查 tool call
            tcs = [x for x in (getattr(token, "tool_calls", None) or []) if x.get("name")]
            if tcs:
                tool_calls.extend(tcs)
                continue

            text = text_of(token)
            if text:
                tokens.append(text)

        print(f"Tokens: {tokens}")
        print(f"Tool calls: {tool_calls}")

        # 应该有一些文本输出
        assert len(tokens) > 0, "应该有文本输出"

    def test_agent_streaming_with_btc_price(self):
        """测试查 BTC 价格"""
        messages = [{"role": "user", "content": "查一下BTC价格"}]

        tokens = []
        tool_calls = []

        for chunk in agent.stream(
            {"messages": messages},
            config={"configurable": {"thread_id": "test-btc-price"}},
            stream_mode="messages",
            subgraphs=True,
        ):
            token = extract_token(chunk)
            if token is None:
                continue

            # 检查 tool call
            tcs = [x for x in (getattr(token, "tool_calls", None) or []) if x.get("name")]
            if tcs:
                tool_calls.extend(tcs)
                continue

            # tool message
            if getattr(token, "type", "") == "tool":
                print(f"[Tool result] {getattr(token, 'name', 'unknown')}: {getattr(token, 'content', '')}")
                continue

            text = text_of(token)
            if text:
                tokens.append(text)

        print(f"\nFinal tokens: {''.join(tokens)}")
        print(f"Tool calls: {[tc['name'] for tc in tool_calls]}")

        # 应该有 tool call
        assert len(tool_calls) > 0, f"应该有 tool call，实际: {tool_calls}"
        tool_names = [tc["name"] for tc in tool_calls]
        assert "perp_get_market_price" in tool_names or "coin_get_price" in tool_names, \
            f"应该是查价格的 tool，实际: {tool_names}"


class TestFastAPIEndpoint:
    """测试 FastAPI 端点"""

    def setup_method(self):
        self.client = TestClient(app)

    def test_health_check(self):
        """测试服务能响应"""
        # 发送一个简单的请求
        response = self.client.post(
            "/api/chats/sessions/test/stream",
            json={"message": "你好", "context": "{}"},
        )
        assert response.status_code == 200

    def test_sse_response_format(self):
        """测试 SSE 响应格式"""
        with self.client.stream(
            "POST",
            "/api/chats/sessions/test/stream",
            json={"message": "说个 hi", "context": "{}"},
        ) as response:
            assert response.status_code == 200

            content = ""
            for line in response.iter_lines():
                if line:
                    content += line + "\n"
                if "session_end" in content:
                    break

            print(f"\nSSE Response:\n{content}")

            # 应该包含 session_start
            assert "session_start" in content
            # 应该包含 llm_token
            assert "llm_token" in content or "hi" in content
            # 应该包含 session_end
            assert "session_end" in content

    def test_btc_price_request(self):
        """测试查 BTC 价格"""
        with self.client.stream(
            "POST",
            "/api/chats/sessions/test-btc/stream",
            json={"message": "查一下BTC价格", "context": "{}"},
        ) as response:
            assert response.status_code == 200

            content = ""
            for line in response.iter_lines():
                if line:
                    content += line + "\n"
                if "session_end" in content:
                    break

            print(f"\nBTC Response:\n{content}")

            # 应该有 tool_call_start
            assert "tool_call_start" in content or "perp_get_market_price" in content or "coin_get_price" in content, \
                f"应该有 tool_call，实际响应:\n{content}"
