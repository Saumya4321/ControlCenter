"""
this code enables GUI to communicate with moonraker wrt recoater and roller operations

JSON RPC protocol over HTTP is used for communicating with moonraker server.
"""
import requests
from ErrorLogging3 import ErrorLogger

class Recoater:
    """
    Class representing a recoater.
    Args:
        parent (object): The parent object.
    Attributes:
        parent (object): The parent object.
        api (str): The API for the octopus board.
        timeout (int): The timeout value.
        mech_error_logger (ErrorLogger): The error logger.
        consoleWidget (object): The console widget.
    Methods:
        moonraker_api_for_script: Sends an API request through JSON RPC over HTTP.
        set_recoater_speed: Sets the recoater speed.
        recoater_go_right: Directs the recoater to move towards the right.
        recoater_go_left: Directs the recoater to move towards the left.
        recoater_stop: Stops the recoater.
        start_recoater_testing: Starts the recoater testing process.
        home_recoater: Homes the recoater.
        set_roller_speed: Sets the roller speed.
        roller_cw: Makes the roller move clockwise.
        roller_ccw: Makes the roller move counter-clockwise.
        roller_stop: Stops the roller.
    """
    def __init__(self, parent=None):
        try:
            # take these variables from parent class
            self.parent = parent
            self.api = self.parent.api # API for octopus board
            self.timeout = self.parent.timeout

            self.api_mutex = parent.api_mutex  # Use the shared mutex
        

            # Initialize the Error Logger
            self.mech_error_logger = ErrorLogger()  # Initialize this first

            # Assign the logger to the parent if a parent is provided
            if self.parent:
                self.mech_error_logger = self.parent.mech_logger
            

        except Exception as e: # no error logging here . is that ok?
            print(f"E200: Error during initialising variables of Recoater instance. \n {e}")

# function for sending API request through JSON RPC over HTTP
    def moonraker_api_for_script(self):
        self.req = self.request

        # logging part
        self.mech_error_logger.logger.info(f"Sending request to {self.function} with timeout of {self.timeout}s...")
        self.parent.print_to_console({"info": f"Sending request to {self.function} with timeout of {self.timeout}s..."})

        try:

            self.api_mutex.acquire()  # Acquire the mutex

            # send the request to moonraker
            self.req = requests.post(url=f"http://{self.api}/printer/gcode/script",
                            json=self.req, params = self.req["params"], timeout=self.timeout)
            
            self.req.raise_for_status() # do i need this


            try:
                
                # if request is successful
                if self.req.status_code == 200:
                    # log the success
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":  f"{self.function} request successfully sent."})

                # decode and log the response from moonraker
                response_data = self.req.json()
                self.mech_error_logger.logger.info(f"Response from moonraker: {response_data}")
                self.parent.print_to_console({"info": f"Response from moonraker: {response_data}"})

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message == "ok":
                        # moonraker sends "ok" if function sent was executed successfully
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"{self.function} Request successfully executed."})

                    else:
                        # in case function wasn't executed successfully by moonraker
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error": f"E100: Error while executing {self.function} function"})

                else:
                    # if moonraker response is in a format different to the one given in Feeltek documentation
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({ "error": f"E101: Moonraker response in unexpected format \n {self.function} not successful"})
                
            except Exception as e:
                # error while getting response from moonraker
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error": f"E103: Error while getting/ reading response \n {self.function} not successful"})


        except requests.exceptions.Timeout as e:
            # in case request times out
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error": f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        except requests.exceptions.RequestException as e:
            # to catch any other exceptions
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error": f"E104: Error while executing {self.function} \n {e}"})

        finally:
            self.api_mutex.release()  # Release the mutex


# function to set recoater speed - must be run first before calling recoater right/ left
    # def set_recoater_speed(self):
    #     # take pwm value from parent class
    #     self.recoater_pwm = self.parent.recoater_pwm
    #     self.function = "Setting recoater speed"
    #     self.request = {
    #                     "jsonrpc": "2.0",
    #                     "method": "printer.gcode.script",
    #                     "params": {
    #                                 "script": f"SET_PIN PIN=recoater_pwm VALUE={self.recoater_pwm}"

    #                                 },
    #                 "id": 7466}
    #     self.moonraker_api_for_script()

# function to direct recoater to move towards the right
    def recoater_go_right(self):
        self.function = "Recoater go RIGHT"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "recoater_go_right"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

# function to direct recoater to move towards the left
    def recoater_go_left(self): # same for homing also
        self.function = "Recoater go LEFT"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "recoater_go_left"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

# function to stop recoater
    def recoater_stop(self):
        self.function = "Stop recoater"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "recoater_stop"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

# function to start recoater testing - NOT USED; IGNORE
    def start_recoater_testing(self):
        self.mech_error_logger.logger.info("Starting Recoater testing process...")
        self.parent.print_to_console(self.consoleWidget, "Starting Recoater testing process...")

        self.function = "Recoater go left"
        my_pwm = 0
        my_value = 0
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "recoater_go_left"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()
        
        self.function =""
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "G4 P5000"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

        self.function = "Recoater go right"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "recoater_go_right"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

        self.function = ""
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "G4 P5000"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()


# function to home recoater
    def home_recoater(self):
        self.recoater_go_left()


# function to set roller speed
    def set_roller_speed(self):
        # take pwm value from parent class
        self.roller_pwm = self.parent.roller_pwm
        self.function = "Setting roller speed"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": f"SET_PIN PIN=roller_pwm VALUE={self.roller_pwm}"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

# function to make roller go clockwise
    def roller_cw(self):
        self.function = "Roller move CLOCKWISE"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "roller_cw"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

# function to make roller go counter-clockwise
    def roller_ccw(self):
        self.function = "Roller move COUNTER-CLOCKWISE"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "roller_ccw"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

# function to stop roller
    def roller_stop(self):
        self.function = "Stop roller"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "roller_stop"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

