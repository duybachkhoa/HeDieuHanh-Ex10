import socket
import json
import threading
import time
import random
import sys

def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def count_primes(n):
    return sum(1 for i in range(n+1) if is_prime(i))

def monte_carlo_pi(samples):
    inside = 0
    for _ in range(samples):
        x, y = random.random(), random.random()
        if x*x + y*y <= 1:
            inside += 1
    return 4 * inside / samples

class Worker:
    def __init__(self, master_host='127.0.0.1', master_port=5555, worker_id=None):
        self.master_host = master_host
        self.master_port = master_port
        self.worker_id = worker_id or random.randint(100, 999)
        self.socket = None
        self.running = True

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.master_host, self.master_port))
        print(f"Worker {self.worker_id} connected to master")

        # Register
        reg_msg = {"type": "REGISTER", "worker_id": self.worker_id}
        self.socket.send((json.dumps(reg_msg) + '\n').encode('utf-8'))

        # Heartbeat thread
        threading.Thread(target=self.send_heartbeat, daemon=True).start()

    def send_heartbeat(self):
        while self.running:
            try:
                hb = {"type": "HEARTBEAT", "worker_id": self.worker_id}
                self.socket.send((json.dumps(hb) + '\n').encode('utf-8'))
            except:
                break
            time.sleep(2)

    def run(self):
        self.connect()
        try:
            while self.running:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                messages = data.split('\n')
                for msg in messages:
                    if msg.strip():
                        self.process_task(json.loads(msg))
        except Exception as e:
            print(f"Worker error: {e}")
        finally:
            self.running = False

    def process_task(self, msg):
        if msg.get('type') != 'TASK':
            return

        task_id = msg.get('task_id')
        operation = msg.get('operation')
        input_data = msg.get('input')

        print(f"Worker {self.worker_id} processing task {task_id}: {operation}")

        if operation == 'prime_count':
            result = count_primes(int(input_data))
        elif operation == 'monte_carlo_pi':
            result = monte_carlo_pi(int(input_data))
        else:
            result = "Unknown task"

        result_msg = {
            "type": "RESULT",
            "task_id": task_id,
            "output": str(result)
        }
        try:
            self.socket.send((json.dumps(result_msg) + '\n').encode('utf-8'))
            print(f"Task {task_id} completed")
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        wid = int(sys.argv[1])
        worker = Worker(worker_id=wid)
    else:
        worker = Worker()
    worker.run()
