from beef.test.sample_workers import timeout_1s, server
import asyncio
import pytest

@pytest.fixture(scope='function')
async def timeout_1s_server():
    async with server(timeout_1s):
        try:
            yield
        finally:
            await asyncio.sleep(2.0)  # give it chance to finish workers


async def test_timeout_1s(timeout_1s_server):
    async with timeout_1s.connect(url='amqp://localhost/'):
        task_id = await timeout_1s.submit(delay=0.1, ret=5)
        result = await timeout_1s.result(task_id=task_id)
        assert result == 5


async def test_timeout_1s_expires(timeout_1s_server):
    with pytest.raises(Exception, match='task .* failed with remote exception TimeoutError()'):
        async with timeout_1s.connect(url='amqp://localhost/'):
            task_id = await timeout_1s.submit(delay=2.0, ret=5)
            result = await timeout_1s.result(task_id=task_id)
            assert result == 5
