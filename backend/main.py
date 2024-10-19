import time
import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from queue import Queue
from threading import Thread
from typing import List

app = FastAPI()

# 任務佇列（最大容量為 100）
queue = Queue(maxsize=100)
producers = []
consumers = []
clients = []

producer_pool_size = 6
consumer_pool_size = 5
running_producers = False
running_consumers = False

# WebSocket 連接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# 生產者函數
def producer():
    while running_producers:
        if queue.full():
            time.sleep(random.uniform(0.5, 1.5))
            continue

        task = random.randint(1, 100)
        queue.put(task)
        print(f"Produced task: {task}")
        asyncio.run(manager.broadcast(f"Produced task: {task}, Queue Size: {queue.qsize()}"))
        time.sleep(random.uniform(0.3, 0.7))

# 消費者函數
def consumer():
    while running_consumers:
        if queue.empty():
            time.sleep(random.uniform(0.5, 1.5))
            continue

        task = queue.get()
        print(f"Consumed task: {task}")
        asyncio.run(manager.broadcast(f"Consumed task: {task}, Queue Size: {queue.qsize()}"))
        time.sleep(random.uniform(0.7, 1.2))

# 啟動生產者和消費者的執行緒池
def start_producer_pool():
    global running_producers
    running_producers = True
    for _ in range(producer_pool_size):
        producer_thread = Thread(target=producer)
        producer_thread.start()
        producers.append(producer_thread)

def start_consumer_pool():
    global running_consumers
    running_consumers = True
    for _ in range(consumer_pool_size):
        consumer_thread = Thread(target=consumer)
        consumer_thread.start()
        consumers.append(consumer_thread)

def stop_producer_pool():
    global running_producers
    running_producers = False

def stop_consumer_pool():
    global running_consumers
    running_consumers = False

# API 入口：啟動/停止生產者和消費者池
@app.post("/start")
async def start_pool():
    start_producer_pool()
    start_consumer_pool()
    return {"message": "Producer and Consumer Pools Started"}

@app.post("/stop")
async def stop_pool():
    stop_producer_pool()
    stop_consumer_pool()
    return {"message": "Producer and Consumer Pools Stopped"}

# API 入口：設置生產者和消費者數量
@app.post("/set_pool")
async def set_pool(producer_count: int, consumer_count: int):
    global producer_pool_size, consumer_pool_size
    producer_pool_size = producer_count
    consumer_pool_size = consumer_count
    return {"message": f"Producer count set to {producer_count}, Consumer count set to {consumer_count}"}

# WebSocket 連接入口
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket disconnected")
