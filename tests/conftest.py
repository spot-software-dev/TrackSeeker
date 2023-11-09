import pytest
from loguru import logger
from _pytest.logging import LogCaptureFixture
from ..instagram_bot import IGBOT
from ..drive_logic import Drive


@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,  # Set to 'True' if your test is spawning child processes.
    )
    yield caplog
    logger.remove(handler_id)


@pytest.fixture
def drive():
    return Drive()


@pytest.fixture
def igbot():
    return IGBOT()
