from fastapi import FastAPI, WebSocket
import time
import asyncio
import numpy as np
import orjson

app = FastAPI()

# Track active connections
active_connections: list[WebSocket] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Wait for any messages from the client (optional)
            data = await websocket.receive_text()
            # Process data if needed
            print(f"Received data: {data}")

            # You can send data immediately or in response to client messages
    except Exception as e:
        print(f"Error: {e}")
    finally:
        active_connections.remove(websocket)


# Function to push data to all connected clients
async def broadcast_data():
    while True:
        if len(active_connections) > 0:
            # Generate or fetch your data
            array = np.arange(1000000)
            data = {
                "time": time.time(),
                "value": orjson.dumps(array, option=orjson.OPT_SERIALIZE_NUMPY).decode(
                    "utf-8"
                ),
            }

            # Send to all connected clients
            for connection in active_connections:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    print(f"Error sending data: {e}")

        # Adjust frequency as needed
        await asyncio.sleep(1)  # 100ms intervals


# Start the background task when the app starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_data())
