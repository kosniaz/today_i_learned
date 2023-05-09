import asyncio
from tornado import websocket

 
# define a coroutine
async def custom_coroutine():
    print("opening a websocket to localhost:8000/test")
    await asyncio.sleep(1)
    ws= await websocket.websocket_connect("ws://localhost:8000/test")
    print("trying to read an open websocket")
    await asyncio.sleep(1)
    first_message= await ws.read_message()
    print("first message is " + first_message + ". sleeping 4 seconds")
    await asyncio.sleep(4)
    print("trying to read again, this time on closed websocket but with unread message")
    first_message= await ws.read_message()
    print("second message is " + first_message)
    await asyncio.sleep(1)
    print("trying to read again on closed websocket")
    message= await ws.read_message()
    print("Got " + str(message), "indicating that websocket's closed and theres no unread messages")
    print("trying to write to the closed websocket")
    await asyncio.sleep(1)
    try:
        await ws.write_message("aaa")
    except websocket.WebSocketClosedError as e:
        print("Got WebsocketClosedError: " + str(e))
    print("trying to read again, on a closed websocket")
    message= await ws.read_message()
    import random
    if random.randint(0,9) % 2==0:
        print("trying to read again, on a closed websocket. It hangs")
        await asyncio.sleep(1)
        message= await ws.read_message()
 
# execute the coroutine
asyncio.run(custom_coroutine())
