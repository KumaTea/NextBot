import asyncio
from aiohttp import web

# Create a queue to hold the tasks
task_queue = asyncio.Queue()
COUNTER = 0


async def handle_request(request):
    # Simulate a task that takes time and resources
    # task_data = await request.json()
    global COUNTER
    COUNTER += 1
    print(f"Received task: {COUNTER}")
    await task_queue.put(COUNTER)
    return web.json_response({"status": "Task received"})


async def process_tasks():
    while True:
        task_data = await task_queue.get()
        print(f"Processing task: {task_data}")
        # Simulate a time-consuming task
        await asyncio.sleep(5)
        print(f"Completed task: {task_data}")
        task_queue.task_done()


async def init_app():
    app = web.Application()
    app.router.add_get('/submit', handle_request)
    return app


async def main():
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    # Start the task processor
    task_processor = asyncio.create_task(process_tasks())

    print("Server started at http://0.0.0.0:8080")
    try:
        while True:
            await asyncio.sleep(3600)  # Keep the server running
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
