import sys
import json
import pika
import threading
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QVBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

ALLOWED_PROGRAMS = {"Computer Science", "Economy", "AI"}

class WyseflowUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WyseFlow – Message Monitor")
        self.setMinimumSize(700, 400)

        self.data_file = "received_students_wyseflow.json"
        self.received_data = {}

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 10))

        self.status_label = QLabel("🔄 Waiting for messages...")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.setup_ui()
        self.load_existing_data()  # ✅ Nach UI-Setup!
        self.start_rabbitmq_listener()


    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📥 Received Student Data:"))
        layout.addWidget(self.log_area)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def log(self, text: str):
        self.log_area.append(text)

    def save_student_data(self, student: dict):
        key = f"{student['name']}_{student['ID']}"
        timestamp = datetime.now().isoformat()
        self.received_data[key] = {
            "timestamp": timestamp,
            "data": student
        }
        with open(self.data_file, "w") as f:
            json.dump(self.received_data, f, indent=4)

    def load_existing_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.received_data = json.load(f)

                for key, entry in self.received_data.items():
                    student = entry.get("data")
                    if not student:
                        self.log(f"⚠️ Skipped entry '{key}': no 'data' field.")
                        continue

                    name = student.get("name")
                    number = student.get("ID")
                    programs = student.get("programs")

                    if name and number and programs:
                        self.log(f"[Startup] {key}:\n{json.dumps(student, indent=2)}")
                    else:
                        self.log(f"⚠️ Incomplete data in entry '{key}'.")
            except Exception as e:
                print(f"⚠️ Failed to load students:", e)


    def start_rabbitmq_listener(self):
        def callback(ch, method, properties, body):
            message = body.decode()
            try:
                data = json.loads(message)
                if data.get("type") == "ping":
                    pong = json.dumps({"type": "pong", "source": "wyseflow"})
                    ch.basic_publish(exchange="student_exchange", routing_key="his.pong", body=pong)
                    self.status_label.setText("✅ Ping received, Pong sent.")

                elif "programs" in data:
                    sender = data.get("source", "Sender")
                    programs = data["programs"]
                    self.log(f"[{sender}] Student:\n{json.dumps(data, indent=2)}")

                    unknown = [p for p in programs if p not in ALLOWED_PROGRAMS]
                    if unknown:
                        error = f"WyseFlow: Unknown programs: {', '.join(unknown)}"
                        error_msg = json.dumps({"error": error})
                        ch.basic_publish(exchange="student_exchange", routing_key="his.error", body=error_msg)
                        self.status_label.setText(f"❌ Unknown program(s): {', '.join(unknown)}")
                    else:
                        self.save_student_data(data)  # Save only if programs are valid
                        self.status_label.setText(f"✅ All programs valid: {', '.join(programs)}")
                else:
                    self.status_label.setText("ℹ️ Unknown message type.")
            except json.JSONDecodeError:
                self.status_label.setText("⚠️ Invalid JSON received.")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        def listen():
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()
            channel.exchange_declare(exchange="student_exchange", exchange_type="topic", durable=True)
            channel.queue_declare(queue="queue_wyseflow", durable=True)
            channel.queue_bind(exchange="student_exchange", queue="queue_wyseflow", routing_key="wyseflow.info")
            channel.queue_bind(exchange="student_exchange", queue="queue_wyseflow", routing_key="wyseflow.ping")
            channel.basic_consume(queue="queue_wyseflow", on_message_callback=callback, auto_ack=False)
            channel.start_consuming()


        thread = threading.Thread(target=listen, daemon=True)
        thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WyseflowUI()
    window.show()
    sys.exit(app.exec())
