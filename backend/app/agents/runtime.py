"""Run-local infrastructure for typed communication between autonomous agents."""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field

from app.agents.protocol import (
    AgentCommunication,
    AgentContext,
    AgentId,
    AgentLocalState,
    AgentMessage,
    AgentPlan,
    AgentReview,
    MessageEndpoint,
    ToolObservation,
)


@dataclass
class AgentBlackboard:
    """Shared blackboard; routing decisions remain explicit agent messages."""

    context: AgentContext
    max_rounds: int
    review_enabled: bool
    current_round: int = 1
    plan: AgentPlan | None = None
    draft: str = ""
    review: AgentReview | None = None
    observations: list[ToolObservation] = field(default_factory=list)
    final_response: str = ""


class MASAgent(ABC):
    """Autonomous specialist with a goal, capabilities, and run-local state."""

    agent_id: AgentId
    objective: str
    capabilities: tuple[str, ...]

    def create_state(self) -> AgentLocalState:
        return AgentLocalState(
            agent=self.agent_id,
            objective=self.objective,
            capabilities=list(self.capabilities),
        )

    @abstractmethod
    async def handle(
        self,
        message: AgentMessage,
        blackboard: AgentBlackboard,
        state: AgentLocalState,
    ) -> list[AgentMessage]:
        """Perceive one message, decide locally, and emit zero or more messages."""


class MASMessageBus:
    """FIFO message bus with sanitized communication tracing and local counters."""

    def __init__(self, states: dict[AgentId, AgentLocalState]):
        self._queue: deque[AgentMessage] = deque()
        self._states = states
        self.communications: list[AgentCommunication] = []

    def publish(self, message: AgentMessage) -> None:
        sender = self._as_agent_id(message.sender)
        if sender is not None:
            self._states[sender].messages_sent += 1
        self._queue.append(message)
        self.communications.append(
            AgentCommunication(
                message_id=message.message_id,
                sender=message.sender,
                recipient=message.recipient,
                performative=message.performative,
                kind=message.kind,
                round=message.round,
                summary=message.summary,
            )
        )

    def receive(self) -> AgentMessage | None:
        if not self._queue:
            return None
        message = self._queue.popleft()
        recipient = self._as_agent_id(message.recipient)
        if recipient is not None:
            state = self._states[recipient]
            state.messages_received += 1
            state.last_message_kind = message.kind
        return message

    @staticmethod
    def _as_agent_id(endpoint: MessageEndpoint) -> AgentId | None:
        try:
            return AgentId(endpoint.value)
        except ValueError:
            return None
