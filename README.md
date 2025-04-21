# Topicos Especiales en Telematica
## Proyecto 1
### Opcion 2 - gRPC + MOM

---

**Integrantes:**
- Juan Sebastian Jácome Burbano - jsjacomeb@eafit.edu.co
- Juan Camilo anzola Gómez - jcanzolag@eafit.edu.co

---

## GRPC

Para este proyecto utilizamos python en la implementacion del grpc. Creamos 3 microservicios sencillos los cuales reciben un nombre y devuelven un mensaje de saludo (ejemplo, "Hola, Pepito, Soy el Microservicio 1").

- **IP´s:**
    - **Microservicio 1:** 52.54.183.72:50051
    - **Microservicio 2:** 34.225.64.212:50051
    - **Microservicio 3:** 18.214.152.83:50051
    - **Worker:** 44.217.113.210

- **Requerimientos:**
    ```
    grpcio == 1.71.0
    grpcio-tools == 1.71.0
    pika == 1.3.2
    python-dotenv == 1.1.0
    ```

- **Archivo proto:**
    ```proto
    syntax = "proto3";

    package microservicio;

    service SaludoService {
    rpc Saludar (SaludoRequest) returns (SaludoReply) {}
    }

    message SaludoRequest {
    string nombre = 1;
    }

    message SaludoReply {
    string mensaje = 1;
    }
    ```

- **Server:**
    ```python
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
    ```

- **worker:**
    ```python
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
    ```

---
## MOM

Para el MOM utilizamos rabbitmq, el cual montamos en una instancia ec2 con docker. Utilizamos los siguientes comandos para levantar el servicio:

```bash
# Instalar Docker
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl start docker

# Correr RabbitMQ con panel web
sudo docker run -d --name rabbitmq \
-p 5672:5672 -p 15672:15672 \
-e RABBITMQ_DEFAULT_USER=microservicios \
-e RABBITMQ_DEFAULT_PASS=password123 \
rabbitmq:3-management
```

**IP:** 54.197.149.87:15672

---
## API-GATEWAY

Para el api gateway montamos una api con fastapi en una instancia ec2.

- **IP:** 54.224.31.253:8000

- **Requerimientos:**
    ```
    pika == 1.3.2
    fastapi == 0.115.12
    uvicorn == 0.34.2
    python-dotenv == 1.1.0
    ```

- **Codigo:**
    ```python
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
    ```

---
## Cliente REST

Para el cliente REST usamos la funcionalidad de API de aws y la conectamos a el api gateway.

- **IP:** https://vop14aud58.execute-api.us-east-1.amazonaws.com/docs