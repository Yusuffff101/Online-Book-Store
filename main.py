import boto3
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
# NEW: Import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

# --- Configuration ---
SQS_QUEUE_URL = "https://sqs.ap-south-1.amazonaws.com/679500837952/OrderQueue" # Your correct URL

# --- Pydantic Model ---
class Order(BaseModel):
    user_id: str
    items: list[dict] # e.g., [{"item_id": "book123", "quantity": 1}]
    shipping_address: str

# --- FastAPI App ---
app = FastAPI()

# --- vvv THIS IS THE FIX vvv ---
# We are changing `origins` to `["*"]` to allow all origins.
origins = [
    "*", # This is the wildcard that allows requests from any origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)
# --- ^^^ THIS IS THE FIX ^^^ ---

# Create a Boto3 client for SQS
sqs_client = boto3.client("sqs")

@app.post("/place-order")
async def place_order(order: Order):
    """
    This endpoint receives an order from the user, validates it,
    and sends it to the SQS queue for asynchronous processing.
    """
    print(f"Received order for user: {order.user_id}")
    try:
        message_body = order.model_dump_json()
        response = sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message_body
        )
        print(f"Message sent! Message ID: {response['MessageId']}")
        return {
            "status": "Order Received",
            "message": "Your order is being processed. You will receive a confirmation email shortly."
        }
    except ClientError as e:
        print(f"Error sending message to SQS: {e}")
        raise HTTPException(status_code=500, detail="Could not place order. Please try again later.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# Add a simple root endpoint for testing
@app.get("/")
def read_root():
    return {"message": "Bookstore API is running. Visit /docs to see endpoints."}

