import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='54.83.38.254',
    port=5672,
    credentials=pika.PlainCredentials('microservicio', 'password123')
))

channel = connection.channel()
channel.queue_declare(queue='prueba')

channel.basic_publish(exchange='', routing_key='prueba', body='¡Hola RabbitMQ!')
print("✅ Mensaje enviado correctamente")

connection.close()
