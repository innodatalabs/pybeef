import asyncio
from beef.pool import Pool


class FakeChannel:

    def __init__(self, cid=None):
        self.is_closed = False
        self.cid = cid

    async def close(self):
        self.is_closed = True

class FakeConnection:
    def __init__(self):
        self._cid = 0

    async def channel(self):
        self._cid += 1
        cid = self._cid
        return FakeChannel(cid)


async def test_pool():
    pool = Pool(FakeConnection(), max_items=2)
    async with pool.acquire() as channel:
        assert not channel.is_closed
        assert channel.cid == 1
    await channel.close()
    async with pool.acquire() as channel:
        assert not channel.is_closed
        assert channel.cid == 2
    async with pool.acquire() as channel1:
        async with pool.acquire() as channel2:
            assert not channel1.is_closed
            assert channel1.cid == 2
            assert not channel2.is_closed
            assert channel2.cid == 3

    async def hold_channel():
        async with pool.acquire() as channel:
            assert not channel.is_closed
            assert channel.cid == 3
            await asyncio.sleep(1)
            return channel

    hold = asyncio.create_task(hold_channel())
    await asyncio.sleep(0.1)
    async with pool.acquire() as channel1:
        assert not channel1.is_closed
        assert channel1.cid == 2
        async with pool.acquire() as channel2:
            assert not channel2.is_closed
            assert channel2.cid == 3
    await hold
