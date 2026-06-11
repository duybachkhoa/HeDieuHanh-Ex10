import socket
import json
import threading
import time
import queue
from collections import defaultdict
import sys

class Master:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.workers = {}  # worker_id: {'socket': conn, 'load': 0, 'last_heartbeat': time.time(), 'alive': True}
        self.task_queue = queue.Queue()
        self.tasks = {}  # task_id: task_info
        self.worker_lock = threading.Lock()
        self.task_lock = threading.Lock()
        self.next_task_id = 1
        self.running = True

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(10)
        print(f"Master started on {self.host}:{self.port}")

        # Heartbeat monitor
        threading.Thread(target=self.heartbeat_monitor, daemon=True).start()

        # Scheduler
        threading.Thread(target=self.scheduler, daemon=True).start()

        while self.running:
            try:
                conn, addr = server.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except:
                break

    def handle_client(self, conn, addr):
        try:
            while True:
                data = conn.recv(4096).decode('utf-8')
                if not data:
                    break
                messages = data.split('\n')
                for msg in messages:
                    if msg.strip():
                        self.process_message(json.loads(msg), conn)
        except:
            pass
        finally:
            conn.close()

    def process_message(self, msg, conn):
        msg_type = msg.get('type')

        if msg_type == 'REGISTER':
            worker_id = msg.get('worker_id')
            with self.worker_lock:
                self.workers[worker_id] = {
                    'socket': conn,
                    'load': 0,
                    'last_heartbeat': time.time(),
                    'alive': True
                }
            print(f"Worker {worker_id} registered")
            self.send_response(conn, {"type": "REGISTERED", "status": "success"})

        elif msg_type == 'HEARTBEAT':
            worker_id = msg.get('worker_id')
            with self.worker_lock:
                if worker_id in self.workers:
                    self.workers[worker_id]['last_heartbeat'] = time.time()

        elif msg_type == 'TASK':
            task = {
                'task_id': msg.get('task_id', self.next_task_id),
                'operation': msg.get('operation'),
                'input': msg.get('input'),
                'status': 'READY',
                'assigned_worker': None
            }
            self.next_task_id += 1
            self.task_queue.put(task)
            print(f"New task {task['task_id']} received: {task['operation']}")

        elif msg_type == 'RESULT':
            task_id = msg.get('task_id')
            result = msg.get('output')
            with self.task_lock:
                if task_id in self.tasks:
                    self.tasks[task_id]['status'] = 'COMPLETED'
                    self.tasks[task_id]['result'] = result
            print(f"Task {task_id} completed with result: {result[:100]}...")

    def heartbeat_monitor(self):
        while self.running:
            time.sleep(2)
            current_time = time.time()
            with self.worker_lock:
                for wid, info in list(self.workers.items()):
                    if current_time - info['last_heartbeat'] > 6:
                        if info['alive']:
                            print(f"Worker {wid} failed!")
                            info['alive'] = False
                            self.reassign_tasks(wid)

    def reassign_tasks(self, failed_worker):
        with self.task_lock:
            for tid, task in self.tasks.items():
                if task.get('assigned_worker') == failed_worker and task['status'] == 'RUNNING':
                    task['status'] = 'READY'
                    task['assigned_worker'] = None
                    self.task_queue.put(task)
                    print(f"Task {tid} reassigned due to worker failure")

    def scheduler(self):
        while self.running:
            if not self.task_queue.empty():
                task = self.task_queue.get()
                worker_id = self.select_worker()
                if worker_id:
                    self.assign_task(task, worker_id)
                else:
                    self.task_queue.put(task)  # put back if no worker
            time.sleep(0.1)

    def select_worker(self, policy='least_loaded'):
        with self.worker_lock:
            alive_workers = {wid: info for wid, info in self.workers.items() if info['alive']}
            if not alive_workers:
                return None

            if policy == 'least_loaded':
                return min(alive_workers.items(), key=lambda x: x[1]['load'])[0]
            elif policy == 'round_robin':
                # Simple round robin
                return list(alive_workers.keys())[0]
            else:
                return list(alive_workers.keys())[0]

    def assign_task(self, task, worker_id):
        with self.worker_lock:
            if worker_id in self.workers and self.workers[worker_id]['alive']:
                task['status'] = 'RUNNING'
                task['assigned_worker'] = worker_id
                self.tasks[task['task_id']] = task
                self.workers[worker_id]['load'] += 1

                msg = {
                    "type": "TASK",
                    "task_id": task['task_id'],
                    "operation": task['operation'],
                    "input": task['input']
                }
                try:
                    self.workers[worker_id]['socket'].send((json.dumps(msg) + '\n').encode('utf-8'))
                    print(f"Task {task['task_id']} assigned to worker {worker_id}")
                except:
                    self.workers[worker_id]['alive'] = False

    def send_response(self, conn, response):
        try:
            conn.send((json.dumps(response) + '\n').encode('utf-8'))
        except:
            pass

if __name__ == "__main__":
    master = Master()
    master.start()
