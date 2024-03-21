import serial
import serial.tools.list_ports as port_list
import time

ports = list(port_list.comports())
for p in ports:
    print (p)

serialPort = serial.Serial(
    port="COM3", baudrate=9600
    # , bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE
)
time.sleep(2)
print("DONE SLEEPING")

# serialPort.write("RELX50\n".encode())
data = "RELX50".encode('ascii')
list(data)
serialPort.write(data)

serialString = ""  # Used to hold data coming over UART
while 1:
    # Wait until there is data waiting in the serial buffer
    if serialPort.in_waiting > 0:

        # Read data out of the buffer until a carraige return / new line is found
        serialString = serialPort.readline()

        # Print the contents of the serial data
        try:
            print(serialString.decode("Ascii"))
        except:
            pass