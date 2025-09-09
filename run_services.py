import subprocess
import sys
import time
import os
import signal
import threading

def run_service(service_name, command, cwd):
    """Run a service in a subprocess."""
    print(f"Starting {service_name}...")
    process = subprocess.Popen(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Create a thread to read and print output
    def read_output():
        for line in process.stdout:
            print(f"[{service_name}] {line.strip()}")
    
    thread = threading.Thread(target=read_output)
    thread.daemon = True
    thread.start()
    
    return process

def main():
    """Main function to run services."""
    print("=== Starting Services ===\n")
    
    # Define services to run
    services = [
        {
            "name": "Social Suit",
            "command": "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000",
            "cwd": "C:\\Users\\hhp\\social_suit\\social-suit"
        },
        {
            "name": "Sparkr",
            "command": "python -m uvicorn app.main:app --host 0.0.0.0 --port 8001",
            "cwd": "C:\\Users\\hhp\\social_suit\\sparkr"
        }
    ]
    
    # Start services
    processes = []
    for service in services:
        process = run_service(service["name"], service["command"], service["cwd"])
        processes.append((service["name"], process))
    
    print("\nServices started. Press Ctrl+C to stop.")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        for name, process in processes:
            print(f"Stopping {name}...")
            if sys.platform == 'win32':
                process.terminate()
            else:
                os.kill(process.pid, signal.SIGTERM)
        
        # Wait for processes to terminate
        for name, process in processes:
            process.wait()
            print(f"{name} stopped.")
        
        print("All services stopped.")

if __name__ == "__main__":
    main()