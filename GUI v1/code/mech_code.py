"""
This code contains methods to handle mechanical functions other than of recoater, hopper and Z.
i.e. laser window open/ close, emergency stop. The rest of the methods in this class are still in
development stage for version 2 and can be ignored.

JSON RPC protocol over HTTP is used for communicating with moonraker server.
"""

# import necessary libraries
import requests
from ErrorLogging3 import ErrorLogger


# class to handle miscellaneous mechanical functions
class MechCodeHandler:
    """
    Class responsible for handling the mechanical code operations.
    Attributes:
        parent: The parent object.
        api: The API for the octopus board.
        timeout: The timeout value for API requests.
        mech_error_logger: The error logger object.
        consoleWidget: The console widget object.
    Methods:
        moonraker_api_for_script: Sends an API request to Moonraker and receives its response.
        laser_window_open: Opens the laser window.
        laser_window_close: Closes the laser window.
    """
    def __init__(self, parent=None):
        try:
            self.parent = parent
            self.api = self.parent.api # API for octopus board
            self.timeout = self.parent.timeout

            self.api_mutex = parent.api_mutex  # Use the shared mutex
            
            # Initialize the Error Logger
            self.mech_error_logger = ErrorLogger()  # Initialize this first

            # Assign the logger to the parent if a parent is provided
            if self.parent:
                self.mech_error_logger = self.parent.mech_logger

        except Exception as e:
            print(f"E200: Error during initialising variables of MechLogger. \n {e}")

    # function to send API request to moonraker and receive its response
    def moonraker_api_for_script(self):
        self.req = self.request

        # logging part
        self.mech_error_logger.logger.info(f"Sending request to {self.function} with timeout of {self.timeout}s...")
        self.parent.print_to_console({"info":f"Sending request to {self.function} with timeout of {self.timeout}s..."})

        try:
            self.api_mutex.acquire()  # Acquire the mutex
            # send the request
            self.response = requests.post(url=f"http://{self.api}/printer/gcode/script",
                            json=self.req, params = self.req["params"], timeout=self.timeout)
            
            self.response.raise_for_status()

            try:

                # if request is successful
                if self.response.status_code == 200:
                     # log success
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":f"{self.function} request successfully sent."})

                # save response and display it
                response_data = self.response.json()
                self.mech_error_logger.logger.info(f"Response from moonraker: {response_data}")
                self.parent.print_to_console({"info":f"Response from moonraker: {response_data}"})

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message == "ok":
                        # log as success if response = "ok"
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"{self.function} Request successfully executed."})

                        # log as fail if response is not "ok"
                    else:
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error":f"E100: Error while executing {self.function} function"})

                 # in the case that response format is different than what we expected
                else:
                    print("Unexpected response format.")
                    # log error
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({"error":f"E101: Moonraker response in unexpected format \n {self.function} not successful"})
                
            # in case of error in receiving response from moonraker      
            except Exception as e:
                # log error
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error":f"E103: Error while getting/ reading response \n {self.function} not successful"})

        # if the request times out
        except requests.exceptions.Timeout as e:
            # log error
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})

        # to catch the rest of the exceptions                  
        except requests.exceptions.RequestException as e:
            # log error
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"E104: Error while executing {self.function} \n {e}"})

        finally:
            self.api_mutex.release()  # Release the mutex


    def toggle(self):
        self.function = "Toggle recoater Z movement"

        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script":  "toggle_recoat_powder_move_Z"},
                        "id": 7466}
        self.moonraker_api_for_script()   



# function to open laser window
    def laser_window_open(self):
        self.function = "Open Laser Window"

        # create json rpc request
        self.req = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "laser_door_open"

                                    },
                    "id": 7466}

        # log code
        self.mech_error_logger.logger.info(f"Sending Laser Window OPEN request with timeout of {self.timeout}s...")
        self.parent.print_to_console({"info":f"Sending Laser Window OPEN request with timeout of {self.timeout}s..."})


        try:
            # send the request to moonraker
            self.response = requests.post(url=f"http://{self.api}/printer/gcode/script",
                            json=self.req, params = self.req["params"], timeout=self.timeout)
            
            self.response.raise_for_status() # raising error in case of http request error

            self.parent.print_to_console({"info":f"{self.response.text}"})
            try:

                # if request is successful
                if self.response.status_code == 200:
                    self.mech_error_logger.logger.info("Laser Window close request successfully sent.")
                    self.parent.print_to_console({"info":"Laser Window close request successfully sent."})

                response_gotten = self.response.text
                

                # # Extract the response from the incoming message
                if 'ok' in response_gotten:
                    # response of "ok" indicates that function was executed successfully on moonraker side
                    self.mech_error_logger.logger.info("Laser Window OPEN Request successfully executed.")
                    self.parent.print_to_console({"info":"Laser Window OPEN Request successfully executed."})
                    self.mech_error_logger.logger.info("Laser Window OPENED!")
                    self.parent.print_to_console({"info":"Laser Window OPENED!"})
                    self.parent.laserWindowOpen = True
                    self.parent.laserWindowStatus.setStyleSheet("QPushButton{background-color: green;}")
                    self.parent.laserWindowStatus.setText("OPEN")


                else:
                    # when response received is in a different format than the one given in documentation
                    print("Not successful.")
                    self.mech_error_logger.logger.error(f"E101:{self.function} not successful")
                    self.parent.print_to_console({"error":f"E101: {self.function} not successful"})
                
            except Exception as e:
                 # in the case that there is some error while receiving moonraker response
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful \n {e}")
                self.parent.print_to_console({"error":f"E103: Error while getting/ reading response \n {self.function} not successful \n {e}"})


        except requests.exceptions.Timeout as e:
             # in case of timeout error, raise exception and log the error
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        except requests.exceptions.RequestException as e:
            # to catch any other exception and log it
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"E104: Error while executing {self.function} \n {e}"})
   
 # function to close laser window  
    def laser_window_close(self):
        self.function = "Close Laser Window"

        # create json rpc request
        self.req = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "laser_door_close"

                                    },
                    "id": 7466}
        
        # log code
        self.mech_error_logger.logger.info(f"Sending Laser Window CLOSE request with timeout of {self.timeout}s...")
        self.parent.print_to_console({"info":f"Sending Laser Window CLOSE request with timeout of {self.timeout}s..."})

        try:
            # send the request to moonraker
            self.response = requests.post(url=f"http://{self.api}/printer/gcode/script",
                            json=self.req, params = self.req["params"], timeout=self.timeout)
            
            self.response.raise_for_status() # raising error in case of http request error

            self.parent.print_to_console({"info":f"{self.response.text}"})
            try:

                # if request is successful
                if self.response.status_code == 200:
                    self.mech_error_logger.logger.info("Laser Window close request successfully sent.")
                    self.parent.print_to_console({"info":"Laser Window close request successfully sent."})

                response_gotten = self.response.text
                

                # # Extract the response from the incoming message
                if 'ok' in response_gotten:
                    # response of "ok" indicates that function was executed successfully on moonraker side
                    self.mech_error_logger.logger.info("Laser Window CLOSE Request successfully executed.")
                    self.parent.print_to_console({"info":"Laser Window CLOSE Request successfully executed."})
                    self.mech_error_logger.logger.info("Laser Window CLOSED!")
                    self.parent.print_to_console({"info":"Laser Window CLOSED!"})
                    self.parent.laserWindowOpen = False
                    self.parent.laserWindowStatus.setStyleSheet("QPushButton{background-color: red;}")
                    self.parent.laserWindowStatus.setText("CLOSED")


                else:
                    # when response received is in a different format than the one given in documentation
                    print("Not successful.")
                    self.mech_error_logger.logger.error(f"E101:{self.function} not successful")
                    self.parent.print_to_console({"error":f"E101: {self.function} not successful"})
                
            except Exception as e:
                 # in the case that there is some error while receiving moonraker response
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful \n {e}")
                self.parent.print_to_console({"error":f"E103: Error while getting/ reading response \n {self.function} not successful \n {e}"})


        except requests.exceptions.Timeout as e:
             # in case of timeout error, raise exception and log the error
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        except requests.exceptions.RequestException as e:
            # to catch any other exception and log it
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"E104: Error while executing {self.function} \n {e}"})


# function to query end stop status from moonraker
    def send_query_endstops_status(self):
        self.function = "Query Endstop Status"
        query_cmd = {
        "jsonrpc": "2.0",
        "method": "printer.query_endstops.status",
        "id": 3456
    }
    
        try:
            # logging part
            self.mech_error_logger.logger.info(f"Sending request to {self.function} with timeout of {self.timeout}s...")
            self.parent.print_to_console({"info":f"Sending request to {self.function} with timeout of {self.timeout}s..."})

            # send the request
            req = requests.post(url=f"http://{self.api}/printer/query_endstops/status",
                            json=query_cmd, timeout=2)
            
            try:

                 # if request is successful
                if req.status_code == 200:
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":f"{self.function} request successfully sent."})

                # save response and display it
                response_data = req.json()
                self.mech_error_logger.logger.info(f"Response from moonraker: {response_data}")
                self.parent.print_to_console({"info":f"Response from moonraker: {response_data}"})

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message:
                        # log as success if response = "ok"
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"{self.function} Request successfully executed."})

                    # log as fail if response is not "ok"
                    else:
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error":f"E100: Error while executing {self.function} function"})

                # in the case that response format is different than what we expected
                else:
                    print("Unexpected response format.")
                    # log error
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({"error":f"E101: Moonraker response in unexpected format \n {self.function} not successful"})
                
            # in case of error in receiving response from moonraker     
            except Exception as e:
                # log error
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error":f"E103: Error while getting/ reading response \n {self.function} not successful"})

        # if the request times out
        except requests.exceptions.Timeout as e:
            # log error
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        # to catch the rest of the exceptions
        except requests.exceptions.RequestException as e:
            # log error
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"E104: Error while executing {self.function} \n {e}"})

# review the error exceptions after this


# function to restart moonraker server 
    def restart_server(self):
        self.function = "Restart Moonraker server"
        query_cmd = {
        "jsonrpc": "2.0",
        "method": "server.restart",
        "id": 4656
    }
    
        try:
            # send the request
            req = requests.post(url=f"http://{self.api}/server/restart",
                            json=query_cmd, timeout=2)
            try:

                # if request is successful
                if req.status_code == 200:
                    # log success
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":f"{self.function} request successfully sent."})

                # save response and display it
                response_data = req.json()
                self.mech_error_logger.logger.info(f"Response from moonraker: {response_data}")
                self.parent.print_to_console({"info":f"Response from moonraker: {response_data}"})

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message == "ok":
                        # log as success if response = "ok"
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"{self.function} Request successfully executed."})

                    # log as fail if response is not "ok"
                    else:
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error":f"E100: Error while executing {self.function} function"})

                # in the case that response format is different than what we expected
                else:
                    print("Unexpected response format.")
                    # log error
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({"error":f"E101: Moonraker response in unexpected format \n {self.function} not successful"})

            # in case of error in receiving response from moonraker     
            except Exception as e:
                # log error
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error":f"E103: Error while getting/ reading response \n {self.function} not successful"})

        # if the request times out
        except requests.exceptions.Timeout as e:
            # log error
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})

        # to catch the rest of the exceptions                    
        except requests.exceptions.RequestException as e:
            # log error
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"E104: Error while executing {self.function} \n {e}"})

# function to perform emergency stop wrt mechanical firmware
    def emergency_stop(self):
        self.function = "Emergency stop"
        query_cmd = {
        "jsonrpc": "2.0",
        "method": "printer.emergency_stop",
        "id": 4564
        }
    
        try:
            # send the request
            req = requests.post(url=f"http://{self.api}/printer/emergency_stop",
                            json=query_cmd, timeout=2)
            try:

                # if request is successful
                if req.status_code == 200:
                    # log success
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":f"{self.function} request successfully sent."})

                # save response and display it
                response_data = req.json()
                self.mech_error_logger.logger.info(f"Response from moonraker: {response_data}")
                self.parent.print_to_console({"info":f"Response from moonraker: {response_data}"})

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message == "ok":
                        # log as success if response = "ok"
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"{self.function} Request successfully executed."})

                    # log as fail if response is not "ok"
                    else:
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error":f"E100: Error while executing {self.function} function"})

                # in the case that response format is different than what we expected
                else:
                    print("Unexpected response format.")
                    # log error
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({"error":f"E101: Moonraker response in unexpected format \n {self.function} not successful"})
                
             # in case of error in receiving response from moonraker     
            except Exception as e:
                # log error
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error":f"E103: Error while getting/ reading response \n {self.function} not successful"})

        # if the request times out
        except requests.exceptions.Timeout as e:
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        # to catch the rest of the exceptions 
        except requests.exceptions.RequestException as e:
            # log error
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"E104: Error while executing {self.function} \n {e}"})

# function to do a host restart - NOT USED; IGNORE 
    def host_restart(self):
        self.function = "Moonraker Host restart"
        query_cmd = {
        "jsonrpc": "2.0",
        "method": "printer.restart",
        "id": 4894
        }
    
        try:
            req = requests.post(url=f"http://{self.api}/printer/restart",
                            json=query_cmd, timeout=2)
            try:

                if req.status_code == 200:
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":f"> {self.function} request successfully sent."})

                response_data = req.json()
                self.mech_error_logger.logger.info(f"Response from moonraker: {response_data}")
                self.parent.print_to_console({"info":f"> Response from moonraker: {response_data}"})

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message == "ok":
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"> {self.function} Request successfully executed."})

                    else:
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error":f"> E100: Error while executing {self.function} function"})

                else:
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({"error":f"> E101: Moonraker response in unexpected format \n {self.function} not successful"})
                
            except Exception as e:
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error":f"> E103: Error while getting/ reading response \n {self.function} not successful"})


        except requests.exceptions.Timeout as e:
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"> E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        except requests.exceptions.RequestException as e:
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"> E104: Error while executing {self.function} \n {e}"})

# function to do a firmware restart
    def firmware_restart(self):
        self.function = "mechanical Firmware restart"
        query_cmd = {
        "jsonrpc": "2.0",
        "method": "printer.firmware_restart",
        "id": 8463
        }
    
        try:
            # send the request to moonraker
            req = requests.post(url=f"http://{self.api}/printer/firmware_restart",
                            json=query_cmd, timeout=2)
            try:
                # if request is successful
                if req.status_code == 200:
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":f"{self.function} request successfully sent."})

                # decode and log the response received
                response_data = req.json()
                self.mech_error_logger.logger.info(f"Response from moonraker: {response_data}")
                self.parent.print_to_console({"info":f"Response from moonraker: {response_data}"})

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message == "ok":
                         # response of "ok" indicates that function was executed successfully on moonraker side
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"{self.function} Request successfully executed."})

                    else:
                        # any other response indicates that function ran into error while executing on moonraker side
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error":f"E100: Error while executing {self.function} function"})

                else:
                    # when response received is in a different format than the one given in documentation
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({"error":f"E101: Moonraker response in unexpected format \n {self.function} not successful"})
                
            except Exception as e:
                # in the case that there is some error while receiving moonraker response
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error":f"E103: Error while getting/ reading response \n {self.function} not successful"})


        except requests.exceptions.Timeout as e:
             # in case of timeout error, raise exception and log the error
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        except requests.exceptions.RequestException as e:
            # to catch any other exception and log it
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"E104: Error while executing {self.function} \n {e}"})

    def heater_on(self):
        self.function = "Turning on heater"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": "heater_on"},
                        "id": 7466}
        self.moonraker_api_for_script()       

    def heater_off(self):
        self.function = "Turning off heater"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": "heater_off"},
                        "id": 7466}
        self.moonraker_api_for_script()  

    def check_connection(self):
        query_cmd = {
            "jsonrpc": "2.0",
            "method": "printer.info",
            "id": 5445
        }
        
        try:
            # send the request to moonraker
            req = requests.post(url=f"http://{self.api}/printer/info",
                            json=query_cmd, timeout=2)
            try:
             
                # decode and log the response received
                response_data = req.json()


                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message['state'] == "ready":
                         # response of "ok" indicates that function was executed successfully on moonraker side
                        self.parent.klipperConnection = True

                    else:
                        # any other response indicates that function ran into error while executing on moonraker side
                        self.parent.klipperConnection = False

                else:
                    # when response received is in a different format than the one given in documentation
                    self.parent.klipperConnection = False
                
            except Exception as e:
                # in the case that there is some error while receiving moonraker response
                self.parent.klipperConnection = False

        except requests.exceptions.Timeout as e:
             # in case of timeout error, raise exception and log the error
            self.parent.klipperConnection = False
                          
        except requests.exceptions.RequestException as e:
            # to catch any other exception and log it
            self.parent.klipperConnection = False
    

# function to shutdown machine
    def machine_shutdown(self):
        self.function = "Machine shutdown"
        query_cmd = {    "jsonrpc": "2.0",    "method": "machine.shutdown",    "id": 4665}
    
        try:
            # send the request to moonraker
            req = requests.post(url=f"http://{self.api}/machine/shutdown",
                            json=query_cmd, timeout=2)
            try:
                # if request is successful
                if req.status_code == 200:
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":f"{self.function} request successfully sent."})

                # decode and log the response received
                response_data = req.json()

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message == "ok":
                         # response of "ok" indicates that function was executed successfully on moonraker side
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"{self.function} Request successfully executed."})

                    else:
                        # any other response indicates that function ran into error while executing on moonraker side
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error":f"E100: Error while executing {self.function} function"})

                else:
                    # when response received is in a different format than the one given in documentation
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({"error":f"E101: Moonraker response in unexpected format \n {self.function} not successful"})
                
            except Exception as e:
                # in the case that there is some error while receiving moonraker response
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error":f"E103: Error while getting/ reading response \n {self.function} not successful"})


        except requests.exceptions.Timeout as e:
             # in case of timeout error, raise exception and log the error
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error":f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        except requests.exceptions.RequestException as e:
            # to catch any other exception and log it
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error":f"E104: Error while executing {self.function} \n {e}"})

    def pre_layer_new_code(self, cmd):
        script = cmd
        self.function = "pre-layer-gcodes"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": script

                                    },
                    "id": 7464}
        self.moonraker_api_for_script()