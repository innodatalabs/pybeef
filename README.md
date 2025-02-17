# beef

Beef is good for your health.

An opinionated distributed RPC using AMQP messages (inspired by celery amqp backend).

## Installing

```bash
pip install pybeef
```

## Usage

Worker:

```python
from beef import beef

@beef
async def add(x: int, y: int) -> int:
    return x + y
```

Server:

```python
async def server():
    async with add.connect('amqp://localhost/'):
        await add.serve()  # here server blocks forever, executing incoming tasks

if __name__ == '__main__':
    import asyncio

    asyncio.run(server())
```

Client (blocking):

```python
async def client():
    async with add.connect('amqp://localhost/'):
        task_id = await add.submit(1, 2)  # submits task
        result = await add.result(task_id)  # waits for completion

if __name__ == '__main__':
    import asyncio

    asyncio.run(client())
```

Client (polling):

```python
import asyncio

async def client():
    async with add.connect('amqp://localhost/'):
        task_id = await add.submit(1, 2)  # submits task

        while True:
            status = await add.get_status(task_id)
            if status.is_final:
                break
            await asyncio.sleep(1)
        print(f'Task {task_id} completed with status {status})

if __name__ == '__main__':
    import asyncio

    asyncio.run(client())
```

## Testing

You need a running RabbitMQ server for testing. For example:

```bash
docker run -it --network host rabbitmq
```

Then, make sure that test dependencies are installed:

```bash
pip install .[test]
```

Finally, run the tests

```bash
python -m pytest beef/test
```

or

```bash
make test
```

## Building

```bash
pip wheel . --no-deps -w wheels/
```

or

```bash
make
```

## Publishing

```bash
twine upload wheels/pybeef-XXX.whl -u __token__ -p <secret-pipy-token>
```
