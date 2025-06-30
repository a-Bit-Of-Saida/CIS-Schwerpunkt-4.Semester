# 📘 Student Management System with RabbitMQ

This project simulates a university student lifecycle system using three components that communicate via RabbitMQ:

- **HIS** – student data entry
- **Peregos** – Students requests for examination office
- **Wyseflow** – Thesis application

---

## ⚙️ Requirements

- 🐍 Python 3.10 or higher
- 📦 Installed packages: `pika`, `PyQt6`
- 🐇 A running RabbitMQ server on `localhost` (default port: `5672`)

> 💡 The RabbitMQ Management UI (optional) can be accessed at:  
> http://localhost:15672  
> Default credentials: `guest` / `guest`

---

## ▶️ Starting the System

1. **Start RabbitMQ**  
   Make sure RabbitMQ is running on your machine.

2. **Start all 3 components in separate terminals:**

```bash
# Terminal 1 – HIS Interface
python his.py

# Terminal 2 – Peregos Interface
python peregos.py

# Terminal 3 – Wyseflow Interface
python wyseflow.py
