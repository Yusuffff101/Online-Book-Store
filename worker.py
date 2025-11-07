import boto3
import json
import time
import sqlite3
from botocore.exceptions import ClientError

# --- Configuration ---
SQS_QUEUE_URL = "https://sqs.ap-south-1.amazonaws.com/679500837952/OrderQueue"
SNS_TOPIC_ARN = "arn:aws:sns:ap-south-1:679500837952:LowInventoryAlarmTopic"
DB_NAME = "bookstore_orders.db"
LOW_STOCK_THRESHOLD = 5

# --- Boto3 Clients ---
sqs_client = boto3.client("sqs")
sns_client = boto3.client("sns")

# --- Database Functions ---

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        shipping_address TEXT NOT NULL,
        items_json TEXT NOT NULL,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create Inventory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_id TEXT PRIMARY KEY NOT NULL,
        stock_level INTEGER NOT NULL
    )
    """)
    
    # Populate inventory if it's empty (for demo purposes)
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        print("Inventory is empty. Populating with default stock...")
        default_stock = [
            ("book_987", 6),
            ("book_123", 6),
            ("book_456", 6),
            ("book_789", 7),
            ("book_010", 8),
            ("book_112", 6),
            ("book_314", 6),
            ("book_592", 6),
            ("book_653", 6)
        ]
        cursor.executemany("INSERT INTO inventory (item_id, stock_level) VALUES (?, ?)", default_stock)
        print(f"Populated inventory with {len(default_stock)} items.")
    
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized and tables 'orders' & 'inventory' ensured.")

def save_order_to_db(order_data: dict):
    """Saves a processed order to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Convert items list to a JSON string for storage
    items_json = json.dumps(order_data['items'])
    
    cursor.execute("""
    INSERT INTO orders (user_id, shipping_address, items_json)
    VALUES (?, ?, ?)
    """, (order_data['user_id'], order_data['shipping_address'], items_json))
    
    conn.commit()
    conn.close()

def check_and_update_inventory(item_id: str, quantity: int) -> (bool, int):
    """
    Checks if stock is available and updates it.
    Returns (is_successful, new_stock_level)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Lock the row for this item to prevent race conditions
    # (Note: In a real-world high-concurrency system, you'd use a more robust locking mechanism)
    cursor.execute("SELECT stock_level FROM inventory WHERE item_id = ?", (item_id,))
    result = cursor.fetchone()
    
    if result is None:
        print(f"Inventory check FAILED: Item {item_id} does not exist in inventory.")
        conn.close()
        return False, 0
    
    current_stock = result[0]
    
    if current_stock < quantity:
        print(f"Order FAILED: Item {item_id} is out of stock. (Want {quantity}, have {current_stock})")
        conn.close()
        return False, current_stock
    
    # All good, update the stock
    new_stock = current_stock - quantity
    cursor.execute("UPDATE inventory SET stock_level = ? WHERE item_id = ?", (new_stock, item_id))
    conn.commit()
    conn.close()
    
    print(f"Inventory updated for {item_id}: {current_stock} -> {new_stock}")
    return True, new_stock

def send_low_stock_alarm(item_id: str, stock_level: int):
    """Sends a low stock alarm via SNS."""
    print(f"--- LOW STOCK ALARM! ---")
    print(f"Item {item_id} has reached the low stock threshold ({stock_level}).")
    print("Sending SNS notification...")
    
    subject = "LOW STOCK ALARM"
    message = (
        f"Warning: Inventory for item '{item_id}' is running low.\n"
        f"Current stock level: {stock_level}\n"
        f"Please restock soon."
    )
    
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        print(f"Alarm sent! Message ID: {response['MessageId']}")
    except ClientError as e:
        print(f"Error sending SNS alarm: {e}")

# --- Helper Function for "Heavy Lifting" ---

def process_order(order_data: dict):
    """
    This is where you do all the slow work.
    - Check inventory
    - Process payment
    - Update main database
    - Send confirmation email
    """
    print(f"--- PROCESSING ORDER for user: {order_data['user_id']} ---")
    
    # For this demo, we only process one item per order
    item = order_data['items'][0]
    item_id = item['item_id']
    quantity = item['quantity']

    # 1. Check and update inventory
    success, new_stock = check_and_update_inventory(item_id, quantity)
    
    if not success:
        # If inventory check fails, we stop processing.
        # We still delete the message so we don't retry a bad order.
        # In a real system, you might send this to a DLQ.
        raise Exception(f"Order FAILED: Item {item_id} is out of stock.")

    # 2. Simulate other heavy work (e.g., calling a payment API)
    print("Simulating payment processing...")
    time.sleep(3) 
    
    # 3. Save the successful order to our database
    save_order_to_db(order_data)
    print(f"Order saved to database.")

    # 4. Check if we need to send a low stock alarm
    if new_stock <= LOW_STOCK_THRESHOLD:
        send_low_stock_alarm(item_id, new_stock)
    
    print(f"--- COMPLETED ORDER for user: {order_data['user_id']} ---")


# --- Main Worker Loop ---

# Initialize the database on startup
init_db()

print("Starting Order Worker... Polling for messages.")

while True:
    try:
        # Ask SQS for messages
        response = sqs_client.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10,
            VisibilityTimeout=30 
        )

        if "Messages" in response:
            message = response["Messages"][0]
            receipt_handle = message["ReceiptHandle"]
            message_body = message["Body"]
            order_data = json.loads(message_body)

            try:
                # --- This is the critical part ---
                # 1. Process the order (includes inventory, payment, DB save)
                process_order(order_data)
                
                # 2. If processing is successful, delete the message
                sqs_client.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=receipt_handle
                )
                print(f"Message {message['MessageId']} processed and deleted.\n")

            except Exception as e:
                # If process_order() fails (e.g., out of stock),
                # we still delete the message to prevent an infinite retry loop.
                # A better system would use a Dead Letter Queue (DLQ) here.
                print(f"Error processing order: {e}")
                print(f"Message {message['MessageId']} will be deleted to prevent retry.")
                sqs_client.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=receipt_handle
                )
                
        else:
            # No messages, just loop again
            print("No messages in queue. Waiting...")

    except ClientError as e:
        print(f"Boto3 client error: {e}")
        time.sleep(15)

