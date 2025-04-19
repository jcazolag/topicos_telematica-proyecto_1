import grpc
from concurrent import futures
import time
import pika

from compilacion import microservicio_pb2, microservicio_pb2_grpc

import os
from dotenv import load_dotenv

load_dotenv()

id = os.getenv("SERVER_ID")

mom_ip = os.getenv("MOM_IP")
mom_port = os.getenv("MOM_PORT")
mom_name = os.getenv("MOM_NAME")
mom_password = os.getenv("MOM_PASSWORD")

class SaludoServiceServicer(microservicio_pb2_grpc.SaludoServiceServicer):
    def __init__(self, microservicio_id):
        self.microservicio_id = microservicio_id
        self.rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=mom_ip,
            port=mom_port,
            credentials=pika.PlainCredentials(mom_name, mom_password)
        ))
        self.channel = self.rabbit_connection.channel()
        self.channel.queue_declare(queue='logs')

    def Saludar(self, request, context):
        nombre = request.nombre
        respuesta = f"Hola, {nombre}, soy el Microservicio {self.microservicio_id}"
        
        # Enviar mensaje a RabbitMQ
        self.channel.basic_publish(
            exchange='',
            routing_key='logs',
            body=respuesta
        )

        print(f"✅ Se recibió: {nombre} y se envió a RabbitMQ: {respuesta}")
        return microservicio_pb2.SaludoReply(mensaje=respuesta)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    microservicio_pb2_grpc.add_SaludoServiceServicer_to_server(
        SaludoServiceServicer(microservicio_id=id), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print("🚀 Microservicio 1 escuchando en puerto 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
