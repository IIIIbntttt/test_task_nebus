import asyncio

from payments.outbox.worker import run_outbox_iteration
from payments.shared.db import get_session_factory


class FailingOutboxService:
    async def flush_pending(self, session) -> int:
        raise RuntimeError("publish failed")


def _run(coro):
    return asyncio.run(coro)


def test_run_outbox_iteration_handles_exceptions_without_crash(client) -> None:
    session_factory = get_session_factory()
    success = _run(run_outbox_iteration(FailingOutboxService(), session_factory))
    assert success is False
