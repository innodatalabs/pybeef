from beef.test.sample_workers import universal, server
import asyncio
import pytest
import contextlib
import sys

async def universal_server(*av, **kaw):
    async with server(universal, *av, **kaw):
        try:
            yield
        finally:
            await asyncio.sleep(2.0)  # give it chance to finish workers

async def test_timeout_1s():
    async with server(universal, task_timeout_seconds=1.0):
        async with universal.connect(url='amqp://localhost/'):
            task_id = await universal.submit(delay=0.1, ret=5)
            result = await universal.result(task_id=task_id)
            assert result == 5


async def test_timeout_1s_expires():
    async with server(universal, task_timeout_seconds=1.0):
        with pytest.raises(Exception, match='task .* failed with remote exception Task timed out after 1.0s'):
            async with universal.connect(url='amqp://localhost/'):
                task_id = await universal.submit(delay=2.0, ret=5)
                result = await universal.result(task_id=task_id)
                assert result == 5

        # call server again to make sure it did not exit on timeout!
        async with universal.connect(url='amqp://localhost/'):
            task_id = await universal.submit(delay=0.1, ret=55)
            result = await universal.result(task_id=task_id)
            assert result == 55


async def test_timeout_1s_expires_and_exits():

    async def server(beef, *av, **kaw):
        async with beef.connect(url='amqp://localhost/'):
            await beef.serve(*av, **kaw)

    server_task = asyncio.create_task(server(universal, task_timeout_seconds=1.0, exit_on_task_timeout=True))
    try:
        with pytest.raises(Exception, match='task .* failed with remote exception Task timed out after 1.0s'):
            async with universal.connect(url='amqp://localhost/'):
                task_id = await universal.submit(delay=2.0, ret=5)
                await universal.result(task_id=task_id)

        await asyncio.sleep(1.0)
        assert server_task.done()
    finally:
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task


async def test_timeout_1s_expires_and_does_not_exit():

    async def server(beef, *av, **kaw):
        async with beef.connect(url='amqp://localhost/'):
            await beef.serve(*av, **kaw)

    server_task = asyncio.create_task(server(universal, task_timeout_seconds=1.0))
    try:
        with pytest.raises(Exception, match='task .* failed with remote exception Task timed out after 1.0s'):
            async with universal.connect(url='amqp://localhost/'):
                task_id = await universal.submit(delay=2.0, ret=5)
                await universal.result(task_id=task_id)

        await asyncio.sleep(1.0)
        assert not server_task.done()
    finally:
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await server_task
