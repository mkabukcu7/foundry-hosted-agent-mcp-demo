"""Native A2A 1.0 wire transport with SDK compatibility DTOs inside the app."""

from types import SimpleNamespace
from urllib.parse import urlsplit
from uuid import uuid4

from a2a.client import A2ACardResolver as NativeCardResolver
from a2a.client.transports.jsonrpc import JsonRpcTransport
from a2a.compat.v0_3.conversions import to_compat_message, to_core_agent_card, to_core_message, to_core_send_message_request
from a2a.compat.v0_3.types import AgentCapabilities, AgentCard, AgentSkill, Artifact, DataPart, FilePart, FileWithBytes, Message, MessageSendParams, Part, Role, SendMessageRequest, TextPart
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler as NativeRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.utils.errors import TaskNotCancelableError
from starlette.applications import Starlette


class A2ACardResolver:
    def __init__(self, http_client, url):
        self.resolver = NativeCardResolver(http_client, url)
        self.card_path = "agentCard/v1.0" if (urlsplit(url).hostname or "").endswith(".services.ai.azure.com") else None

    async def get_agent_card(self):
        card = await self.resolver.get_agent_card(relative_card_path=self.card_path)
        interfaces = [interface for interface in card.supported_interfaces
                      if interface.protocol_binding == "JSONRPC" and interface.protocol_version in {"1.0", "1.0.0"}]
        if not interfaces:
            raise RuntimeError("Specialist must advertise native A2A 1.0 JSONRPC.")
        return SimpleNamespace(native=card, protocol_version="1.0.0", preferred_transport="JSONRPC", url=interfaces[0].url)


class A2AClient:
    def __init__(self, http_client, agent_card):
        http_client.headers["A2A-Version"] = "1.0"
        self.transport = JsonRpcTransport(http_client, agent_card.native, agent_card.url)

    async def send_message(self, request):
        response = await self.transport.send_message(to_core_send_message_request(request))
        if not response.HasField("message"):
            raise RuntimeError("Expected an A2A 1.0 completed message, not an unfinished task.")
        return SimpleNamespace(root=SimpleNamespace(result=to_compat_message(response.message)))


class RequestContext:
    """Application view of SDK-owned native server context."""

    def __init__(self, request=None, native=None):
        if native is not None:
            self.message = to_compat_message(native.message)
            self.context_id = native.context_id
            self.metadata = native.metadata
        else:
            self.message = request.message
            self.context_id = self.message.context_id or uuid4().hex
            self.message.context_id = self.context_id
            self.metadata = request.metadata or {}

    def get_user_input(self):
        return "\n".join(part.root.text for part in self.message.parts if part.root.kind == "text")


class ExecutorBridge(AgentExecutor):
    def __init__(self, executor):
        self.executor = executor

    async def execute(self, context, event_queue):
        class Queue:
            async def enqueue_event(self, message):
                await event_queue.enqueue_event(to_core_message(message))
        await self.executor.execute(RequestContext(native=context), Queue())

    async def cancel(self, context, event_queue):
        raise TaskNotCancelableError()


class DefaultRequestHandler:
    def __init__(self, executor, task_store):
        self.executor, self.task_store = executor, task_store


class A2AStarletteApplication:
    """Compose native 1.0 routes without legacy wire compatibility."""

    def __init__(self, card, handler):
        self.card = to_core_agent_card(card)
        for interface in self.card.supported_interfaces:
            interface.protocol_version = "1.0"
        self.handler = NativeRequestHandler(agent_executor=ExecutorBridge(handler.executor),
            task_store=handler.task_store, agent_card=self.card)

    def build(self, lifespan=None):
        return Starlette(routes=[*create_agent_card_routes(self.card),
                                 *create_jsonrpc_routes(self.handler, rpc_url="/")], lifespan=lifespan)