# 📚 Async Bookstore: Cloud-Native Order Processing

This project is a decoupled, asynchronous order management system built with **FastAPI**, **AWS SQS**, and **Python**. It demonstrates a scalable "Producer-Consumer" architecture where high-latency tasks (like payment processing and inventory updates) are offloaded to background workers to keep the user experience seamless.

## 🚀 Features

* **Asynchronous Processing:** Orders are received via a FastAPI endpoint and immediately queued in **AWS SQS**.
* **Background Worker:** A dedicated Python worker polls the queue, simulates "heavy lifting" (like a 3-second payment delay), and updates the local database.
* **Automated Inventory Management:** The system tracks stock levels and provides a fallback mechanism if an item is out of stock.
* **Real-time Alerts:** Integrated with **AWS SNS** to trigger low-stock notifications when inventory hits a threshold of **5**.
* **Data Persistence:** Uses **SQLite** to manage `orders` and `inventory` tables locally.
* **Responsive Frontend:** A modern, single-page application built with **Tailwind CSS** and **Fetch API**.

---

## 🏗️ System Architecture

1.  **The Producer (`main.py`):** A FastAPI server that validates incoming orders and sends them as JSON messages to an SQS queue.
2.  **The Queue (AWS SQS):** Acts as a buffer to handle spikes in traffic without crashing the server.
3.  **The Consumer (`worker.py`):** Processes messages one by one, ensuring data integrity during inventory updates and persisting successful orders.
4.  **The Dashboard (`index.html`):** Provides a clean UI for users to browse books and place orders asynchronously.

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Framework:** FastAPI
* **AWS Services:** SQS (Simple Queue Service), SNS (Simple Notification Service)
* **Database:** SQLite3
* **Frontend:** Tailwind CSS, HTML5, JavaScript
* **Cloud SDK:** Boto3

---

## 📂 Project Structure

* `main.py`: The entry point for the FastAPI backend and SQS producer.
* `worker.py`: The background script that processes orders and manages inventory.
* `view_db.py`: A utility script to monitor the `orders` and `inventory` tables in real-time.
* `index.html`: The frontend client for the bookstore.
* `bookstore_orders.db`: Local database containing system data.

---

## ⚙️ Setup & Installation

### 1. Configure AWS
Ensure your environment is configured with AWS credentials (`~/.aws/credentials`) and that you have created:
* An **SQS Queue** (Standard).
* An **SNS Topic** for notifications.

### 2. Install Dependencies
```bash
pip install fastapi uvicorn boto3
```

### 3. Run the System
1.  **Initialize & Start Worker:**
    ```bash
    python worker.py
    ```
2.  **Launch Backend:**
    ```bash
    uvicorn main:app --reload
    ```
3.  **Open Frontend:** Open `index.html` in any modern browser.

---

## 📊 Database Management
You can use the included `view_db.py` tool to inspect your system's state:
```bash
python view_db.py
```
This will output current stock levels and a history of processed orders with their timestamps.

---

