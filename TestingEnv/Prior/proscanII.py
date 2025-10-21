from serial import Serial
import sys
import threading
from queue import Queue
import json
import os         
import time

# Set up serial connection
device = Serial(port='COM3', baudrate=9600, timeout=.1) 
print('Connected to COM3')

def send_to_station(command):
    """Send a command to the station via serial"""
    device.write(bytes(f"{command}\r\n", 'ascii'))
    print(f'Sent command: {command}')

def listen_serial():
    """Continuously listen for and display serial data"""
    while True:
        try:
            reading = device.readline()
            if reading:
                # Decode and strip whitespace for cleaner display
                decoded = reading.decode('ascii', errors='ignore').strip()
                if decoded:
                    print(f'Received: {decoded}')
        except Exception as e:
            print(f'Error reading serial: {e}')

# Start the listening thread
thread = threading.Thread(target=listen_serial)
thread.daemon = True
thread.start()

# Give the serial connection time to establish
time.sleep(1)
print('Serial listener started. Type commands to send (or exit to quit):')
print('-' * 50)

# Main command loop
try:
    while True:
        # Get user input
        command = input('> ').strip()
        
        # Check for exit command
        if command.lower() in ['exit', 'quit', 'q']:
            print('Exiting...')
            break
        
        # Send non-empty commands
        if command:
            send_to_station(command)
        
except KeyboardInterrupt:
    print('\nInterrupted by user')
except Exception as e:
    print(f'Error: {e}')
finally:
    # Close the serial connection
    if device.is_open:
        device.close()
        print('Serial connection closed')