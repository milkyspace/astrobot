from rq import Worker, Queue
from rq.connections import RedisConnection
from redis import Redis
import os

listen = ["payments", "calculations"]

redis_conn = Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
)

if __name__ == "__main__":
    with RedisConnection(redis_conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
