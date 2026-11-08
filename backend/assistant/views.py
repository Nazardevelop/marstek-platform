"""AI assistant chat endpoint.

⚠️ MOCK: the real Anthropic tool-use loop (plan step 6) is not built yet. This endpoint already
speaks the final contract, so the FE can build the chat drawer against it today:

    POST /api/v1/assistant/chat/
        {messages: [{role, content}], context?: {route, device_id, extra}}
    200 text/event-stream:
        event: delta   data: {"text": "..."}         (repeated: streamed answer chunks)
        event: done    data: {"mock": true}          (end of answer)
    400 application/json: the usual error envelope (validation happens before streaming)
"""

import json
import time
from collections.abc import Iterator
from typing import Any

from django.conf import settings
from django.http import StreamingHttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from assistant.serializers import ChatRequestSerializer

MOCK_REPLY = (
    "The Marstek AI assistant is still in progress. "
    "Soon I'll answer questions about your battery, solar and energy history here."
)
CHUNK_DELAY_S = 0.03  # makes the mock *look* like streaming in the UI


class EventStreamRenderer(BaseRenderer):
    """Lets DRF accept `Accept: text/event-stream` (otherwise content negotiation returns 406)."""

    media_type = "text/event-stream"
    format = "sse"

    def render(
        self, data: Any, accepted_media_type: str | None = None, renderer_context: Any = None
    ) -> bytes:
        return json.dumps(data).encode()


def sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def mock_stream(delay: float) -> Iterator[str]:
    for word in MOCK_REPLY.split(" "):
        yield sse("delta", {"text": word + " "})
        if delay:
            time.sleep(delay)
    yield sse("done", {"mock": True})


class ChatView(APIView):
    renderer_classes = [JSONRenderer, EventStreamRenderer]

    def handle_exception(self, exc: Exception) -> Response:
        # Errors are always the JSON envelope, even when the client asked for an event stream.
        response = super().handle_exception(exc)
        self.request.accepted_renderer = JSONRenderer()
        self.request.accepted_media_type = JSONRenderer.media_type
        return response

    @extend_schema(
        request=ChatRequestSerializer,
        responses={
            (200, "text/event-stream"): OpenApiResponse(
                OpenApiTypes.STR,
                description="SSE: `delta` events {text}, then one `done` event. MOCK for now.",
            )
        },
    )
    def post(self, request: Request) -> StreamingHttpResponse:
        """Ask the assistant. ⚠️ Currently a mock that replies 'in progress'."""
        ChatRequestSerializer(data=request.data).is_valid(raise_exception=True)
        delay = 0.0 if settings.ASSISTANT_MOCK_INSTANT else CHUNK_DELAY_S
        response = StreamingHttpResponse(mock_stream(delay), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # stop nginx (later, in docker) buffering the stream
        response["X-Assistant-Mock"] = "true"
        return response
