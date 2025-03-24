"""
this code sets up a PID control loop for the heating chamber

Author: Vijay 
"""
import requests
from ErrorLogging3 import ErrorLogger
import time
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5.QtCore import QTimer

from threading import Lock

def run_async(func):
    """
    Function decorater to make methods run in a thread
    """
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


class buildChamber:

    def __init__(self, parent=None):
        try:
            # take these variables from parent class
            self.parent = parent
            self.api = self.parent.api # API for octopus board
            self.timeout = self.parent.timeout
            self.stopChamberHeatingFlag = False
            self.pyrometer = self.parent.ch1
            self.pyroLabel = self.parent.pyroReading
            self.PID_SetpointLabel = self.parent.PIDSetpointReading
            self.zoneA = self.parent.zoneA
            self.zoneB = self.parent.zoneB
            self.zoneC = self.parent.zoneC
            self.zoneD = self.parent.zoneD
            self.PID_P = self.parent.PID_P
            self.PID_I = self.parent.PID_I
            self.PID_D = self.parent.PID_D
            self.iClamp = self.parent.iClamp  
            self.overshootDivisor = self.parent.overshootDivisor
            self.PID_Setpoint = self.parent.setChamberTemperatureLineEdit

            self.api_mutex = parent.api_mutex

            self.temperatures = []
            self.outputs = []
            self.time_stamps = []

            self.timer = QTimer()
            self.timer.setSingleShot(False)  # Ensure it repeats

            self.updatePyroReading()
            self.show_plot_window()
            
            # Initialize the Error Logger
            self.mech_error_logger = ErrorLogger()  # Initialize this first

            # Assign the logger to the parent if a parent is provided
            self.mech_error_logger = self.parent.mech_logger

            

        except Exception as e: 
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
            
            self.req.raise_for_status() 
            # print("URL ",self.req)


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
                    # print("Mesage", response_message)
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
            self.mech_error_logger.logger.error(f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful\n Initiating firmware restart")
            self.parent.print_to_console({"error": f"E102 : {self.function} Request to Moonraker Timed out \n {self.function} not successful \n Initiating firmware restart"})
            # print("Ganesh is wrong and right timeput",self.function)
            # self.firmware_restart()
            time.sleep(10)
                          
        except requests.exceptions.RequestException as e:

            if "Bad Gateway" in e:
                self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e} \n Initiating firmware restart")
                self.parent.print_to_console({"error": f"E104: Error while executing {self.function} \n {e} \n Initiating firmware restart"})
                # print("Ganesh is wrong and right",self.function)
                # self.firmware_restart()
                time.sleep(10)
           
            else:
                self.mech_error_logger.logger.error(f"E104: Error while executing {self.function} \n {e}")
                self.parent.print_to_console({"error": f"E104: Error while executing {self.function} \n {e}"})

        finally:
            self.api_mutex.release() # Release the mutex

    def show_plot_window(self):
        # Create a new plot window
        self.plot_widget = pg.PlotWidget(title="PID Control Response")
        self.plot_widget.setLabel('left', 'Temperature / Output')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        
        self.temp_curve = self.plot_widget.plot([], [], pen='r', name='Temperature (°C)')
        self.output_curve = self.plot_widget.plot([], [], pen='g', name='PID Output (%)')

        self.plot_widget.show()

        # Start the timer for updating the plot
        self.timer.start(100)  # Update plot every 100 ms
        self.timer.timeout.connect(self.update_plot)  # Connect timer to update_plot

    def update_plot(self):
        # Update the plot with the latest data
        # print(self.temperatures, self.outputs)
        if self.temperatures and self.outputs:
        # Ensure time_stamps and temperatures have the same length
            min_length_temp = min(len(self.time_stamps), len(self.temperatures))
            min_length_output = min(len(self.time_stamps), len(self.outputs))

            # Truncate arrays to the minimum length
            truncated_time_temp = self.time_stamps[:min_length_temp]
            truncated_temps = self.temperatures[:min_length_temp]

            truncated_time_output = self.time_stamps[:min_length_output]
            truncated_outputs = self.outputs[:min_length_output]

            # Update the curves
            self.temp_curve.setData(truncated_time_temp, truncated_temps)
            self.output_curve.setData(truncated_time_output, np.array(truncated_outputs))

        # Calculate slope and print it
        slope = self.calculate_slope()
        self.parent.temp_slope = slope
        # if self.temperatures and self.outputs:
        #     self.temp_curve.setData(self.time_stamps, self.temperatures)
        #     self.output_curve.setData(self.time_stamps, np.array(self.outputs))  # Scale output to percentage

        #  # Calculate slope and print it
        # slope = self.calculate_slope()
        # # print(f"Current temperature slope: {slope}")
        # self.parent.temp_slope = slope

    def calculate_slope(self):
    # Calculate the slope of the temperature data
        if len(self.temperatures) < 2:
            return 0  # Not enough data to calculate slope

        # Calculate the differences
        temp_diff = self.temperatures[-1] - self.temperatures[-2]
        time_diff = self.time_stamps[-1] - self.time_stamps[-2]
    
        # Handle case where time difference might be zero
        if time_diff == 0:
            return 0  # Avoid division by zero

        slope = temp_diff / time_diff  # Calculate slope
        return slope

    @run_async
    def moonrakerSetZoneTemp(self,zoneA=0,zoneB=0,zoneC=0,zoneD=0):
        if zoneA>1:
            zoneA = 1
        if zoneB>1:
            zoneB = 1
        if zoneC>1:
            zoneC = 1
        if zoneD>1:
            zoneD = 1
        if zoneA<0:
            zoneA = 0
        if zoneB<0:
            zoneB = 0
        if zoneC<0:
            zoneC = 0
        if zoneD<0:
            zoneD = 0

        for zone in [zoneA,zoneB,zoneC,zoneD]:
            if zone is None:
                zone = 0

        self.function = f"Setting Chamber Zones to a= {zoneA}, b= {zoneB}, c= {zoneC}, d= {zoneD}"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"M15 A{zoneA} B{zoneB} C{zoneC} D{zoneD}"},
                        "id": 7466}
        self.moonraker_api_for_script()
        
    
    @run_async
    def moonrakerSetBedTemp(self,channel,bedTemp):
        self.function = f"Setting Bed {channel} Temperature to {bedTemp}"
        self.request = {
                        "jsonrpc": "2.0",
                        "method": "printer.gcode.script",
                        "params": {"script": f"SET_HEATER_TEMPERATURE HEATER={channel} TARGET={bedTemp}"},
                        "id": 7466}
        self.moonraker_api_for_script()

    
    def setBuildChamberPWM(self,PWM):
        PWM = float(PWM)
        self.moonrakerSetZoneTemp(zoneA=(PWM*float(self.zoneA.text())/100),zoneB=(PWM*float(self.zoneB.text())/100),zoneC=(PWM*float(self.zoneC.text())/100),zoneD=(PWM*float(self.zoneD.text())/100))

    
    def setBedTemp(self,setPoint):
        setPoint = float(setPoint)
        self.moonrakerSetBedTemp("heater_bed",setPoint)    
        time.sleep(0.05)   
        self.moonrakerSetBedTemp("bed_heater1",setPoint)    
    
    def cooldownBedTemp(self):
        self.moonrakerSetBedTemp("heater_bed",0)     
        time.sleep(0.05)   
        self.moonrakerSetBedTemp("bed_heater1",0)    
    
    def cooldownBuildChamber(self):
        self.stopChamberHeatingFlag = True
        time.sleep(2)
        self.stopChamberHeatingFlag = False
        self.moonrakerSetZoneTemp(0,0,0,0)
    
    
    def readChamberTemp(self):
        try:
            return round(float(self.pyrometer.text()),2)
        except:
            return 0
    
    @run_async
    def updatePyroReading(self):
        while True:
            try:
                self.pyroLabel.setText(str(round(float(self.pyrometer.text()),2)))
                time.sleep(1)
            except:
                pass
        

    @run_async
    def setChamberPIDTemp(self,setpoint=0):
        self.cooldownBuildChamber()  # Stop any ongoing heating process
        # Initialize PID variables
        if setpoint == 0:
            setpoint = float(self.PID_Setpoint.text())
        integral = 0
        derivative = 0
        last_error = 0
        self.temperatures = []
        self.outputs = []
        self.time_stamps = []
        start_time = time.time()

        # Control loop
        while True:
            try:
                P = float(self.PID_P.text())
                I = float(self.PID_I.text())
                D = float(self.PID_D.text())
                iClamp = float(self.iClamp.text())
                overshootDivisor = float(self.overshootDivisor.text())

                self.temperatures.append(self.readChamberTemp())
                error = setpoint - self.readChamberTemp()

                # PID calculations
                error = setpoint - self.readChamberTemp()
                integral = integral + error     #Improves the rate of convergence
                #integral clamp:
                if (integral*I)>iClamp:
                    integral = iClamp/I
                if (integral*I)<-iClamp:
                    integral = -iClamp/I
                derivative = error - last_error #Dampens the oscillations
                last_error = error 
                output = P * error + I * integral + D * derivative
                if output>1:
                    output = 1
                if output<0:
                    output = 0
                if self.readChamberTemp() >= setpoint: #clamp max allowed temperature
                    output = output/overshootDivisor
                self.setBuildChamberPWM(output)  # Send output to the heater
                self.outputs.append(setpoint)
                self.PID_SetpointLabel.setText(str(round(output * 100, 2)))  # Update label
                self.time_stamps.append(time.time() - start_time)


                time.sleep(0.2)  # Wait for the next cycle (could be adjusted)

                # Check for stop signal
                if self.stopChamberHeatingFlag:
                    self.stopChamberHeatingFlag = False
                    break
            except Exception as e:
                pass

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
                            json=query_cmd, timeout=10)
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
  