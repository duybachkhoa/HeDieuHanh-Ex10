import time
import threading
import subprocess
import sys
import os

print("=== Distributed Task Scheduler Test ===")

# Start Master in background (in real test you would run it separately)
print("Please run Master in another terminal first: python3 master.py")

# For demo, we assume master is running

print("\nStarting 3 workers...")
workers = []

for i in range(3):
    try:
        p = subprocess.Popen(['python3', 'worker.py'], 
                           cwd=os.path.dirname(__file__),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        workers.append(p)
        print(f"Worker {i+1} started")
        time.sleep(1)
    except:
        pass

print("\nTest tasks submitted via Master (manually in another terminal or extend test)")

print("\n=== Test completed. Check Master console for logs ===")
print("To stop: kill the processes")
