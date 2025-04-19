import grpc
from concurrent import futures

import microservicio_pb2, microservicio_pb2_grpc

import os
from dotenv import load_dotenv

load_dotenv()

id = os.getenv("SERVER_ID")

class SaludoServiceServicer(microservicio_pb2_grpc.SaludoServiceServicer):
    def __init__(self, microservicio_id):
        self.microservicio_id = microservicio_id

    def Saludar(self, request, context):
        nombre = request.nombre
        respuesta = f"Hola, {nombre}, soy el Microservicio {self.microservicio_id}"

        print(f"✅ Se recibió: {nombre}")
        return microservicio_pb2.SaludoReply(mensaje=respuesta)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    microservicio_pb2_grpc.add_SaludoServiceServicer_to_server(
        SaludoServiceServicer(microservicio_id=id), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print(f"🚀 Microservicio {id} escuchando en puerto 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
