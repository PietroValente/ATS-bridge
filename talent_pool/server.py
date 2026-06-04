import os
from concurrent import futures

import grpc

import klaaryo_pb2_grpc
import repository
from event_bus.redis_adapter import RedisEventBus
from servicer import TalentPoolServicer


def serve() -> None:
    db_path = os.environ.get("DB_PATH", "/data/talent_pool.db")
    redis_host = os.environ.get("REDIS_HOST", "redis")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))

    repository.init_db(db_path)
    bus = RedisEventBus(host=redis_host, port=redis_port)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    klaaryo_pb2_grpc.add_TalentPoolServicer_to_server(
        TalentPoolServicer(db_path, bus), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("talent_pool listening on :50051", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
