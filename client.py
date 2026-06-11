import socket
import json
import time
from config import HOST, PORT

def submit_task(operation="prime", count=1):
    for i in range(count):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            
            msg = {
                "type": "TASK",
                "task_id": i+1,
                "operation": operation
            }
            s.sendall(json.dumps(msg).encode() + b'\n')
            print(f"✅ Submitted task {i+1} - {operation}")
            s.close()
            time.sleep(0.2)
        except:
            print("❌ Cannot connect to master")

if __name__ == "__main__":
    print("=== Distributed Task Scheduler Client ===")
    print("1. Prime Count")
    print("2. Matrix Multiplication")
    print("3. Monte Carlo Pi")
    
    choice = input("Chọn loại task (1-3): ")
    num = int(input("Số lượng task muốn submit: "))
    
    ops = {1: "prime", 2: "matrix", 3: "pi"}
    submit_task(ops.get(choice, "prime"), num)
