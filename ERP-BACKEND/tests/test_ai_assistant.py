"""
Unit tests for the AI assistant module (app/ai/assistant.py).
"""
import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai.assistant import (
    AIAgentActor,
    ChatMessage,
    ChatResponse,
    query_ollama,
    build_router,
)
from app.api_boundary.boundary import BoundaryError
from app.auth import get_current_user
from app.database import get_db


class TestAIAgentActor:
    """Tests for the AIAgentActor dataclass."""

    def test_actor_kind_defaults_to_ai_agent(self):
        actor = AIAgentActor(id=5)
        assert actor.id == 5
        assert actor.actor_kind == "ai_agent"

    def test_actor_id_can_be_none(self):
        actor = AIAgentActor(id=None)
        assert actor.id is None

    def test_actor_kind_can_be_overridden(self):
        actor = AIAgentActor(id=1, actor_kind="custom_kind")
        assert actor.actor_kind == "custom_kind"


class TestChatModels:
    """Tests for the ChatMessage / ChatResponse pydantic models."""

    def test_chat_message_context_defaults_to_none(self):
        msg = ChatMessage(message="hello")
        assert msg.message == "hello"
        assert msg.context is None

    def test_chat_message_accepts_context(self):
        msg = ChatMessage(message="hi", context="extra context")
        assert msg.context == "extra context"

    def test_chat_response_sources_defaults_to_none(self):
        resp = ChatResponse(response="ok")
        assert resp.response == "ok"
        assert resp.sources is None

    def test_chat_response_accepts_sources_list(self):
        resp = ChatResponse(response="ok", sources=["finance.dashboard"])
        assert resp.sources == ["finance.dashboard"]


class TestQueryOllama:
    """Tests for the query_ollama helper coroutine."""

    def _mock_async_client(self, json_payload):
        mock_response = MagicMock()
        mock_response.json.return_value = json_payload
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        return mock_client

    @pytest.mark.asyncio
    async def test_uses_default_model_and_configured_url(self):
        mock_client = self._mock_async_client({"response": "hello world"})

        with patch("app.ai.assistant.httpx.AsyncClient", return_value=mock_client):
            with patch("app.ai.assistant.settings") as mock_settings:
                mock_settings.OLLAMA_MODEL = "llama3.1"
                mock_settings.OLLAMA_URL = "http://ollama:11434"
                result = await query_ollama("say hi")

        assert result == "hello world"
        mock_client.post.assert_called_once_with(
            "http://ollama:11434/api/generate",
            json={"model": "llama3.1", "prompt": "say hi", "stream": False},
        )

    @pytest.mark.asyncio
    async def test_custom_model_overrides_default_setting(self):
        mock_client = self._mock_async_client({"response": "custom answer"})

        with patch("app.ai.assistant.httpx.AsyncClient", return_value=mock_client):
            result = await query_ollama("prompt text", model="mistral")

        assert result == "custom answer"
        _, kwargs = mock_client.post.call_args
        assert kwargs["json"]["model"] == "mistral"
        assert kwargs["json"]["prompt"] == "prompt text"
        assert kwargs["json"]["stream"] is False

    @pytest.mark.asyncio
    async def test_missing_response_field_returns_empty_string(self):
        mock_client = self._mock_async_client({})

        with patch("app.ai.assistant.httpx.AsyncClient", return_value=mock_client):
            result = await query_ollama("prompt")

        assert result == ""

    @pytest.mark.asyncio
    async def test_network_error_propagates_and_is_not_swallowed(self):
        """Negative case: query_ollama has no try/except around the HTTP call,
        so a connection failure must propagate to the caller instead of being
        silently converted into an empty/default response."""
        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.ai.assistant.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.ConnectError):
                await query_ollama("prompt")


class TestChatEndpoint:
    """Integration-style tests for the /chat endpoint built by build_router()."""

    def _make_app(self, current_user=None):
        app = FastAPI()
        app.include_router(build_router())

        def override_get_db():
            yield MagicMock()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: current_user or MagicMock(id=1)
        return app

    def test_chat_returns_ollama_response_and_finance_source_when_available(self):
        user = MagicMock(id=42)
        app = self._make_app(current_user=user)

        with patch("app.ai.assistant.boundary.query", return_value={"total_invoices": 3}) as mock_query, \
             patch("app.ai.assistant.query_ollama", new=AsyncMock(return_value="AI answer")):
            client = TestClient(app)
            response = client.post("/chat", json={"message": "How is finance?"})

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "AI answer"
        assert data["sources"] == ["finance.dashboard"]

        mock_query.assert_called_once()
        _, kwargs = mock_query.call_args
        assert kwargs["name"] == "finance.dashboard"
        assert kwargs["actor"].id == 42
        assert kwargs["actor"].actor_kind == "ai_agent"

    def test_chat_falls_back_gracefully_when_boundary_raises(self):
        app = self._make_app(current_user=MagicMock(id=7))

        with patch("app.ai.assistant.boundary.query", side_effect=BoundaryError("denied")), \
             patch("app.ai.assistant.query_ollama", new=AsyncMock(return_value="fallback answer")):
            client = TestClient(app)
            response = client.post("/chat", json={"message": "hi"})

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "fallback answer"
        assert data["sources"] == []

    def test_chat_prompt_includes_finance_summary_and_user_message(self):
        app = self._make_app(current_user=MagicMock(id=1))

        with patch("app.ai.assistant.boundary.query", return_value={"total_invoices": 9}), \
             patch("app.ai.assistant.query_ollama", new=AsyncMock(return_value="ok")) as mock_ollama:
            client = TestClient(app)
            client.post("/chat", json={"message": "What is my revenue?"})

        prompt_arg = mock_ollama.call_args[0][0]
        assert "What is my revenue?" in prompt_arg
        assert "total_invoices" in prompt_arg

    def test_chat_requires_message_field(self):
        app = self._make_app()

        client = TestClient(app)
        response = client.post("/chat", json={})

        assert response.status_code == 422

    def test_chat_sources_empty_when_finance_summary_is_none_without_error(self):
        app = self._make_app(current_user=MagicMock(id=1))

        with patch("app.ai.assistant.boundary.query", return_value=None), \
             patch("app.ai.assistant.query_ollama", new=AsyncMock(return_value="answer")):
            client = TestClient(app)
            response = client.post("/chat", json={"message": "hi"})

        assert response.status_code == 200
        assert response.json()["sources"] == []

    def test_chat_propagates_500_when_ollama_backend_is_unreachable(self):
        """Negative case: the chat endpoint has no error handling around
        query_ollama, so a downstream failure should surface as a server
        error rather than a fabricated 200 response."""
        app = self._make_app(current_user=MagicMock(id=1))

        with patch("app.ai.assistant.boundary.query", return_value=None), \
             patch("app.ai.assistant.query_ollama", new=AsyncMock(side_effect=httpx.ConnectError("down"))):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/chat", json={"message": "hi"})

        assert response.status_code == 500


class TestMainAppWiring:
    """Regression test verifying app/main.py mounts the AI assistant router."""

    def test_ai_chat_route_is_mounted_under_expected_prefix(self):
        from app.main import app as main_app

        paths = {route.path for route in main_app.routes}
        assert "/api/v1/ai/chat" in paths