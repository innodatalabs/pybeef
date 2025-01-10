from beef import beef
import asyncio
import contextlib

@beef
async def addition(a, b):
    return a + b

@beef(queue_name='multiplication-queue')
async def multiplication(a, b):
    return a * b

@beef(reply_expiration_millis=1000)
async def short_lived(*, delay=None, exception=None, ret=None):
    if delay is not None:
        await asyncio.sleep(delay)
    if exception is not None:
        raise exception
    return ret

@beef
async def universal(*, delay=None, exception=None, ret=None):
    if delay is not None:
        await asyncio.sleep(delay)
    if exception is not None:
        raise exception
    return ret

@contextlib.asynccontextmanager
async def server(beef, *av, **kaw):
    async def server():
        async with beef.connect(url='amqp://localhost/'):
            await beef.serve(*av, **kaw)

    server_task = asyncio.create_task(server())

    yield
    server_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await server_task

