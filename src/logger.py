import os
from datetime import datetime
import atexit

class Logger:
    messages = []
    socket_manager = None

    def __init__(self):
        pass

    def __del__(self):
        pass

    @staticmethod
    def set_socket_manager(socket_manager):
        Logger.socket_manager = socket_manager

    @staticmethod
    def init_logger(socket_manager):
        Logger.set_socket_manager(socket_manager)
        atexit.register(Logger.save_logs)

    @staticmethod
    def save_logs():
        Logger.log("Saving logs - Final message count: " + str(len(Logger.messages)))
        os.makedirs('logs', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'logs/log_{timestamp}.txt'
        with open(filename, 'w') as f:
            for message in Logger.messages:
                f.write(f'{message}\n')

    @staticmethod
    def log_no_send(message):
        Logger.messages.append(str(message))
        print(message)

    @staticmethod
    def log(message):
        Logger.log_no_send(message)
        Logger.socket_manager.send_message(str(message))


    @staticmethod
    def log_error(message):
        Logger.log_no_send(message)
        Logger.socket_manager.send_error(str(message))
    
    @staticmethod
    def get_messages(count: int = 0):
        if count > 0:
            return Logger.messages[-count:]
        else:
            return Logger.messages

    @staticmethod
    def clear_messages():
        Logger.messages = []