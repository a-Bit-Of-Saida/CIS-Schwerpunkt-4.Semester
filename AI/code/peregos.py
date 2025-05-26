import pika
import json

ALLOWED_PROGRAMS = {"Informatik", "Wirtschaft", "Maschinenbau"}

def callback(ch, method, properties, body):
    message = body.decode()
    try:
        data = json.loads(message)
        if data.get("type") == "ping":
            response = json.dumps({"type": "pong", "source": "peregos"})
            ch.basic_publish(exchange="student_exchange", routing_key="his.pong", body=response)

        elif "programs" in data:
            received_programs = data["programs"]
            print(f"[{data.get('source', 'Receiver')}] Received student data: {json.dumps(data, indent=2)}")
            unknown = [p for p in received_programs if p not in ALLOWED_PROGRAMS]
            if unknown:
                error = json.dumps({"error": f"Peregos: Unknown programs: {', '.join(unknown)}"})
                ch.basic_publish(exchange="student_exchange", routing_key="his.error", body=error)
            else:
                print(f"[Peregos] ✅ All programs valid: {received_programs}")

        else:
            print("[peregos] Received non-program data:", message)
    except json.JSONDecodeError:
        print("[peregos] Received (non-JSON):", message)

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.exchange_declare(exchange="student_exchange", exchange_type="topic")
result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="peregos.info")
channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="peregos.ping")
print("peregos waiting for messages...")
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()