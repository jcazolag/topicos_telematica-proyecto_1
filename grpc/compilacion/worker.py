import pika
import json
import os
import grpc
from dotenv import load_dotenv
from microservicio_pb2 import SaludoRequest  # Importa las definiciones de gRPC
from microservicio_pb2_grpc import SaludoServiceStub

# Cargar variables de entorno
load_dotenv()

rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = int(os.getenv("RABBITMQ_PORT"))
rabbitmq_user = os.getenv("RABBITMQ_USER")
rabbitmq_pass = os.getenv("RABBITMQ_PASS")

micro1 = os.getenv("MICRO1_IP")
micro2 = os.getenv("MICRO2_IP")
micro3 = os.getenv("MICRO3_IP")

# Configuración de conexión gRPC
def get_grpc_channel(service_id):
    """ Devuelve el canal gRPC para el microservicio correspondiente """
    if service_id == 1:
        return grpc.insecure_channel(f"{micro1}:50051")
    elif service_id == 2:
        return grpc.insecure_channel(f"{micro2}:50051")
    elif service_id == 3:
        return grpc.insecure_channel(f"{micro3}:50051")
    else:
        raise ValueError("ID de microservicio no válido")

def worker():
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            credentials=credentials
        )
    )
    channel = connection.channel()

    # Declarar las colas
    channel.queue_declare(queue='request_queue', durable=True)
    channel.queue_declare(queue='response_queue', durable=True)


    # Callback para procesar los mensajes en request_queue
    def on_request(ch, method, props, body):
        try:
            message = json.loads(body)
            name = message['name']
            service_id = message['service_id']

            # Establecer canal gRPC para el microservicio correspondiente
            grpc_channel = get_grpc_channel(service_id)
            stub = SaludoServiceStub(grpc_channel)

            # Realizar la solicitud gRPC
            request = SaludoRequest(nombre=name)
            response = stub.Saludar(request)  # Realiza la llamada gRPC

            # Enviar la respuesta a la cola de respuesta (response_queue)
            ch.basic_publish(
                exchange='',
                routing_key=props.reply_to,
                body=json.dumps({"message": response.mensaje}),
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id
                )
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error al procesar el mensaje: {e}")

    # Consumir mensajes desde request_queue
    channel.basic_consume(
        queue='request_queue',
        on_message_callback=on_request
    )

    print("Worker esperando mensajes. Para salir presiona CTRL+C.")
    channel.start_consuming()

if __name__ == '__main__':
    worker()
