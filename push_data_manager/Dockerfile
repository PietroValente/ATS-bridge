FROM python:3.12-slim
WORKDIR /app

COPY push_data_manager/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt grpcio-tools

COPY proto/ /proto/
RUN python -m grpc_tools.protoc \
    -I/proto \
    --python_out=/app \
    --grpc_python_out=/app \
    /proto/klaaryo.proto

COPY push_data_manager/ .

ENV DJANGO_SETTINGS_MODULE=push_data_manager.settings

RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
