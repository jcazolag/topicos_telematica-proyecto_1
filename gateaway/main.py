from fastapi import FastAPI
import pika, uuid, json

from dotenv import load_dotenv
import os
load_dotenv()

rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = int(os.getenv("RABBITMQ_PORT"))
rabbitmq_user = os.getenv("RABBITMQ_USER")
rabbitmq_pass = os.getenv("RABBITMQ_PASS")

app = FastAPI()

@app.get("/")
def read_root():
    return {"mensaje": "¡Hola desde FastAPI!"}

@app.get("/saludo/{microservicio_id}/{nombre}")
def saludo(microservicio_id: int, nombre: str):
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitmq_host,
                port=rabbitmq_port,
                credentials=credentials
            )
        )
    except pika.exceptions.AMQPConnectionError:
        return {"error": "No se pudo conectar a RabbitMQ"}

    channel = connection.channel()
    corr_id = str(uuid.uuid4())
    reply_queue = channel.queue_declare(queue='', exclusive=True).method.queue

    response = None
    def on_response(ch, method, props, body):
        nonlocal response
        if props.correlation_id == corr_id:
            response = json.loads(body)["message"]

    # Consumir la respuesta desde la cola response_queue
    channel.basic_consume(
        queue=reply_queue,
        on_message_callback=on_response,
        auto_ack=True
    )

    message = {
        "name": nombre,
        "service_id": microservicio_id,
        "reply_to": reply_queue,
        "correlation_id": corr_id
    }

    # Publicar el mensaje en request_queue
    channel.basic_publish(
        exchange='',
        routing_key='request_queue',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            reply_to=reply_queue,
            correlation_id=corr_id
        )
    )

    import time
    timeout = 5
    start_time = time.time()
    while response is None:
        connection.process_data_events()
        if time.time() - start_time > timeout:
            return {"error": "Tiempo de espera agotado, el microservicio no respondió"}

    connection.close()
    return {"respuesta": response}
