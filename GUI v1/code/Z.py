import requests
from ErrorLogging3 import ErrorLogger
import json

class Z:
    """
    This class represents the Z object.
    Attributes:
        parent: The parent object.
        api: The API endpoint.
        timeout: The timeout value.
    Methods:
        __init__(self, parent=None): Initializes the Z object.
        moonraker_api_for_script(self): Sends a request to the Moonraker API for script execution.
        z_stage_down(self): Executes the Z Stage down script.
        z_stage_up(self): Executes the Lift Z Stage UP script.
        move_z_down(self): Moves the Z axis down.
        move_z_up(self): Moves the Z axis up.
        get_z_position(self): Retrieves the current Z axis position.
        home_z(self): Homing the Z axis.
        check_for_z_homing(self): Checks if the Z axis is homed.
    """
    def __init__(self, parent=None):
        try:
            self.parent = parent
            self.api = self.parent.api
            self.timeout = self.parent.timeout

            # self.api_mutex = parent.api_mutex  # Use the shared mutex
            

            # Initialize the Error Logger
            self.mech_error_logger = ErrorLogger()  # Initialize this first

            # Assign the logger to the parent if a parent is provided
            if self.parent:
                self.mech_error_logger = self.parent.mech_logger
            

        except Exception as e:
            print(f"E200: Error during initialising variables of Z instance. \n {e}")


    def moonraker_api_for_script(self):
        self.req = self.request

        self.mech_error_logger.logger.info(f"Sending request to {self.function} with timeout of {self.timeout}s...")
        self.parent.print_to_console({"info": f"Sending request to {self.function} with timeout of {self.timeout}s..."})

        try:

            # self.api_mutex.acquire()  # Acquire the mutex

            self.req = requests.post(url=f"http://{self.api}/printer/gcode/script",
                            json=self.req, params = self.req["params"], timeout=self.timeout)
            
            self.req.raise_for_status() # do i need this

            try:

                if self.req.status_code == 200:
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":  f"{self.function} request successfully sent."})

                response_data = self.req.json()
                self.mech_error_logger.logger.info(f"Response from moonraker: {response_data}")
                self.parent.print_to_console({"info": f"Response from moonraker: {response_data}"})

                # Extract the response from the incoming message
                if 'result' in response_data:
                    response_message = response_data['result']
                    if response_message == "ok":
                        self.mech_error_logger.logger.info(f"{self.function} Request successfully executed.")
                        self.parent.print_to_console({"info":f"{self.function} Request successfully executed."})

                    else:
                        self.mech_error_logger.logger.error(f"E100: Error while executing {self.function} function")
                        self.parent.print_to_console({"error": f"E100: Error while executing {self.function} function"})

                else:
                    self.mech_error_logger.logger.error(f"E101: Moonraker response in unexpected format \n {self.function} not successful")
                    self.parent.print_to_console({ "error": f"E101: Moonraker response in unexpected format \n {self.function} not successful"})
                
            except Exception as e:
                self.mech_error_logger.logger.error(f"E103: Error while getting/ reading response \n {self.function} not successful")
                self.parent.print_to_console({"error": f"E103: Error while getting/ reading response \n {self.function} not successful"})

        except requests.exceptions.Timeout as e:
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful")
            self.parent.print_to_console({"error": f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful"})
                          
        except requests.exceptions.RequestException as e:
            self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
            self.parent.print_to_console({"error": f"E104: Error while executing {self.function} \n {e}"})

        # finally:
        #     self.api_mutex.release()  # Release the mutex

    def z_stage_down(self):
        self.function = "Z Stage down"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "undock"

                                    },
                    "id": 7463}
        self.moonraker_api_for_script()


    def z_stage_up(self):
        self.function = "Lift Z Stage UP"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "dock"

                                    },
                    "id": 7464}
        self.moonraker_api_for_script()

    def move_z_down(self, distance):
        self.function = f"sending command G91"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "G91",
 
                                    },
                    "id": 7461}
        self.moonraker_api_for_script()
        self.function = f"Moving Z axis down by {distance} mm"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": f"G0 Z{distance}"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()
        self.function = "Getting Z position"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": f"M114"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()
        self.parent.update_Z_position() 

    def move_z_up(self, distance):
        self.function = f"sending command G91"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "G91",
 
                                    },
                    "id": 7461}
        self.moonraker_api_for_script()
        self.function = f"Moving Z axis up by {distance} mm"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": f"G0 Z-{distance}"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()
        self.function = "Getting Z position"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": f"M114"

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()
    
    def home_z(self):
        self.timeout = 360
        self.function = "Homing Z axis - command 1/4"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "G28 Z0",

                                    },
                    "id": 7461}
        self.moonraker_api_for_script()

        self.function = "Homing Z axis - command 2/4"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "G90",
 
                                    },
                    "id": 7461}
        self.moonraker_api_for_script()

        self.function = "Homing Z axis - command 3/4"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "G0 Z0",

                                    },
                    "id": 7466}
        self.moonraker_api_for_script()

        self.function = "Homing Z axis - command 4/4"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {
                                    "script": "G91",
 
                                    },
                    "id": 7461}
        self.moonraker_api_for_script()
        # self.parent.update_Z_position()

        self.timeout = self.parent.timeout
        

    def z_force_up(self, offset):
        self.function = f"Moving Z by {offset}"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"FORCE_MOVE stepper=stepper_z distance={offset} velocity=2"},
                        "id": 7466}
        self.moonraker_api_for_script()

    def z_force_down(self, offset):
        self.function = f"Moving Z by {offset}"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"FORCE_MOVE stepper=stepper_z distance=-{str(offset + 1)} velocity=2"},
                        "id": 7466}
        self.moonraker_api_for_script()

    def get_Z_position(self):
        url = "http://192.168.0.231/printer/objects/query?gcode_move&toolhead&extruder=target,temperature"
 
        try:
            self.mech_error_logger.logger.info("Sending Z position query to printer...")
            response = requests.get(url)
 
            # Check if the request was successful
            if response.status_code == 200:
                # Parse the JSON response
                self.mech_error_logger.logger.info("Request successful. Parsing JSON response...")
                response_json = response.json()
               
                # Extract the Z position from the response
                z_position = response_json["result"]["status"]["gcode_move"]["position"][2]
                self.mech_error_logger.logger.info(f"Z position: {z_position}")
               
                # print("Z position:", z_position)
                return z_position

               
            else:
                print("Failed to query printer object status. HTTP Status Code:", response.status_code)
                self.mech_error_logger.logger.error(f"Failed to query printer object status. HTTP Status Code: {response.status_code}")

        except Exception as e:
            print(f"Failed to connect to the printer: {e}")
            self.mech_error_logger.logger.error(f"Failed to connect to the printer: {e}")