import pika
import json

def callback(ch, method, properties, body):
    message = body.decode()
    
    try:
        data = json.loads(message)
        if data.get("type") == "ping":
            # Keine Anzeige für Ping-Nachrichten, aber Pong senden
            response = json.dumps({"type": "pong", "source": "peregos"})
            ch.basic_publish(exchange="student_exchange", routing_key="his.pong", body=response)
        else:
            print("[Peregos] Received:", message)  # Nur Nutzdaten anzeigen
    except json.JSONDecodeError:
        print("[Peregos] Received (non-JSON):", message)

# Verbindung zu RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.exchange_declare(exchange="student_exchange", exchange_type="topic")

# Temporäre exklusive Queue deklarieren
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

# Binde relevante Routing-Keys
channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="peregos.info")
channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="peregos.ping")

print("Peregos waiting for messages...")
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()
