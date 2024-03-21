from serial import Serial
import time

device = Serial(port='COM3', baudrate=9600, timeout=.1) 
# def write_read(x): 
	#    device.write(bytes(x, 'utf-8')) 
	#    time.sleep(0.05) 
	#    data = device.readline() 
	#    return data 

# while True: 
# 	   num = input("Enter a number: ") # Taking input from user 
# 	   value = write_read(num) 
# 	   print(value) # printing the value 
# time.sleep(3)
device.write(bytes("RELX10\n", 'ascii'))
while True:
    x = str(device.readline())
    
    if x != "b\'\'":
        print(x)
    