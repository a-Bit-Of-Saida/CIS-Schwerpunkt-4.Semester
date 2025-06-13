import sys
import json
import pika
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer


class HISWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HIS – Student Data Entry")
        self.setMinimumSize(600, 300)

        self.status = {"wyseflow": False, "peregos": False}
        self.last_pongs = {"wyseflow": False, "peregos": False}

        self.allowed_programs = {
            "Computer Science": "01/10/2022",
            "Economics": "15/03/2023",
            "AI": "01/04/2024"
        }

        self.program_credits = {k: 3 for k in self.allowed_programs}
        self.students = {}

        self.setup_ui()
        self.setup_rabbit_listener()
        self.setup_error_listener()
        self.setup_heartbeat()

    def setup_ui(self):
        layout = QVBoxLayout()
        font_label = QFont("Segoe UI", 10)
        font_input = QFont("Segoe UI", 10)

        self.name_input = QLineEdit()
        self.id_input = QLineEdit()
        self.programs_input = QLineEdit()

        for text, widget in [
            ("Name", self.name_input),
            ("Matrikelnummer", self.id_input),
            ("Study Programs (comma-separated)", self.programs_input)
        ]:
            label = QLabel(text)
            label.setFont(font_label)
            widget.setFont(font_input)
            widget.setFixedHeight(30)
            layout.addWidget(label)
            layout.addWidget(widget)

        self.add_btn = QPushButton("Send")
        self.add_btn.setFixedHeight(30)
        self.add_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.add_btn.clicked.connect(self.add_and_send_student)

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        self.connection_status = QLabel("")
        self.connection_status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        layout.addWidget(self.add_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(self.connection_status)
        self.setLayout(layout)

    def setup_rabbit_listener(self):
        def callback(ch, method, properties, body):
            data = json.loads(body.decode())
            sender = data.get("source")
            if sender in self.last_pongs:
                self.last_pongs[sender] = True

        def listen():
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()
            channel.exchange_declare(exchange="student_exchange", exchange_type="topic")
            result = channel.queue_declare('', exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="his.pong")
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            channel.start_consuming()

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def setup_error_listener(self):
        def callback(ch, method, properties, body):
            data = json.loads(body.decode())
            error_message = data.get("error", "Unknown error")
            QMessageBox.critical(self, "Validation Error", error_message)

        def listen():
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()
            channel.exchange_declare(exchange="student_exchange", exchange_type="topic")
            result = channel.queue_declare('', exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange="student_exchange", queue=queue_name, routing_key="his.error")
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            channel.start_consuming()

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def setup_heartbeat(self):
        def heartbeat():
            for service in ["wyseflow", "peregos"]:
                self.last_pongs[service] = False
                self.send_to_rabbitmq(f"{service}.ping", {"type": "ping", "target": service})
            QTimer.singleShot(2000, self.evaluate_heartbeat)

        self.timer = QTimer()
        self.timer.timeout.connect(heartbeat)
        self.timer.start(5000)

    def evaluate_heartbeat(self):
        self.status = self.last_pongs.copy()
        status_text = f"🩺 Peregos: {'✅' if self.status['peregos'] else '❌'} | WyseFlow: {'✅' if self.status['wyseflow'] else '❌'}"
        self.connection_status.setText(status_text)

        # Sende-Button bleibt IMMER aktiv!

    def add_and_send_student(self):
        try:
            if not all(self.status.values()):
                offline = [s.capitalize() for s, ok in self.status.items() if not ok]
                QMessageBox.critical(
                    self,
                    "Service is offline",
                    f"❌ The following services are currently unavaliable:\n\n{', '.join(offline)}\n\n"
                    "Please try again later."
                )
                return

            name = self.name_input.text().strip()
            student_id = self.id_input.text().strip()
            requested_programs = [p.strip() for p in self.programs_input.text().split(",") if p.strip()]

            if not name.replace(" ", "").isalpha():
                raise ValueError("Name is only allowed to have characters.")
            if not student_id.isdigit():
                raise ValueError("Matrikelnumber has to be a number.")
            if not requested_programs:
                raise ValueError("Choose at least one stduy program.")

            for p in requested_programs:
                if p not in self.allowed_programs:
                    raise ValueError(f"Unknown study program: {p}")

            key = (name, student_id)
            if key not in self.students:
                self.students[key] = requested_programs
            else:
                for p in requested_programs:
                    if p not in self.students[key]:
                        self.students[key].append(p)

            final_programs = self.students[key]
            start_map = {p: self.allowed_programs[p] for p in final_programs}
            credit_map = {p: self.program_credits[p] for p in final_programs}
            total_credits = sum(credit_map.values())

            student = {
                "name": name,
                "martikelnumber": int(student_id),
                "programs": final_programs,
                "startDates": start_map,
                "creditsPerProgram": credit_map,
                "totalCredits": total_credits
            }

            self.send_to_rabbitmq("peregos.info", {
                "name": name,
                "martikelnumber": int(student_id),
                "programs": final_programs
            })
            self.send_to_rabbitmq("wyseflow.info", student)

            self.status_label.setText("✅ Student succsessfully sent.")
            self.clear_inputs()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def clear_inputs(self):
        self.name_input.clear()
        self.id_input.clear()
        self.programs_input.clear()

    def send_to_rabbitmq(self, routing_key, payload):
        connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
        channel = connection.channel()
        channel.exchange_declare(exchange="student_exchange", exchange_type="topic")
        channel.basic_publish(exchange="student_exchange", routing_key=routing_key, body=json.dumps(payload))
        connection.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HISWindow()
    window.show()
    sys.exit(app.exec())
