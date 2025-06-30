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

class PeregosUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Peregos - Message Monitor")
        self.setMinimumSize(700, 400)

        self.data_file = "received_students_peregos.json"
        self.received_data = {}
        

        self.program_log = QTextEdit()
        self.program_log.setReadOnly(True)
        self.program_log.setFont(QFont("Consolas", 10))

        self.status_label = QLabel("🔄 Waiting for messages...")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.setup_ui()
        self.load_existing_data()
        self.start_rabbitmq_listener()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📥 Received Student Data:"))
        layout.addWidget(self.program_log)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def log_message(self, msg: str):
        self.program_log.append(msg)

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
                        self.log_message(f"⚠️ Skipped entry '{key}': no 'data' field.")
                        continue

                    name = student.get("name")
                    number = student.get("ID")
                    programs = student.get("programs")

                    if name and number and programs:
                        self.log_message(f"[Startup] {key}:\n{json.dumps(student, indent=2)}")
                    else:
                        self.log_message(f"⚠️ Incomplete data in entry '{key}'.")
            except Exception as e:
                print(f"⚠️ Failed to load students:", e)



    def start_rabbitmq_listener(self):
        def callback(ch, method, properties, body):
            message = body.decode()
            try:
                data = json.loads(message)
                if data.get("type") == "ping":
                    pong = json.dumps({"type": "pong", "source": "peregos"})
                    ch.basic_publish(exchange="student_exchange", routing_key="his.pong", body=pong)
                    self.status_label.setText("✅ Ping received, Pong sent.")

                elif "programs" in data:
                    sender = data.get("source", "Sender")
                    programs = data["programs"]
                    self.log_message(f"[{sender}] Student:\n{json.dumps(data, indent=2)}")

                    unknown = [p for p in programs if p not in ALLOWED_PROGRAMS]
                    if unknown:
                        error = f"Peregos: Unknown programs: {', '.join(unknown)}"
                        error_msg = json.dumps({"error": error})
                        ch.basic_publish(exchange="student_exchange", routing_key="his.error", body=error_msg)
                        self.status_label.setText(f"❌ Unknown program(s): {', '.join(unknown)}")
                    else:
                        self.save_student_data(data)
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
            channel.queue_declare(queue="queue_peregos", durable=True)
            channel.queue_bind(exchange="student_exchange", queue="queue_peregos", routing_key="peregos.info")
            channel.queue_bind(exchange="student_exchange", queue="queue_peregos", routing_key="peregos.ping")
            channel.basic_consume(queue="queue_peregos", on_message_callback=callback, auto_ack=False)
            channel.start_consuming()


        thread = threading.Thread(target=listen, daemon=True)
        thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PeregosUI()
    window.show()
    sys.exit(app.exec())
