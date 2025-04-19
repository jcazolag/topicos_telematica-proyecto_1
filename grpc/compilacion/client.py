import grpc

import microservicio_pb2, microservicio_pb2_grpc

def run():
    with grpc.insecure_channel('[::]:50051') as channel:
        stub = microservicio_pb2_grpc.SaludoServiceStub(channel)
        response = stub.Saludar(microservicio_pb2.SaludoRequest(nombre="Carlos"))
        print("🟢 Respuesta del microservicio:", response.mensaje)

if __name__ == '__main__':
    run()
