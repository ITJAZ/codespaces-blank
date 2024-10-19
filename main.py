import time
import asyncio
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
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
    while True:
        if queue.full():
            time.sleep(random.uniform(0.5, 1.5))  # 當 queue 滿時，等待
            continue

        task = random.randint(1, 100)
        queue.put(task)
        print(f"Produced task: {task}")
        asyncio.run(manager.broadcast(f"Produced task: {task}, Queue Size: {queue.qsize()}"))
        time.sleep(random.uniform(0.5, 0.5))  # 模擬不同的生產速度

# 消費者函數
def consumer():
    while True:
        if queue.empty():
            time.sleep(random.uniform(0.5, 1.5))  # 當 queue 為空時，等待
            continue

        task = queue.get()
        print(f"Consumed task: {task}")
        asyncio.run(manager.broadcast(f"Consumed task: {task}, Queue Size: {queue.qsize()}"))
        time.sleep(random.uniform(0.5, 0.5))  # 模擬消費的時間

# 啟動生產者和消費者的執行緒池
def start_producer_pool():
    for _ in range(producer_pool_size):
        producer_thread = Thread(target=producer)
        producer_thread.start()
        producers.append(producer_thread)

def start_consumer_pool():
    for _ in range(consumer_pool_size):
        consumer_thread = Thread(target=consumer)
        consumer_thread.start()
        consumers.append(consumer_thread)

# API 入口：啟動生產者和消費者池
@app.get("/start")
async def start_pool():
    start_producer_pool()
    start_consumer_pool()
    return {"message": "Producer and Consumer Pools Started"}

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
