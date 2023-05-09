import asyncio
from fastapi import FastAPI, WebSocket, Response, status
from connection_manager import ConnectionManager
app = FastAPI()
conn_manager=ConnectionManager()


@app.websocket("/test")
async def speech_to_text(asr_client: WebSocket):
    await conn_manager.connect(asr_client)
    await asr_client.send_text("a")
    await asyncio.sleep(1)
    await asr_client.send_text("b")
    asr = await conn_manager.disconnect(asr_client)
    print("Client disconnected.")

 
