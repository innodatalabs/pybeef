from beef import beef
import asyncio

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
