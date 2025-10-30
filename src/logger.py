import os
from datetime import datetime

from socket_manager import Socket_Manager

class Logger:
    instances = []
    def __init__(self ):
        self.messages = []
        Logger.instances.append(self)

    def __del__(self):
        Logger.save_logs()

    @staticmethod
    def save_logs():
        for instance in Logger.instances:
            instance.log("Saving logs - Final message count: " + str(len(instance.messages)))
            os.makedirs('logs', exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'logs/log_{timestamp}.txt'
            with open(filename, 'w') as f:
                for message in instance.messages:
                    f.write(f'{message}\n')

    def log(self, message: str):
        Socket_Manager.send_message(message)

    def log_error(self, message: str):
        Socket_Manager.send_error(message)
    
    @staticmethod
    def global_log(message: str):
        Logger.instances[0].log(message)

    def get_messages(self, count: int = 0):
        if count > 0:
            return self.messages[-count:]
        else:
            return self.messages

    def clear_messages(self):
        self.messages = []