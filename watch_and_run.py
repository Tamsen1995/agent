import time
import subprocess
import psutil
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def kill_process(process_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            proc.kill()

class MyHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None

    def on_modified(self, event):
        if event.src_path.endswith('agent.py'):
            print('agent.py has been modified. Restarting...')
            if self.process:
                self.process.terminate()
                self.process.wait()
            kill_process('python.exe')  # For Windows
            kill_process('python3')  # For Unix-based systems
            try:
                self.process = subprocess.Popen(['python', 'agent.py'])
            except Exception as e:
                print(f"Error starting agent.py: {e}")

if __name__ == "__main__":
    path = '.'
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    try:
        event_handler.on_modified(type('Event', (), {'src_path': 'agent.py'})())  # Initial run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()