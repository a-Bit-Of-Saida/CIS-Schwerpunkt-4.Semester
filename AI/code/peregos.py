import pika

def callback(ch, method, properties, body):
    print("[Peregos] Received:", body.decode())

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.exchange_declare(exchange="student_exchange", exchange_type="topic")
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="peregos.info")

print("Peregos waiting for messages...")
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
