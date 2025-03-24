"""
A class that represents a hopper and provides methods to communicate with Klipper regarding hopper functionalities.
Attributes:
    parent: The parent class.
    api: The API endpoint.
    timeout: The timeout for API requests.
    mech_error_logger: The error logger.
    consoleWidget: The console widget.
    slot_distance: The distance of the hopper slot.
    hopper_time_ms: The duration of hopper movement in milliseconds.
Methods:
    __init__(self, parent=None): Initializes the Hopper instance.
    moonraker_api_for_script(self): Sends an API request to Moonraker and receives its response.
    get_LHopper_status(self): Gets the status of the left hopper.
    get_RHopper_status(self): Gets the status of the right hopper.
    open_LHopper(self): Opens the left hopper.
    open_RHopper(self): Opens the right hopper.
    dose(self): Triggers the dosing of the hopper.
this code contains a class called 'Hopper', which has methods to communicate with klipper regarding hopper functionalities

JSON RPC protocol over HTTP is used to communicate with moonraker server

"""

# import requests module to send API requests
import requests

# import logger class
from ErrorLogging3 import ErrorLogger


class Hopper:
    """
    A class representing a hopper.
    Attributes:
        parent (object): The parent object.
        api (str): The API address.
        timeout (int): The timeout duration.
        mech_error_logger (ErrorLogger): The error logger.
        consoleWidget (object): The console widget.
        slot_distance (int): The distance of the hopper slot.
        hopper_time_ms (int): The duration of the hopper operation in milliseconds.
    Methods:
        __init__(self, parent=None): Initializes the Hopper instance.
        moonraker_api_for_script(self): Sends an API request to Moonraker and receives its response.
        get_LHopper_status(self): Gets the status of the left hopper.
        get_RHopper_status(self): Gets the status of the right hopper.
        open_LHopper(self): Opens the left hopper.
        open_RHopper(self): Opens the right hopper.
        dose(self): Triggers the dosing of the hopper.
    """
    def __init__(self, parent=None): # why None?
        try:

            # getting the variables from parent class
            self.parent = parent
            self.api = self.parent.api
            self.timeout = self.parent.timeout

            self.api_mutex = parent.api_mutex  # Use the shared mutex

            # Initialize the Error Logger
            self.mech_error_logger = ErrorLogger()  # Initialize this first

            # Assign the logger to the parent if a parent is provided
            if self.parent:
                self.mech_error_logger = self.parent.mech_logger
           

            # self.slot_distance = self.parent.hopperDistance  
            # self.hopper_time_ms = self.parent.hopperDuration * 1000

        except Exception as e:
            print(f"E200: Error during initialising variables of Hopper instance. \n {e}")


    # function to send API request to moonraker and receive its response
    def moonraker_api_for_script(self):
        self.req = self.request

        # logging part
        self.mech_error_logger.logger.info(f"Sending request to {self.function} with timeout of {self.timeout}s...")
        self.parent.print_to_console({"info":f"Sending request to {self.function} with timeout of {self.timeout}s..."})

        try:
            self.api_mutex.acquire()  # Acquire the mutex
            # send the request
            self.req = requests.post(url=f"http://{self.api}/printer/gcode/script",
                            json=self.req, params = self.req["params"], timeout=self.timeout)
            
            self.req.raise_for_status() # do i need this

            try:

                # if request is successful
                if self.req.status_code == 200:
                    # log success
                    self.mech_error_logger.logger.info(f"{self.function} request successfully sent.")
                    self.parent.print_to_console({"info":f"{self.function} request successfully sent."})

                # save response and display it
                response_data = self.req.json()
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


    def get_LHopper_status(self):
        pass

    def get_RHopper_status(self):
        pass

    # function to open left hopper
    def open_LHopper(self):
     
        # get the parameters from parent class
        self.slot_distance = self.parent.hopperDistanceLEFT  
        self.hopper_time_ms = self.parent.hopperDurationLEFT * 1000

        # change color of status label to green
        self.parent.lHopperStatus.setStyleSheet("QLabel {background-color: green;}")

        #TO DO -  update status on GUI

        # creating the 3 line message and sending it successively
        self.function = f"Moving left hopper motors {self.slot_distance}mm - stage 1"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"FORCE_MOVE stepper=stepper_x distance={self.slot_distance} velocity=30"},
                        "id": 7466}
        self.moonraker_api_for_script()

        self.function = f"Dwell for {self.hopper_time_ms}"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"G4 P{self.hopper_time_ms}"},
                        "id": 7467}
        self.moonraker_api_for_script()

        self.function = "Moving left hopper motors - stage 2"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"FORCE_MOVE stepper=stepper_x distance=-{str(self.slot_distance + 1)} velocity=30"},
                        "id": 7468}
        self.moonraker_api_for_script()
        
        # change the status label back to red
        self.parent.lHopperStatus.setStyleSheet("QLabel {background-color: red;}")



    # function to open right hopper
    def open_RHopper(self):

        # get the parameters from parent class
        self.slot_distance = self.parent.hopperDistanceRIGHT  
        self.hopper_time_ms = self.parent.hopperDurationRIGHT * 1000

        # change status label to green
        self.parent.rHopperStatus.setStyleSheet("QLabel {background-color: green;}")

        # creating the 3 line message and sending it successively
        self.function = f"Moving right hopper motor {self.slot_distance}mm - stage 1"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"FORCE_MOVE stepper=dual_carriage distance={self.slot_distance} velocity=30"},
                        "id": 7466}
        self.moonraker_api_for_script()

        self.function = f"Dwell for {self.hopper_time_ms}"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"G4 P{self.hopper_time_ms}"},
                        "id": 7467}
        self.moonraker_api_for_script()

        self.function = "Moving right hopper motors - stage 2"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"FORCE_MOVE stepper=dual_carriage distance=-{str(self.slot_distance + 1)} velocity=30"},
                        "id": 7468}
        self.moonraker_api_for_script()

        # change status label back to red
        self.parent.rHopperStatus.setStyleSheet("QLabel {background-color: red;}")

    # function to trigger dosing of hopper
    def dose(self):
        # take the choice from parent class
        self.hopper_choice = self.parent.hopper_choice

        # if left hopper is chosen
        if self.hopper_choice == "left":
            self.open_LHopper()

        # if right hopper is chosen
        elif self.hopper_choice == "right":
            self.open_RHopper()
            
        # in case both hoppers are chosen (during actual printing)   
        else:
            # open both left and right hopper one after the other
            self.open_LHopper()
            self.open_RHopper()

