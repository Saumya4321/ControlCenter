from threading import Lock

# Shared mutex for API synchronization
api_mutex = Lock()



from PyQt5.QtCore import QThread, pyqtSignal
import time
import json
import socket

class CycleThread(QThread):
    # define as global variables so that it can be accessed by main thread 
    progress = pyqtSignal(int)
    
    # signals for updating ui components through main thread
    update_count_signal = pyqtSignal(str)
   

    def __init__(self, function, update_console_signal, update_z_signal, *args, **kwargs):
        super().__init__()
        self.function = function  # Function to run in thread
        self.update_console_signal = update_console_signal  # Use the signal from the main class
        self.update_z_signal = update_z_signal
        self.args = args  # Positional arguments
        self.kwargs = kwargs  # Keyword arguments
        self.is_running = False
       


    def run(self):
        self.is_running = True
        self.function(*self.args, **self.kwargs)
        self.progress.emit(100)  # Emit signal to terminal when task is complete
        self.is_running = False
      


class PrintThread(QThread):
    # define as global variables so that it can be accessed by main thread 
    progress = pyqtSignal(int)
    
    # signals for updating ui components through main thread
    update_layer_signal = pyqtSignal(str)

    # update elapsed time signal
    update_elapsed_time = pyqtSignal(tuple)

    def __init__(self, function, update_console_signal, update_z_signal,*args, **kwargs):
        super().__init__()
        self.function = function  # Function to run in thread
        self.update_console_signal = update_console_signal  # Use the signal from the main class
        self.update_z_signal = update_z_signal
        self.args = args  # Positional arguments
        self.kwargs = kwargs  # Keyword arguments
        self.is_running = False
        


    def run(self):
        self.is_running = True
        self.function(*self.args, **self.kwargs)
        self.progress.emit(100)  # Emit signal to terminal when task is complete
        self.is_running = False




class NetworkChecker(QThread):
    status_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        self.parent = parent
        super().__init__(parent)
        self.is_running = True

    def run(self):
        while self.is_running:
            status = self.check_network()
            self.status_changed.emit(status)
            time.sleep(5)  # Check every 5 seconds

    def check_network(self):
        self.is_running = self.parent.networkCheckIsRunning
        self.parent.check_klipper_connection()
        if self.parent.klipperConnection:
            return True  # or False based on the actual network status
        else:
            return False
        
    def stop(self):
        self.is_running = False


class ScancardConnection(QThread):
    status_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        self.parent = parent
        super().__init__(parent)
        self.is_running = True
        self.HOST = "localhost"
        self.PORT = 50000

    def run(self):
        # self.is_running = self.parent.scancardCheckIsRunning
        while self.is_running:
            self.check_connection()
            time.sleep(5)  # Check every 5 seconds
        
    def stop(self):
        self.is_running = False

    def check_connection(self):
        request = {
                 "sid": 0,
                 "cmd": "get_working_status",
             }
        try:
            json_string = json.dumps(request)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.HOST, self.PORT))

            try:
                sock.sendall(json_string.encode())
                sock.settimeout(2)
        
                try:
                    ret = sock.recv(1024) 
                except socket.timeout:
                    self.status_changed.emit(False)
                    
                if ret:
                    try:    
           
                        ret_str = ret.decode('GB2312')
                        ret_json = json.loads(ret_str)
                        formatted_json = json.dumps(ret_json, indent=4)  
                        connectionStatus = formatted_json[60]

                        if connectionStatus == "0":
                            self.status_changed.emit(True)
                        elif connectionStatus == "1":
                            self.status_changed.emit(True)
                        elif connectionStatus == "2":
                            self.status_changed.emit(True)
                        elif connectionStatus == "3":
                            self.status_changed.emit(True)
                        else:
                            self.status_changed.emit(False)

                    except Exception as e:
                        self.status_changed.emit(False)

            except Exception as e:
                self.status_changed.emit(False)
                
        except Exception as e:
            self.status_changed.emit(False)

class ConfigEditorWorker(QThread):

    def __init__(self, config_editor_instance,parent=None):
        super().__init__(parent)
        self.config_editor_instance = config_editor_instance
        self.parent = parent

    def run(self):
        try:
            # Move the main function's operations here
            self.config_editor_instance.main_function()
            self.parent.print_to_console("Task completed successfully.")
        except Exception as e:
            self.parent.print_to_console(f"An error occurred: {str(e)}")