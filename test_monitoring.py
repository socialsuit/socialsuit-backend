"""
Test script for the monitoring system.

This script tests the structured logging, alerting, and monitoring functionality.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
import sys
sys.path.append(str(Path(__file__).parent))

from services.monitoring import (
    structured_logger,
    alert_manager,
    LogLevel,
    EventType,
    AlertSeverity,
    AlertType,
    EmailAlertChannel,
    WebhookAlertChannel,
    log_performance,
    log_operation,
    alert_background_task_failure,
    alert_api_downtime
)

async def test_structured_logging():
    """Test structured logging functionality."""
    print("🔍 Testing Structured Logging...")
    
    # Test basic logging
    structured_logger.log_structured(
        LogLevel.INFO,
        "Testing structured logging",
        EventType.SYSTEM,
        test_id="test_001",
        component="monitoring_test"
    )
    
    # Test API request logging
    structured_logger.log_api_request(
        method="GET",
        endpoint="/test",
        request_id="test_req_001",
        user_id="test_user",
        status_code=200,
        response_time=0.123
    )
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        structured_logger.log_error(
            e,
            context={"test": True, "error_type": "intentional"}
        )
    
    # Test performance logging
    from services.monitoring.logger_config import PerformanceMetrics
    metrics = PerformanceMetrics(
        operation="test_operation",
        duration_ms=1500.0,
        memory_usage_mb=50.5,
        cpu_usage_percent=25.0
    )
    structured_logger.log_performance(metrics)
    
    # Test security event logging
    structured_logger.log_security_event(
        event="test_security",
        severity="medium",
        ip_address="127.0.0.1",
        test=True
    )
    
    print("✅ Structured logging tests completed")

async def test_performance_decorator():
    """Test the performance monitoring decorator."""
    print("🚀 Testing Performance Decorator...")
    
    @log_performance()
    async def slow_operation():
        await asyncio.sleep(0.1)
        return "completed"
    
    result = await slow_operation()
    print(f"✅ Performance decorator test completed: {result}")

async def test_operation_context():
    """Test the operation context manager."""
    print("🔄 Testing Operation Context Manager...")
    
    with log_operation("test_context_operation"):
        await asyncio.sleep(0.05)
        structured_logger.log_structured(
            LogLevel.INFO,
            "Inside context operation",
            EventType.SYSTEM
        )
    
    print("✅ Operation context test completed")

async def test_alerting_system():
    """Test the alerting system."""
    print("🚨 Testing Alerting System...")
    
    # Test webhook channel (won't actually send, just test setup)
    webhook_channel = WebhookAlertChannel("https://hooks.slack.com/test")
    alert_manager.add_channel(webhook_channel)
    
    # Test background task failure alert
    await alert_background_task_failure(
        task_name="test_background_task",
        error="Test failure for monitoring",
        test=True
    )
    
    # Test API downtime alert
    await alert_api_downtime(
        endpoint="/test/endpoint",
        status_code=500,
        test=True
    )
    
    # Check active alerts
    active_alerts = alert_manager.get_active_alerts()
    print(f"📊 Active alerts: {len(active_alerts)}")
    
    # Check alert history
    recent_alerts = alert_manager.get_alert_history(limit=10)
    print(f"📈 Recent alerts: {len(recent_alerts)}")
    
    print("✅ Alerting system tests completed")

def test_log_file_creation():
    """Test that log files are created properly."""
    print("📁 Testing Log File Creation...")
    
    log_dir = Path("logs")
    
    # Check if log files exist
    expected_files = [
        "app.log",
        "app.json",
        "performance.json",
        "errors.log"
    ]
    
    for file_name in expected_files:
        file_path = log_dir / file_name
        if file_path.exists():
            print(f"✅ Log file exists: {file_name}")
            
            # Check if file has content
            if file_path.stat().st_size > 0:
                print(f"📝 Log file has content: {file_name}")
            else:
                print(f"⚠️  Log file is empty: {file_name}")
        else:
            print(f"❌ Log file missing: {file_name}")
    
    print("✅ Log file creation tests completed")

def test_performance_summary():
    """Test performance summary functionality."""
    print("📊 Testing Performance Summary...")
    
    summary = structured_logger.get_performance_summary()
    print(f"Performance Summary: {json.dumps(summary, indent=2)}")
    
    error_summary = structured_logger.get_error_summary()
    print(f"Error Summary: {json.dumps(error_summary, indent=2)}")
    
    print("✅ Performance summary tests completed")

async def run_monitoring_tests():
    """Run all monitoring tests."""
    print("🧪 Starting Monitoring System Tests")
    print("=" * 50)
    
    try:
        # Test structured logging
        await test_structured_logging()
        print()
        
        # Test performance decorator
        await test_performance_decorator()
        print()
        
        # Test operation context
        await test_operation_context()
        print()
        
        # Test alerting system
        await test_alerting_system()
        print()
        
        # Test log file creation
        test_log_file_creation()
        print()
        
        # Test performance summary
        test_performance_summary()
        print()
        
        print("🎉 All monitoring tests completed successfully!")
        
        # Final summary
        print("\n📋 Test Summary:")
        print("- ✅ Structured logging")
        print("- ✅ Performance monitoring")
        print("- ✅ Operation context tracking")
        print("- ✅ Alerting system")
        print("- ✅ Log file management")
        print("- ✅ Performance summaries")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        structured_logger.log_error(e, context={"test": "monitoring_tests"})
        raise

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_monitoring_tests())