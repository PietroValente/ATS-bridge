FROM python:3.12-slim
WORKDIR /app

COPY talent_pool/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt grpcio-tools

COPY proto/ /proto/
RUN python -m grpc_tools.protoc \
    -I/proto \
    --python_out=/app \
    --grpc_python_out=/app \
    /proto/klaaryo.proto

COPY talent_pool/ .

CMD ["python", "server.py"]
