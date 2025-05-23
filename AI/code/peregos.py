import pika
import json

def callback(ch, method, properties, body):
    message = body.decode()
    print("[Peregos] Received:", message)
    
    try:
        data = json.loads(message)
        if data.get("type") == "ping":
            response = json.dumps({"type": "pong", "source": "peregos"})
            ch.basic_publish(exchange="student_exchange", routing_key="his.pong", body=response)
    except json.JSONDecodeError:
        pass  # ignore non-JSON messages

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.exchange_declare(exchange="student_exchange", exchange_type="topic")

result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

# Lauscht auf Daten + Pings
channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="peregos.info")
channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="peregos.ping")

print("Peregos waiting for messages...")
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
