from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from pymodbus.client import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ModbusException
import time


class TempWorker(QThread):
    temp_data_signal = pyqtSignal(tuple)
    temp_connection_signal = pyqtSignal(bool)

    def __init__(self, parent=None): # why None?
        try:
            super(TempWorker, self).__init__(parent)
            self.parent = parent
            self.is_running = True
    
            # Define Modbus connection parameters
            self.MODBUS_HOST = '192.168.1.100'  # KRN1000 IP address
            self.MODBUS_PORT = 502              # Default Modbus TCP port
            self.ch1 = self.parent.ch1
            self.ch2 = self.parent.ch2
            self.ch3 = self.parent.ch3
            self.ch4 = self.parent.ch4
            self.ch5 = self.parent.ch5
            self.ch6 = self.parent.ch6
            self.ch7 = self.parent.ch7
            self.ch8 = self.parent.ch8
            self.ch9 = self.parent.ch9
            self.ch10 = self.parent.ch10
            self.ch11 = self.parent.ch11
            self.ch12 = self.parent.ch12
            self.ch13 = self.parent.ch13
            self.ch14 = self.parent.ch14
            self.ch15 = self.parent.ch15
            self.ch16 = self.parent.ch16

            self.temp = {}

            # logger
            

    
        except Exception as e:
            print(f"Temp instance initialization failed \n {e}")
 
    def read_channel_info(self):
        # Create a Modbus TCP client instance
        client = ModbusClient(self.MODBUS_HOST, port=self.MODBUS_PORT)
   
        try:
            # Connect to the Modbus server
            client.connect()
            
            try:
                # Read channel 1 information
                ch1_info = self.read_channel(client, 0x00DC, "CH1")
                self.print_channel_info(ch1_info,(self.ch1,self.parent.ch_1), 'ch1')
 
                # Read channel 2 information
                ch2_info = self.read_channel(client, 0x00E7, "CH2")
                self.print_channel_info(ch2_info, (self.ch2,self.parent.ch_2), 'ch2')
 
                # Read channel 3 information
                ch3_info = self.read_channel(client, 0x00F3, "CH3")
                self.print_channel_info(ch3_info,(self.ch3,self.parent.ch_3),'ch3')
 
                # Read channel 4 information
                ch4_info = self.read_channel(client, 0x00FD, "CH4")
                self.print_channel_info(ch4_info, (self.ch4,self.parent.ch_4),'ch4')
 
                # Read channel 5 information
                ch5_info = self.read_channel(client, 0x0108, "CH5")
                self.print_channel_info(ch5_info, (self.ch5,self.parent.ch_5),'ch5')
 
                # Read channel 6 information
                ch6_info = self.read_channel(client, 0x0113, "CH6")
                self.print_channel_info(ch6_info, (self.ch6,self.parent.ch_6),'ch6')
       
                # Read channel 7 information
                ch7_info = self.read_channel(client, 0x011E, "CH7")
                self.print_channel_info(ch7_info, (self.ch7,self.parent.ch_7),'ch7')
 
                # Read channel 8 information
                ch8_info = self.read_channel(client, 0x0129, "CH8")
                self.print_channel_info(ch8_info, (self.ch8,self.parent.ch_8),'ch8')
 
                # Read channel 9 information
                ch9_info = self.read_channel(client, 0x0134, "CH9")
                self.print_channel_info(ch9_info, (self.ch9,self.parent.ch_9),'ch9')
 
                # Read channel 10 information
                ch10_info = self.read_channel(client, 0x013F, "CH10")
                self.print_channel_info(ch10_info, (self.ch10,self.parent.ch_10),'ch10')
 
                # Read channel 11 information
                ch11_info = self.read_channel(client, 0x014A, "CH11")
                self.print_channel_info(ch11_info, (self.ch11,self.parent.ch_11),'ch11')
 
                # Read channel 12 information
                ch12_info = self.read_channel(client, 0x0155, "CH12")
                self.print_channel_info(ch12_info, (self.ch12,self.parent.ch_12),'ch12')
 
                # Read channel 13 information
                ch13_info = self.read_channel(client, 0x0160, "CH13")
                self.print_channel_info(ch13_info, (self.ch13,self.parent.ch_13),'ch13')
 
                # Read channel 14 information
                ch14_info = self.read_channel(client, 0x016B, "CH14")
                self.print_channel_info(ch14_info, (self.ch14,self.parent.ch_14),'ch14')
 
                # Read channel 15 information
                ch15_info = self.read_channel(client, 0x0176, "CH15")
                self.print_channel_info(ch15_info, (self.ch15,self.parent.ch_15),'ch15')
 
                # Read channel 16 information
                ch16_info = self.read_channel(client, 0x0181, "CH16")
                self.print_channel_info(ch16_info, (self.ch16,self.parent.ch_16),'ch16')

                self.temp_connection_signal.emit(True)
                self.log()
                self.send_temp_list()

            except Exception as e:
                # add console error statement
                self.temp_connection_signal.emit(False)

        except ModbusException:
            self.temp_connection_signal.emit(False)

        finally:
        # Close the connection
            client.close()
 
    #Reads channel information from the Modbus client.
    def read_channel(self,client, base_address, channel_name):
        channel_info = {}
        addresses = {
            f"{channel_name} PV": base_address
        }
 
        for key, address in addresses.items():
            if "User Unit" in key:
                # Read multiple registers for User Unit
                response = client.read_input_registers(address, 4)
                if not response.isError():
                    value = ''.join(chr((reg >> 8) & 0xFF) + chr(reg & 0xFF) for reg in response.registers).strip()
                    channel_info[key] = value
            else:
                response = client.read_input_registers(address, 4)
                if not response.isError():
                    value = response.registers[0]
                    channel_info[key] = value
 
        return channel_info

    # Prints channel information
    def print_channel_info(self,channel_info, widget, ch_name):
        for key, value in channel_info.items():
            if "PV" in key:
                formatted_pv = self.format_pv_value(value, multiply_by=1000)
                self.temp_data_signal.emit((formatted_pv, widget))
                self.temp[ch_name] = str(formatted_pv)
               
            else:
                # print(f"{key}: {value}")
                self.temp_data_signal.emit((value, widget))
                self.temp[ch_name] = str(value)

        # save channel 1 value separately in parent class
        if ch_name == "ch1":
            self.parent.ch1_actual_temp = float(self.temp[ch_name])
            # print(type(self.parent.ch1_actual_temp))

    # Formats the PV value
    def format_pv_value(self,value, multiply_by=1):
        # Always use 4 decimal places
        return f"{(value * multiply_by) / 10000:.4f}"
    
    def run(self):
        # self.is_running = self.parent.tempLoggerIsRunning
        while self.is_running:
            self.read_channel_info()
            time.sleep(0.1)  # sleep for 5 seconds between reads


    def stop(self):
        self.is_running = False


    def log(self):
        temp_list = [self.temp[channel] for channel in self.temp.keys()]
        # send list to logger
        self.parent.csv_logger.log_temp(temp_list)


    def send_temp_list(self):
        temp_list = [self.temp[channel] for channel in self.temp.keys()]
        self.parent.new_temp = temp_list

 
