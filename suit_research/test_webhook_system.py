#!/usr/bin/env python3
"""Test script for the webhook delivery system."""

import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Dict, Any

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Test webhook receiver server
app = FastAPI(title="Webhook Test Receiver")

# Store received webhooks for verification
received_webhooks = []


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 webhook signature."""
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature[7:]  # Remove 'sha256=' prefix
    return hmac.compare_digest(expected_signature, received_signature)


@app.post("/webhook")
async def receive_webhook(request):
    """Test webhook endpoint that receives and validates webhooks."""
    try:
        # Get request data
        payload = await request.body()
        headers = dict(request.headers)
        
        # Parse JSON payload
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid JSON payload"}
            )
        
        # Verify signature if present
        signature_valid = False
        if 'x-webhook-signature-256' in headers:
            signature = headers['x-webhook-signature-256']
            # In a real scenario, you'd get the secret from your webhook config
            test_secret = "test_webhook_secret_123"
            signature_valid = verify_webhook_signature(
                payload.decode('utf-8'), 
                signature, 
                test_secret
            )
        
        # Store the received webhook
        webhook_data = {
            'id': str(uuid.uuid4()),
            'received_at': datetime.utcnow().isoformat(),
            'headers': headers,
            'payload': data,
            'signature_valid': signature_valid,
            'raw_payload': payload.decode('utf-8')
        }
        
        received_webhooks.append(webhook_data)
        
        print(f"\n=== Webhook Received ===")
        print(f"Event Type: {data.get('event_type', 'unknown')}")
        print(f"Timestamp: {data.get('timestamp', 'unknown')}")
        print(f"Signature Valid: {signature_valid}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Payload: {json.dumps(data, indent=2)}")
        print(f"========================\n")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Webhook received successfully",
                "signature_valid": signature_valid,
                "event_type": data.get('event_type')
            }
        )
    
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


@app.get("/webhooks")
async def list_received_webhooks():
    """List all received webhooks for testing."""
    return {
        "total_received": len(received_webhooks),
        "webhooks": received_webhooks
    }


@app.delete("/webhooks")
async def clear_received_webhooks():
    """Clear all received webhooks."""
    global received_webhooks
    count = len(received_webhooks)
    received_webhooks = []
    return {"message": f"Cleared {count} received webhooks"}


def test_webhook_signature():
    """Test the webhook signature generation and verification."""
    print("\n=== Testing Webhook Signature ===")
    
    # Test data
    payload = json.dumps({
        "event_type": "test.event",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"test": "data", "number": 123}
    }, separators=(',', ':'))
    
    secret = "test_webhook_secret_123"
    
    # Generate signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    full_signature = f"sha256={signature}"
    
    print(f"Payload: {payload}")
    print(f"Secret: {secret}")
    print(f"Signature: {full_signature}")
    
    # Verify signature
    is_valid = verify_webhook_signature(payload, full_signature, secret)
    print(f"Signature Valid: {is_valid}")
    
    # Test with wrong secret
    is_invalid = verify_webhook_signature(payload, full_signature, "wrong_secret")
    print(f"Wrong Secret Valid: {is_invalid}")
    
    print("=================================\n")
    
    return is_valid and not is_invalid


async def test_webhook_delivery():
    """Test webhook delivery by sending a test webhook."""
    print("\n=== Testing Webhook Delivery ===")
    
    # Test data
    event_data = {
        "user_id": 12345,
        "username": "testuser",
        "email": "test@example.com",
        "created_at": datetime.utcnow().isoformat()
    }
    
    payload_data = {
        "event_type": "user.created",
        "timestamp": datetime.utcnow().isoformat(),
        "data": event_data
    }
    
    payload = json.dumps(payload_data, separators=(',', ':'))
    secret = "test_webhook_secret_123"
    
    # Generate signature
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SocialSuit-Webhook/1.0",
        "X-Webhook-Event": "user.created",
        "X-Webhook-Delivery": str(uuid.uuid4()),
        "X-Webhook-Timestamp": str(int(datetime.utcnow().timestamp())),
        "X-Webhook-Signature-256": f"sha256={signature}"
    }
    
    try:
        # Send webhook to test receiver
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/webhook",
                headers=headers,
                content=payload
            )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook delivery successful!")
            return True
        else:
            print("❌ Webhook delivery failed!")
            return False
    
    except Exception as e:
        print(f"❌ Error sending webhook: {str(e)}")
        return False
    
    finally:
        print("=================================\n")


async def run_tests():
    """Run all webhook tests."""
    print("🚀 Starting Webhook System Tests\n")
    
    # Test signature generation/verification
    signature_test = test_webhook_signature()
    
    if signature_test:
        print("✅ Signature test passed")
    else:
        print("❌ Signature test failed")
        return
    
    # Wait a bit for the test server to be ready
    await asyncio.sleep(2)
    
    # Test webhook delivery
    delivery_test = await test_webhook_delivery()
    
    if delivery_test:
        print("✅ Delivery test passed")
    else:
        print("❌ Delivery test failed")
    
    print("\n🎉 Webhook system tests completed!")
    print("\nTo view received webhooks, visit: http://localhost:8001/webhooks")
    print("To clear received webhooks, send DELETE to: http://localhost:8001/webhooks")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run tests
        asyncio.run(run_tests())
    else:
        # Start test webhook receiver server
        print("🎯 Starting Webhook Test Receiver Server")
        print("📡 Listening on http://localhost:8001")
        print("📋 Webhook endpoint: http://localhost:8001/webhook")
        print("📊 View received webhooks: http://localhost:8001/webhooks")
        print("\nTo run tests, use: python test_webhook_system.py test")
        print("\nPress Ctrl+C to stop the server\n")
        
        uvicorn.run(
            "test_webhook_system:app",
            host="0.0.0.0",
            port=8001,
            reload=False
        )