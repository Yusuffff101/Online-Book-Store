import sqlite3
import json

DB_NAME = "bookstore_orders.db"

def print_orders():
    """Prints all orders from the 'orders' table."""
    print("\n--- Orders Table ---")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, user_id, shipping_address, items_json, processed_at FROM orders")
        rows = cursor.fetchall()
        
        if not rows:
            print("No orders found.")
            return
        
        # Print headers
        print(f"{'ID':<4} | {'User ID':<15} | {'Address':<20} | {'Items':<40} | {'Timestamp':<20}")
        print("-" * 100)
        
        # Print rows
        for row in rows:
            order_id, user_id, address, items_json, timestamp = row
            # Prettify the items JSON
            try:
                items = json.loads(items_json)
                items_str = ", ".join([f"{item['item_id']} (x{item['quantity']})" for item in items])
            except:
                items_str = items_json
                
            print(f"{order_id:<4} | {user_id:<15} | {address:<20} | {items_str:<40} | {timestamp:<20}")
            
    except sqlite3.OperationalError:
        print(f"Error: Database file '{DB_NAME}' or table 'orders' not found.")
        print("Please run the worker.py script at least once to create the database.")
    except Exception as e:
        print(f"An unexpected error occurred while reading 'orders': {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def print_inventory():
    """Prints all items from the 'inventory' table."""
    print("\n--- Inventory Table ---")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_id, stock_level FROM inventory ORDER BY item_id")
        rows = cursor.fetchall()
        
        if not rows:
            print("No inventory found.")
            return
            
        # Print headers
        print(f"{'Item ID':<20} | {'Stock Level':<10}")
        print("-" * 33)
        
        # Print rows
        for row in rows:
            item_id, stock = row
            print(f"{item_id:<20} | {stock:<10}")
            
    except sqlite3.OperationalError:
        print(f"Error: Database file '{DB_NAME}' or table 'inventory' not found.")
        print("Please run the worker.py script at least once to create the database.")
    except Exception as e:
        print(f"An unexpected error occurred while reading 'inventory': {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Querying the bookstore database...")
    print_orders()
    print_inventory()
    print("\nQuery complete.")

