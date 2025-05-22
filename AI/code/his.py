import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import pika
from datetime import datetime


class HISWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HIS – Student Data Entry")
        self.setMinimumSize(800, 600)

        self.students = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        font_label = QFont("Segoe UI", 10)
        font_input = QFont("Segoe UI", 10)

        # Form fields
        self.name_input = QLineEdit()
        self.id_input = QLineEdit()
        self.programs_input = QLineEdit()
        self.start_dates_input = QLineEdit()
        self.credits_input = QLineEdit()

        form_layout = QVBoxLayout()
        for text, widget in [
            ("Name", self.name_input),
            ("Matrikelnummer", self.id_input),
            ("Study Programs (comma-separated)", self.programs_input),
            ("Start Dates (comma-separated, DD/MM/YY or YYYY)", self.start_dates_input),
            ("Credits per Program (comma-separated)", self.credits_input),
        ]:
            label = QLabel(text)
            label.setFont(font_label)
            widget.setFont(font_input)
            widget.setFixedHeight(30)
            form_layout.addWidget(label)
            form_layout.addWidget(widget)

        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("+ Hinzufügen")
        send_btn = QPushButton("✔ Alle senden")
        remove_btn = QPushButton("❌ Entfernen")
        for btn in (add_btn, send_btn, remove_btn):
            btn.setFixedHeight(30)
            btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        button_layout.addWidget(add_btn)
        button_layout.addWidget(send_btn)
        button_layout.addWidget(remove_btn)

        add_btn.clicked.connect(self.add_student)
        send_btn.clicked.connect(self.send_all_students)
        remove_btn.clicked.connect(self.remove_selected)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Matrikelnummer"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Status
        self.status = QLabel("")
        self.status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        # Add to layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.status)

        self.setLayout(layout)

    def add_student(self):
        try:
            name = self.name_input.text().strip()
            student_id = self.id_input.text().strip()
            programs = [p.strip() for p in self.programs_input.text().split(",") if p.strip()]
            start_dates = [d.strip() for d in self.start_dates_input.text().split(",") if d.strip()]
            credits_raw = [c.strip() for c in self.credits_input.text().split(",") if c.strip()]

            if not name.replace(" ", "").isalpha():
                raise ValueError("Name darf nur Buchstaben enthalten.")
            if not student_id.isdigit():
                raise ValueError("Matrikelnummer muss eine Ganzzahl sein.")
            if len(programs) != len(start_dates) or len(programs) != len(credits_raw):
                raise ValueError("Alle Felder müssen gleich viele Einträge enthalten.")

            try:
                datetime_objects = []
                for d in start_dates:
                    try:
                        datetime_objects.append(datetime.strptime(d, "%d/%m/%y"))
                    except ValueError:
                        datetime_objects.append(datetime.strptime(d, "%d/%m/%Y"))
            except ValueError:
                raise ValueError("Ungültiges Datumsformat. Verwende DD/MM/YY oder DD/MM/YYYY")

            try:
                credits = [int(c) for c in credits_raw]
            except ValueError:
                raise ValueError("Credits müssen Ganzzahlen sein.")

            start_map = {prog: start_dates[i] for i, prog in enumerate(programs)}
            credit_map = {prog: credits[i] for i, prog in enumerate(programs)}
            total_credits = sum(credits)

            student = {
                "name": name,
                "Martikelnummer": int(student_id),
                "programs": programs,
                "startDates": start_map,
                "creditsPerProgram": credit_map,
                "totalCredits": total_credits
            }

            self.students.append(student)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(student_id))
            self.status.setText("✅ Student hinzugefügt")
            self.clear_inputs()

        except ValueError as e:
            QMessageBox.critical(self, "Fehler", str(e))

    def clear_inputs(self):
        self.name_input.clear()
        self.id_input.clear()
        self.programs_input.clear()
        self.start_dates_input.clear()
        self.credits_input.clear()

    def remove_selected(self):
        selected = self.table.selectionModel().selectedRows()
        for index in sorted(selected, reverse=True):
            del self.students[index.row()]
            self.table.removeRow(index.row())
        self.status.setText("❌ Student(en) entfernt")

    def send_all_students(self):
        try:
            for student in self.students:
                self.send_to_rabbitmq("peregos.info", {
                    "name": student["name"],
                    "Martikelnummer": student["Martikelnummer"],
                    "programs": student["programs"]
                })
                self.send_to_rabbitmq("wyseflow.info", student)

            self.status.setText(f"✅ {len(self.students)} Studierende gesendet")
            self.students.clear()
            self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Senden", str(e))

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
