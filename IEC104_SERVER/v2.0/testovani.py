# SuperFastPython.com
# example of using an asyncio event object
from random import random
import asyncio
import time
 
# task coroutine
async def taska(event, num, number):
    # wait for the event to be set
    await event.wait()
    # generate a random value between 0 and 1
    value = random()
    # block for a moment
    await asyncio.sleep(value)
    # report a message
    print(f'Task {num}.{number} got {value}')
    
def task(event, num, number):
    # wait for the event to be set
    # generate a random value between 0 and 1
    value = random()
    # block for a moment
    time.sleep(value)
    # report a message
    print(f'Task {num}.{number} got {value}')
 
# main coroutine
async def main():
    # create a shared event object
    event = asyncio.Event()
    # create and run the tasks
    tasks = [asyncio.create_task(taska(event,1, i)) for i in range(5)]
    tasks1 = [task(event,0, i) for i in range(5)]
    
    tasks2 = [asyncio.create_task(taska(event, 2,i)) for i in range(5)]
    # allow the tasks to start
    print('Main blocking...')
    await asyncio.sleep(5)
    # start processing in all tasks
    print('Main setting the event')
    event.set()
    # await for all tasks  to terminate
    _1 = await asyncio.wait(tasks)
    time.sleep(1)
    event.clear()
    _2 = await asyncio.wait(tasks2)
 
# run the asyncio program
asyncio.run(main())
