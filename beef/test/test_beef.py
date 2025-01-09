from beef import beef, State, TaskNotFoundError
import pytest
import asyncio
from beef.test.sample_workers import addition, multiplication, short_lived, universal, server

@pytest.fixture(scope='function')
async def addition_server():
    async with server(addition):
        yield

@pytest.fixture(scope='function')
async def multiplication_server():
    async with server(multiplication):
        yield

@pytest.fixture(scope='function')
async def short_lived_server():
    async with server(short_lived):
        yield

@pytest.fixture(scope='function')
async def universal_server():
    async with server(universal):
        try:
            yield
        finally:
            await asyncio.sleep(2.0)  # give it chance to finish workers

async def test_beef():
    with pytest.raises(ValueError, match='beef can only wrap async functions'):
        def work(a, b):
            return a + b
        beef(work)

    async def work(a, b):
        return a + b

    b = beef(work)
    assert b.name == 'test_beef.work'

async def test_beef_name():
    assert addition.name == 'beef.test.sample_workers.addition'
    assert multiplication.name == 'multiplication-queue'

async def test_beef_call():
    assert await addition(1, 2) == 3
    assert await multiplication(1, 2) == 2

async def test_beef_no_connection():
    with pytest.raises(RuntimeError, match='Connection context is missing. Did you forget to wrap this call in "async with beef.connect(...)"?'):
        await addition.serve()

async def test_beef_no_connection2():
    with pytest.raises(RuntimeError, match='Connection context is missing. Did you forget to wrap this call in "async with beef.connect(...)"?'):
        await addition.submit(1, 2)

async def test_beef_no_task_id():
    with pytest.raises(RuntimeError, match='Could not find task_id in the context. You can only omit task_id parameter when calling this method from worker function.'):
        await addition.get_status()

async def test_bad_task_id():
    with pytest.raises(RuntimeError, match='Task "hoho" not found'):
        async with addition.connect(url='amqp://localhost/'):
            await addition.get_status(task_id='hoho')

async def test_bad_task_id2():
    with pytest.raises(RuntimeError, match='Task "hoho" not found'):
        async with addition.connect(url='amqp://localhost/'):
            await addition.result(task_id='hoho')

async def test_serve_multiple(addition_server, multiplication_server):
    async with addition.connect(url='amqp://localhost/'), multiplication.connect(url='amqp://localhost/'):
        task_id = await addition.submit(1, 2)
        result = await addition.result(task_id=task_id)
        assert result == 3

        task_id = await addition.submit(1, 2)
        result = await addition.result(task_id=task_id)
        assert result == 3

async def test_short_lived_does_not_expire(short_lived_server):
    # queue does not expire, because we are waiting for result (there is an active channel waiting fro completion)
    async with short_lived.connect(url='amqp://localhost/'):
        task_id = await short_lived.submit(delay=2, ret=1)
        result = await short_lived.result(task_id=task_id)
        assert result == 1

async def test_short_lived_expires(short_lived_server):
    # here queue does expire, because we connect to the sever after task reply timeout
    async with short_lived.connect(url='amqp://localhost/'):
        task_id = await short_lived.submit(ret=1)

    await asyncio.sleep(2)
    async with short_lived.connect(url='amqp://localhost/'):
        with pytest.raises(RuntimeError, match='Task .+ not found'):
            await short_lived.result(task_id=task_id)

async def test_final_status_persists(universal_server):
    # here queue does expire, because we connect to the sever after task reply timeout
    async with universal.connect(url='amqp://localhost/'):
        task_id = await universal.submit(ret=1)

    await asyncio.sleep(0.2)
    async with universal.connect(url='amqp://localhost/'):
        status = await universal.get_status(task_id=task_id)
        assert status.is_final
        assert status.state == State.SUCCESS
        assert status.body == 1

    # check that final success state is still there
    await asyncio.sleep(2.5)
    async with universal.connect(url='amqp://localhost/'):
        status = await universal.get_status(task_id=task_id)
        assert status.is_final
        assert status.state == State.SUCCESS
        assert status.body == 1

async def test_canceled(universal_server):
    # here queue does expire, because we connect to the sever after task reply timeout
    async with universal.connect(url='amqp://localhost/'):
        task_id = await universal.submit(ret=1, delay=1.0)

    await asyncio.sleep(0.1)
    async with universal.connect(url='amqp://localhost/'):
        status = await universal.get_status(task_id=task_id)
        assert not status.is_final
        assert status.state == State.WORKING

    await asyncio.sleep(0.1)
    async with universal.connect(url='amqp://localhost/'):
        await universal.cancel(task_id=task_id, message='go away, we do not need you')

    await asyncio.sleep(0.1)
    async with universal.connect(url='amqp://localhost/'):
        status = await universal.get_status(task_id=task_id)
        assert status.is_final
        assert status.state == State.CANCELED
        assert status.body == 'go away, we do not need you'

    await asyncio.sleep(1.0)  # let the worker finish

async def test_cleanup(universal_server):
    # here queue does expire, because we connect to the sever after task reply timeout
    async with universal.connect(url='amqp://localhost/'):
        task_id = await universal.submit(ret=1)

    await asyncio.sleep(0.2)
    async with universal.connect(url='amqp://localhost/'):
        status = await universal.get_status(task_id=task_id)
        assert status.is_final
        assert status.state == State.SUCCESS
        assert status.body == 1

    # check that final success state is still there
    await asyncio.sleep(2.5)
    async with universal.connect(url='amqp://localhost/'):
        status = await universal.get_status(task_id=task_id)
        assert status.is_final
        assert status.state == State.SUCCESS
        assert status.body == 1

    async with universal.connect(url='amqp://localhost/'):
        await universal.cleanup(task_id=task_id)

    await asyncio.sleep(2.5)
    async with universal.connect(url='amqp://localhost/'):
        with pytest.raises(TaskNotFoundError):
            await universal.get_status(task_id=task_id)

async def test_with_name(multiplication_server):
    # we use `addition` worker to triegger execution of multiplication worker
    # by swapping queue name, temporarily
    async with addition.connect(url='amqp://localhost/'):
        task_id = await addition.submit_to(multiplication.name, 5, 6)

    await asyncio.sleep(0.2)
    async with addition.connect(url='amqp://localhost/'):
        status = await addition.get_status(task_id=task_id)
        assert status.is_final
        assert status.state == State.SUCCESS
        assert status.body == 30

