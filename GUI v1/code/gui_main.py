
# pyqt libraries
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QStackedWidget, QLineEdit, QFileDialog,QListWidget, QLabel
from PyQt5 import uic
from PyQt5.QtCore import QTimer, pyqtSignal

# for console
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtCore import QThread, QCoreApplication

# for graph
import pyqtgraph as pg

# importing custom modules
from ErrorLogging3 import ErrorLogger
from hopper import Hopper
from buildChamber import buildChamber
from temp import TempWorker
from Z import Z
from recoater import Recoater
from mech_code import MechCodeHandler
from api_test import Scancard
from LaserErrorLogging import LaserErrorLogger
from thread import CycleThread, PrintThread, NetworkChecker, ScancardConnection, ConfigEditorWorker
from update_printer_cfg import ConfigEditor
from CSVLogger import CSVLogger
from graph import Graph
from thread import api_mutex


# other python libraries
import time
import sys


# The main GUI class, which defines our application window with all of it's functionalities
class gui(QMainWindow):
    # signal to update console
    update_console_signal = pyqtSignal(dict)
    # signal to update Z
    update_z_signal = pyqtSignal(str)

    def __init__(self, main):
        super(gui,self).__init__()

        # Set up the UI
        uic.loadUi("../ui files/gui.ui",self)
        self.setWindowTitle("Dashboard")

        
        self.init_default_values()
        self.init_graph()
        self.init_class_instances()
        self.init_ui_elements()
        self.setup_graph()
        self.init_threads()

        #################################################################
        # fetching initial PWM and power values and displaying it
        # self.update_pwm_power_display()
        
        # load the qt application
        self.show()

    def init_default_values(self):
        
        # scancard default parameters 
        self.layer_number = 0
        self.markSpeed = 3000
        self.jumpSpeed = 5000
        self.jumpDelay =100
        self.laserOnDelay = 100
        self.polygonDelay = 100
        self.laserOffDelay = 100
        self.polygonKillerTime = 100
        self.laserfreq = 30
        self.current = 100
        self.firstPulseKillerLength = 100
        self.pulseWidth = 100
        self.firstPulseWidth = 100
        self.incrementStep = 100
        self.api_mutex = api_mutex
        

        # temporary variables
        self.rSpeed = 80  # rpm
        self.roSpeed = 80 # rpm
        self.num = 0
        self.laserWindowOpen = True
        self.slot_distance = 0
        self.ch1_actual_temp = 0


        # mechanical default values
        self.hopperDistanceLEFT = 10 # mm
        self.hopperDurationLEFT = 0.1 #s
        self.hopperDistanceRIGHT = 15 # mm
        self.hopperDurationRIGHT = 0.1 #s
        self.recoater_speed = 100
        self.roller_speed = 80
        self.hopper_choice = "left"
        self.Z_position = 0
        self.Z_initial = 0
        self.count = 0
        self.api = "192.168.0.231"  # API for octopus
        self.timeout = 5 # timeout for klipper requests
        self.z_offset_sum = 0 # mm
        self.zOffset = 0 # mm
        self.heatingTime_value = 1
        self.heatingPower_value = 20
        self.pwmCycleTime_value = 0.3
        self.homed = False
        self.klipperConnection = False
        self.scancardConnection = False
        self.tempLoggerIsRunning = True
        self.networkCheckIsRunning = True
        self.scancardCheckIsRunning = True
        self.temp_slope = 0

        # heating default values
        self.hPower1_val = 0.01
        self.hPower2_val = 0.6
        self.hPower3_val = 0.01
        self.hPower4_val = 0.01
        self.hPower5_val = 0.01
        self.hPower6_val = 0.01
        self.hPower7_val = 0.5
        self.hPower8_val = 0.01
        self.hPower9_val = 0.10
        self.hPower10_val = 0.8
        self.hPower11_val = 0.01
        self.hPower12_val = 0.01
        self.hPower13_val = 0.8
        self.hPower14_val = 0.01
        self.hPower15_val = 0.25
        self.hPower16_val = 0.25

        self.hPWM1_val = 0.2
        self.hPWM2_val =0.2
        self.hPWM3_val =0.2
        self.hPWM4_val =0.2
        self.hPWM5_val = 0.2
        self.hPWM6_val = 0.2
        self.hPWM7_val = 0.2
        self.hPWM8_val = 0.2
        self.hPWM9_val = 0.2
        self.hPWM10_val = 0.2
        self.hPWM11_val = 0.2
        self.hPWM12_val = 0.2
        self.hPWM13_val = 0.2
        self.hPWM14_val = 0.2
        self.hPWM15_val = 0.2
        self.hPWM16_val = 0.2

        self.targetTemp = 0
        self.new_temp = []

    def init_graph(self):
        ###### for graph
        self.graphWidget = self.findChild(pg.PlotWidget, "graphicsView")
        self.graphWidget.setTitle("Temperature graph")
        self.graphWidget.setLabel('bottom', 'Time')
        self.graphWidget.setLabel('left', 'Temperature')


    def init_ui_elements(self):
        
        self.init_stacked_widget()
        # set styling changes for errors
        self.error_style = "QLineEdit { border-radius: 7px; border: 3px solid red; background-color: #fef5f4; color: red; }"
        self.error_style_pink = "QLineEdit { border-radius: 7px; border: 3px solid red; background-color:rgba(232,154,155,255); color: red; }" 
        self.page_chosen = "QPushButton { border: none; color: black; background-color:#feeaeb;}"
        self.page_uncheck = "QPushButton { border: none; color: #fef5f4; background-color:rgba(232,154,155,255);}"

        self.init_heating_page_widgets()
        self.init_temp_widgets()
        self.init_recoater_widgets()
        self.init_roller_widgets()
        self.init_test_cycle_widgets()
        self.init_hopper_widgets()
        self.init_z_widgets()
        self.init_build_info_widgets()
        self.init_misc_widgets()
        self.init_status_widgets()
        self.init_scancard_widgets()

    def init_heating_page_widgets(self):

        

        # chamber temperature widgets

 
        self.setBedTemperatureButton = self.findChild(QPushButton, "setBedTemperatureButton")
        self.BedTempCooldown = self.findChild(QPushButton,"setBedTemperatureCooldownButton")
        self.ChamberTempCooldown = self.findChild(QPushButton,"setChamberTemperatureCooldownButton")
        self.setChamberPIDTemperatureButton = self.findChild(QPushButton,"setChamberPIDTemperatureButton")
        self.pyroReading = self.findChild(QLabel, "pyroReading")
        self.PIDSetpointReading = self.findChild(QLabel, "PIDSetpointReading")
        self.setBedTemperatureLineEdit = self.findChild(QLineEdit, "setBedTemperatureLineEdit")
        self.setChamberTemperatureLineEdit = self.findChild(QLineEdit, "setChamberTemperatureLineEdit")
        self.PID_P = self.findChild(QLineEdit, "PID_P")
        self.PID_I = self.findChild(QLineEdit, "PID_I")
        self.PID_D = self.findChild(QLineEdit, "PID_D")
        self.zoneA = self.findChild(QLineEdit, "zoneA")
        self.zoneB = self.findChild(QLineEdit, "zoneB")
        self.zoenC = self.findChild(QLineEdit, "zoneC")
        self.zoenD = self.findChild(QLineEdit, "zoneD")
        self.iClamp = self.findChild(QLineEdit, "iClamp") 
        self.overshootDivisor = self.findChild(QLineEdit, "overshootDivisor") 



        self.BedTempCooldown.clicked.connect(self.chamber_instance.cooldownBedTemp)
        self.setBedTemperatureButton.clicked.connect(lambda: self.chamber_instance.setBedTemp(self.setBedTemperatureLineEdit.text()))


        self.ChamberTempCooldown.clicked.connect(self.chamber_instance.cooldownBuildChamber)
        self.setChamberPIDTemperatureButton.clicked.connect(lambda: self.chamber_instance.setChamberPIDTemp())

        self.setChamberTemperatureLineEdit.returnPressed.connect(lambda: self.setTargetTemp(self.setChamberTemperatureLineEdit.text()))


        # page 1 


        # self.heaterPower = self.findChild(QLineEdit, "heaterPower")
        # self.heaterPower.returnPressed.connect(self.heatingPower_edit)
        # self.heaterPower.textChanged.connect(lambda: self.reset_line_edit_style(self.heaterPower))
        # self.heaterPower.setText(str(self.heatingPower_value))

        # self.pwmCycleTime = self.findChild(QLineEdit, "pwmCycleTime")
        # self.pwmCycleTime.returnPressed.connect(self.pwmCycleTime_edit)
        # self.pwmCycleTime.textChanged.connect(lambda: self.reset_line_edit_style(self.pwmCycleTime))
        # self.pwmCycleTime.setText(str(self.pwmCycleTime_value))

        # self.updateHeating = self.findChild(QPushButton, "updateHeating")
        # self.updateHeating.clicked.connect(self.update_heating_settings)

        # self.heaterOnButton2 = self.findChild(QPushButton, "heaterOnButton2")
        # self.heaterOnButton2.clicked.connect(self.mech_code_handler_instance.heater_on)

        # self.heaterOffButton2 = self.findChild(QPushButton,"heaterOffButton2")
        # self.heaterOffButton2.clicked.connect(self.mech_code_handler_instance.heater_off)

        self.HeaterOnButton = self.findChild(QPushButton,"HeaterOnButton")
        self.HeaterOnButton.clicked.connect(self.mech_code_handler_instance.heater_on)

        self.HeaterOffButton = self.findChild(QPushButton, "HeaterOffButton")
        self.HeaterOffButton.clicked.connect(self.mech_code_handler_instance.heater_off)

        # page 2
        self.hPower_1 = self.findChild(QLineEdit, "hPower_1")
        self.hPower_1.returnPressed.connect(lambda: self.update_heater_power(self.hPower_1,self.hPower1_val))
        self.hPower_1.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_1))

        self.hPower_2 = self.findChild(QLineEdit, "hPower_2")
        self.hPower_2.returnPressed.connect(lambda: self.update_heater_power(self.hPower_2,self.hPower2_val))
        self.hPower_2.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_2))

        self.hPower_3 = self.findChild(QLineEdit, "hPower_3")
        self.hPower_3.returnPressed.connect(lambda: self.update_heater_power(self.hPower_3,self.hPower3_val))
        self.hPower_3.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_3))

        self.hPower_4 = self.findChild(QLineEdit, "hPower_4")
        self.hPower_4.returnPressed.connect(lambda: self.update_heater_power(self.hPower_4,self.hPower4_val))
        self.hPower_4.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_4))

        self.hPower_5 = self.findChild(QLineEdit, "hPower_5")
        self.hPower_5.returnPressed.connect(lambda: self.update_heater_power(self.hPower_5,self.hPower5_val))
        self.hPower_5.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_5))

        self.hPower_6 = self.findChild(QLineEdit, "hPower_6")
        self.hPower_6.returnPressed.connect(lambda: self.update_heater_power(self.hPower_6,self.hPower6_val))
        self.hPower_6.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_6))

        self.hPower_7 = self.findChild(QLineEdit, "hPower_7")
        self.hPower_7.returnPressed.connect(lambda: self.update_heater_power(self.hPower_7,self.hPower7_val))
        self.hPower_7.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_7))

        self.hPower_9 = self.findChild(QLineEdit, "hPower_9")
        self.hPower_9.returnPressed.connect(lambda: self.update_heater_power(self.hPower_9,self.hPower9_val))
        self.hPower_9.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_9))

        self.hPower_10 = self.findChild(QLineEdit, "hPower_10")
        self.hPower_10.returnPressed.connect(lambda: self.update_heater_power(self.hPower_10,self.hPower10_val))
        self.hPower_10.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_10))

        self.hPower_11 = self.findChild(QLineEdit, "hPower_11")
        self.hPower_11.returnPressed.connect(lambda: self.update_heater_power(self.hPower_11,self.hPower11_val))
        self.hPower_11.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_11))

        self.hPower_12 = self.findChild(QLineEdit, "hPower_12")
        self.hPower_12.returnPressed.connect(lambda: self.update_heater_power(self.hPower_12,self.hPower12_val))
        self.hPower_12.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_12))

        self.hPower_13 = self.findChild(QLineEdit, "hPower_13")
        self.hPower_13.returnPressed.connect(lambda: self.update_heater_power(self.hPower_13,self.hPower13_val))
        self.hPower_13.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_13))

        self.hPower_14 = self.findChild(QLineEdit, "hPower_14")
        self.hPower_14.returnPressed.connect(lambda: self.update_heater_power(self.hPower_14,self.hPower14_val))
        self.hPower_14.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_14))

        self.hPower_15 = self.findChild(QLineEdit, "hPower_15")
        self.hPower_15.returnPressed.connect(lambda: self.update_heater_power(self.hPower_15,self.hPower15_val))
        self.hPower_15.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_15))

        self.hPower_16 = self.findChild(QLineEdit, "hPower_16")
        self.hPower_16.returnPressed.connect(lambda: self.update_heater_power(self.hPower_16,self.hPower16_val))
        self.hPower_16.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPower_16))


        
        self.hPWM_1 = self.findChild(QLineEdit, "hPWM_1")
        self.hPWM_1.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_1,self.hPWM1_val))
        self.hPWM_1.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_1))

        self.hPWM_2 = self.findChild(QLineEdit, "hPWM_2")
        self.hPWM_2.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_2,self.hPWM2_val))
        self.hPWM_2.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_2))

        self.hPWM_3 = self.findChild(QLineEdit, "hPWM_3")
        self.hPWM_3.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_3,self.hPWM3_val))
        self.hPWM_3.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_3))

        self.hPWM_4 = self.findChild(QLineEdit, "hPWM_4")
        self.hPWM_4.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_4,self.hPWM4_val))
        self.hPWM_4.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_4))

        self.hPWM_5 = self.findChild(QLineEdit, "hPWM_5")
        self.hPWM_5.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_5,self.hPWM5_val))
        self.hPWM_5.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_5))

        self.hPWM_6 = self.findChild(QLineEdit, "hPWM_6")
        self.hPWM_6.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_6,self.hPWM6_val))
        self.hPWM_6.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_6))

        self.hPWM_7 = self.findChild(QLineEdit, "hPWM_7")
        self.hPWM_7.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_7,self.hPWM7_val))
        self.hPWM_7.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_7))

        self.hPWM_9 = self.findChild(QLineEdit, "hPWM_9")
        self.hPWM_9.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_9,self.hPWM9_val))
        self.hPWM_9.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_9))

        self.hPWM_10 = self.findChild(QLineEdit, "hPWM_10")
        self.hPWM_10.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_10,self.hPWM10_val))
        self.hPWM_10.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_10))

        self.hPWM_11 = self.findChild(QLineEdit, "hPWM_11")
        self.hPWM_11.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_11,self.hPWM11_val))
        self.hPWM_11.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_11))

        self.hPWM_12 = self.findChild(QLineEdit, "hPWM_12")
        self.hPWM_12.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_12,self.hPWM12_val))
        self.hPWM_12.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_12))

        self.hPWM_13 = self.findChild(QLineEdit, "hPWM_13")
        self.hPWM_13.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_13,self.hPWM13_val))
        self.hPWM_13.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_13))

        self.hPWM_14 = self.findChild(QLineEdit, "hPWM_14")
        self.hPWM_14.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_14,self.hPWM14_val))
        self.hPWM_14.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_14))

        self.hPWM_15 = self.findChild(QLineEdit, "hPWM_15")
        self.hPWM_15.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_15,self.hPWM15_val))
        self.hPWM_15.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_15))

        self.hPWM_16 = self.findChild(QLineEdit, "hPWM_16")
        self.hPWM_16.returnPressed.connect(lambda: self.update_heater_power(self.hPWM_16,self.hPWM16_val))
        self.hPWM_16.textChanged.connect(lambda: self.reset_line_edit_style_pink(self.hPWM_16))

        self.ch_1 = self.findChild(QLabel, "ch1")
        self.ch_2 = self.findChild(QLabel, "ch2")
        self.ch_3 = self.findChild(QLabel, "ch3")
        self.ch_4 = self.findChild(QLabel, "ch4")
        self.ch_5 = self.findChild(QLabel, "ch5")
        self.ch_6 = self.findChild(QLabel, "ch6")
        self.ch_7 = self.findChild(QLabel, "ch7")
        self.ch_8 = self.findChild(QLabel, "ch8")
        self.ch_9 = self.findChild(QLabel, "ch9")
        self.ch_10 = self.findChild(QLabel, "ch10")
        self.ch_11 = self.findChild(QLabel, "ch11")
        self.ch_12 = self.findChild(QLabel, "ch12")
        self.ch_13 = self.findChild(QLabel, "ch13")
        self.ch_14 = self.findChild(QLabel, "ch14")
        self.ch_15 = self.findChild(QLabel, "ch15")
        self.ch_16 = self.findChild(QLabel, "ch16")
        
        self.updateHeatingButton_2 = self.findChild(QPushButton, "updateHeatingButton_2")
        self.updateHeatingButton_2.clicked.connect(self.update_heating_settings_2)


    def init_recoater_widgets(self):
        self.recoaterSpeed_m = self.findChild(QLineEdit, "recoaterSpeed_m")
        self.recoaterSpeed_m.returnPressed.connect(lambda: self.recoater_speed_edit("m", self.recoaterSpeed_m))
        self.recoaterSpeed_m.textChanged.connect(lambda: self.reset_line_edit_style(self.recoaterSpeed_m))
        self.recoaterSpeed_m.setText(str(self.recoater_speed))

        self.recoaterRight_m = self.findChild(QPushButton, "recoaterRight_m")
        self.recoaterRight_m.clicked.connect(lambda: self.recoater_dir("right"))

        self.recoaterLeft_m = self.findChild(QPushButton, "recoaterLeft_m")
        self.recoaterLeft_m.clicked.connect(lambda: self.recoater_dir("left"))

    def init_roller_widgets(self):
        self.rollerSpeed_m = self.findChild(QLineEdit, "rollerSpeed_m")
        self.rollerSpeed_m.returnPressed.connect(lambda: self.roller_speed_edit("m", self.rollerSpeed_m))
        self.rollerSpeed_m.textChanged.connect(lambda: self.reset_line_edit_style(self.rollerSpeed_m))
        self.rollerSpeed_m.setText(str(self.roller_speed))

        self.rollerCW_m = self.findChild(QPushButton, "rollerCW_m")
        self.rollerCW_m.clicked.connect(lambda: self.roller_dir("cw"))

        self.rollerCCW_m = self.findChild(QPushButton, "rollerCCW_m")
        self.rollerCCW_m.clicked.connect(lambda: self.roller_dir("ccw"))


        # self.rollerSpeed = self.findChild(QLineEdit, "rollerSpeed") 
        # self.rollerSpeed.returnPressed.connect(lambda: self.roller_speed_edit("print", self.rollerSpeed))
        # self.rollerSpeed.textChanged.connect(lambda: self.reset_line_edit_style(self.rollerSpeed))
        # self.rollerSpeed.setText(str(self.roller_speed))

    def init_hopper_widgets(self):
        self.lHopper = self.findChild(QPushButton, "lHopper")
        self.lHopper.clicked.connect(lambda: self.hopper_select("left")) 
        self.lHopper.clicked.connect(lambda: self.activate_button_hSelect(self.lHopper))

        self.lHopperStatus = self.findChild(QLabel, "lHopperStatus")

        self.rHopper = self.findChild(QPushButton, "rHopper")
        self.rHopper.clicked.connect(lambda: self.hopper_select("right"))
        self.rHopper.clicked.connect(lambda: self.activate_button_hSelect(self.rHopper))

        self.rHopperStatus = self.findChild(QLabel, "rHopperStatus")
        
        self.h1sec = self.findChild(QPushButton, "h1sec")
        self.h1sec.clicked.connect(lambda: self.hTime(1))
        self.h1sec.clicked.connect(lambda: self.activate_button_hTime(self.h1sec))

        self.h3sec = self.findChild(QPushButton, "h3sec")
        self.h3sec.clicked.connect(lambda: self.hTime(3))
        self.h3sec.clicked.connect(lambda: self.activate_button_hTime(self.h3sec))

        self.h5sec = self.findChild(QPushButton, "h5sec")
        self.h5sec.clicked.connect(lambda: self.hTime(5))
        self.h5sec.clicked.connect(lambda: self.activate_button_hTime(self.h5sec))

        self.h10mm = self.findChild(QPushButton, "h10mm")
        self.h10mm.clicked.connect(lambda: self.hDist(10))
        self.h10mm.clicked.connect(lambda: self.activate_button_hDistance(self.h10mm))

        self.h8mm = self.findChild(QPushButton, "h8mm")
        self.h8mm.clicked.connect(lambda: self.hDist(8))
        self.h8mm.clicked.connect(lambda: self.activate_button_hDistance(self.h8mm))

        self.h6mm = self.findChild(QPushButton, "h6mm")
        self.h6mm.clicked.connect(lambda: self.hDist(6))
        self.h6mm.clicked.connect(lambda: self.activate_button_hDistance(self.h6mm))

        self.hDose_m = self.findChild(QPushButton, "hDose_m")
        self.hDose_m.clicked.connect(self.hopper_instance.dose)

        self.hDistance = self.findChild(QLineEdit, "hDistance")
        self.hDistance.returnPressed.connect(self.hDistance_edit)
        self.hDistance.textChanged.connect(lambda: self.reset_line_edit_style(self.hDistance))
        self.hDistance.setText(str(self.hopperDistanceLEFT))

        self.hDuration = self.findChild(QLineEdit, "hDuration")
        self.hDuration.returnPressed.connect(self.hDuration_edit)
        self.hDuration.textChanged.connect(lambda: self.reset_line_edit_style(self.hDuration))
        self.hDuration.setText(str(self.hopperDurationLEFT))

    def init_z_widgets(self):
        self.Z_current = self.findChild(QLabel, "Z_m")
        self.ZOffset_sum = self.findChild(QLabel, "ZOffset_m")
        self.ZOffset_sum.setText(" --")

        self.ZUp = self.findChild(QPushButton, "ZUp")
        self.ZUp.clicked.connect(self.Z_move_up)

        self.ZDown = self.findChild(QPushButton, "ZDown")
        self.ZDown.clicked.connect(self.Z_move_down)

        self.z001 = self.findChild(QPushButton, "z001")
        self.z001.clicked.connect(lambda: self.Z_offdist_m(0.01))
        self.z001.clicked.connect(lambda: self.activate_button_z(self.z001))

        self.z01 = self.findChild(QPushButton, "z01")
        self.z01.clicked.connect(lambda: self.Z_offdist_m(0.1))
        self.z01.clicked.connect(lambda: self.activate_button_z(self.z01))

        self.z1 = self.findChild(QPushButton, "z1")
        self.z1.clicked.connect(lambda: self.Z_offdist_m(1))
        self.z1.clicked.connect(lambda: self.activate_button_z(self.z1))

        self.z10 = self.findChild(QPushButton, "z10")
        self.z10.clicked.connect(lambda: self.Z_offdist_m(10))
        self.z10.clicked.connect(lambda: self.activate_button_z(self.z10))

        self.z100 = self.findChild(QPushButton, "z100")
        self.z100.clicked.connect(lambda: self.Z_offdist_m(100))
        self.z100.clicked.connect(lambda: self.activate_button_z(self.z100))

        self.ZOffsetUp = self.findChild(QPushButton, "ZOffsetUp")
        self.ZOffsetUp.clicked.connect(lambda: self.ZOffsetDirection("up"))

        self.ZOffsetDown = self.findChild(QPushButton, "ZOffsetDown")
        self.ZOffsetDown.clicked.connect(lambda: self.ZOffsetDirection("down"))

        self.homeButton = self.findChild(QPushButton, "homeButton")
        self.homeButton.clicked.connect(self.homing_z)

    def init_misc_widgets(self):
        self.laserWindowStatus = self.findChild(QPushButton, "laserWindowStatus")
        self.laserWindowStatus.clicked.connect(self.lWindow_button_click)

        self.consoleWidget = self.findChild(QListWidget, "consoleWidget")

        self.emergencyStopButton = self.findChild(QPushButton, "emergencyStopButton")
        self.emergencyStopButton.clicked.connect(self.emergency_stop)

        self.shutdownButton = self.findChild(QPushButton, "shutdownButton")
        self.shutdownButton.clicked.connect(self.machine_shutdown)

        self.firmwareRestartButton = self.findChild(QPushButton, "firmwareRestartButton")
        self.firmwareRestartButton.clicked.connect(self.mech_code_handler_instance.firmware_restart)

        self.toggleButton = self.findChild(QPushButton,"toggleButton")
        self.toggleButton.clicked.connect(self.mech_code_handler_instance.toggle)

        

    def init_status_widgets(self):
        self.mechStatus = self.findChild(QLabel, "mechStatus")

        self.scancardStatus = self.findChild(QLabel, "scancardStatus")

        self.tempStatus = self.findChild(QLabel, "tempStatus")

    def init_scancard_widgets(self):
        self.uploadFileButton = self.findChild(QPushButton, "uploadFileButton")
        self.uploadFileButton.clicked.connect(self.upload_file_button_click)

        self.startPrintButton = self.findChild(QPushButton, "startPrintButton")
        self.startPrintButton.clicked.connect(self.start_print_button_click)

        self.stopPrintButton = self.findChild(QPushButton, "stopPrintButton")
        self.stopPrintButton.clicked.connect(self.stop_print_button_click)

        self.jDelay = self.findChild(QLineEdit, "jDelay")
        self.jDelay.returnPressed.connect(self.jDelay_edit)
        self.jDelay.textChanged.connect(lambda: self.reset_line_edit_style(self.jDelay))
        self.jDelay.setText(str(self.jumpDelay))

        self.pDelay = self.findChild(QLineEdit, "pDelay")
        self.pDelay.returnPressed.connect(self.pDelay_edit)
        self.pDelay.textChanged.connect(lambda: self.reset_line_edit_style(self.pDelay))
        self.pDelay.setText(str(self.polygonDelay))

        self.jSpeed = self.findChild(QLineEdit, "jSpeed")
        self.jSpeed.returnPressed.connect(self.jSpeed_edit)
        self.jSpeed.textChanged.connect(lambda: self.reset_line_edit_style(self.jSpeed))
        self.jSpeed.setText(str(self.jumpSpeed))

        self.mSpeed = self.findChild(QLineEdit, "mSpeed")
        self.mSpeed.returnPressed.connect(self.mSpeed_edit)
        self.mSpeed.textChanged.connect(lambda: self.reset_line_edit_style(self.mSpeed))
        self.mSpeed.setText(str(self.markSpeed))

        self.pWidth = self.findChild(QLineEdit, "pWidth")
        self.pWidth.returnPressed.connect(self.pWidth_edit)
        self.pWidth.textChanged.connect(lambda: self.reset_line_edit_style(self.pWidth))
        self.pWidth.setText(str(self.pulseWidth))

        self.lFreq = self.findChild(QLineEdit, "lFreq")
        self.lFreq.returnPressed.connect(self.lFreq_edit)
        self.lFreq.textChanged.connect(lambda: self.reset_line_edit_style(self.lFreq))
        self.lFreq.setText(str(self.laserfreq))

        self.fpWidth = self.findChild(QLineEdit, "fpWidth")
        self.fpWidth.returnPressed.connect(self.fpulsewidth_edit)
        self.fpWidth.textChanged.connect(lambda: self.reset_line_edit_style(self.fpWidth))
        self.fpWidth.setText(str(self.firstPulseWidth))

        self.pkDelay = self.findChild(QLineEdit, "pkDelay")
        self.pkDelay.returnPressed.connect(self.pKiller_edit)
        self.pkDelay.textChanged.connect(lambda: self.reset_line_edit_style(self.pkDelay))
        self.pkDelay.setText(str(self.polygonKillerTime))

        self.fpkLength = self.findChild(QLineEdit, "fpkLength")
        self.fpkLength.returnPressed.connect(self.fpkLength_edit)
        self.fpkLength.textChanged.connect(lambda: self.reset_line_edit_style(self.fpkLength))
        self.fpkLength.setText(str(self.firstPulseKillerLength))

        self.LOnDelay = self.findChild(QLineEdit, "LOnDelay")
        self.LOnDelay.returnPressed.connect(self.LOnDelay_edit)
        self.LOnDelay.textChanged.connect(lambda: self.reset_line_edit_style(self.LOnDelay))
        self.LOnDelay.setText(str(self.laserOnDelay))

        self.LOffDelay = self.findChild(QLineEdit, "LOffDelay")
        self.LOffDelay.returnPressed.connect(self.LOffDelay_edit)
        self.LOffDelay.textChanged.connect(lambda: self.reset_line_edit_style(self.LOffDelay))
        self.LOffDelay.setText(str(self.laserOffDelay))

        self.iStep = self.findChild(QLineEdit, "iStep")
        self.iStep.returnPressed.connect(self.iStep_edit)
        self.iStep.textChanged.connect(lambda: self.reset_line_edit_style(self.iStep))
        self.iStep.setText(str(self.incrementStep))

    def init_class_instances(self):
        self.mech_logger = ErrorLogger()
        self.hopper_instance = Hopper(self)
        self.recoater_instance = Recoater(self)
        self.Z_instance = Z(self)
        self.chamber_instance = buildChamber(self)
        self.mech_code_handler_instance = MechCodeHandler(self)
        self.scancard_instance = Scancard(self)        
        self.mech_logger = ErrorLogger()
        self.laser_logger = LaserErrorLogger()
        self.config_editor = ConfigEditor(self)
        self.config_editor_worker = ConfigEditorWorker(self.config_editor, self)
        self.csv_logger = CSVLogger()
        self.graphing = Graph(self)

    def init_threads(self):
        ## threads to monitor connection status
        self.network_checker = NetworkChecker(self)
        self.network_checker.status_changed.connect(self.update_network_status)
        self.network_checker.start()

        self.scancard_checker = ScancardConnection(self)
        self.scancard_checker.status_changed.connect(self.update_scancard_status)
        self.scancard_checker.start()

        # thread initialization for reading and updating temperature values
        self.temp_worker = TempWorker(self) 
        self.temp_worker.temp_data_signal.connect(self.update_temperatures)
        self.temp_worker.temp_connection_signal.connect(self.update_templogger_status)
        self.temp_worker.start()

        # thread to handle cycle test loop
        self.worker = CycleThread(self.cycleStart, self.update_console_signal, self.update_z_signal)
        self.worker.progress.connect(self.handle_progress)

        # # thread to handle print loop
        self.printWorker = PrintThread(self.print_loop, self.update_console_signal, self.update_z_signal) 
        self.printWorker.progress.connect(self.handle_progress)
        self.printWorker.update_layer_signal.connect(self.update_layer)
        self.printWorker.update_elapsed_time.connect(self.update_elapsed_time)

        # name the threads to make identification easy
        self.worker.setObjectName("CycleLoopThread")
        self.printWorker.setObjectName("PrintLoopThread")

        # connect console signal to to trigger adding item into console 
        self.update_console_signal.connect(self.console_edit)

    def init_build_info_widgets(self):
        self.buildPercentage = self.findChild(QLabel, "buildPercentage")
        self.layerNum = self.findChild(QLabel, "layerNum")
        self.timeElapsed = self.findChild(QLabel, "timeElapsed")
        self.buildTimeLeft = self.findChild(QLabel, "buildTimeLeft")

    def init_test_cycle_widgets(self):
        # self.recoaterSpeed = self.findChild(QLineEdit, "recoaterSpeed")
        # self.recoaterSpeed.returnPressed.connect(lambda: self.recoater_speed_edit("print", self.recoaterSpeed))
        # self.recoaterSpeed.textChanged.connect(lambda: self.reset_line_edit_style(self.recoaterSpeed))
        # self.recoaterSpeed.setText(str(self.recoater_speed))

        self.cycleCount = self.findChild(QLabel, "cycleCount")
        # self.cycleCount.returnPressed.connect(self.count_edit)
        # self.cycleCount.textChanged.connect(lambda: self.reset_line_edit_style(self.cycleCount))

        self.currentCount = self.findChild(QLabel, "currentCount")

    def init_temp_widgets(self):
        self.ch1 = self.findChild(QLabel, "ch_1")
        self.ch2 = self.findChild(QLabel, "ch_2")
        self.ch3 = self.findChild(QLabel, "ch_3")
        self.ch4 = self.findChild(QLabel, "ch_4")
        self.ch5 = self.findChild(QLabel, "ch_5")
        self.ch6 = self.findChild(QLabel, "ch_6")
        self.ch7 = self.findChild(QLabel, "ch_7")
        self.ch8 = self.findChild(QLabel, "ch_8")
        self.ch9 = self.findChild(QLabel, "ch_9")
        self.ch10 = self.findChild(QLabel, "ch_10")
        self.ch11 = self.findChild(QLabel, "ch_11")
        self.ch12 = self.findChild(QLabel, "ch_12")
        self.ch13 = self.findChild(QLabel, "ch_13")
        self.ch14 = self.findChild(QLabel, "ch_14")
        self.ch15 = self.findChild(QLabel, "ch_15")
        self.ch16 = self.findChild(QLabel, "ch_16")


    def init_stacked_widget(self):
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.dashboard = self.findChild(QWidget,"dashboard")
        self.heatingPage = self.findChild(QWidget,"heatingPage")
        self.graphPage = self.findChild(QWidget, "tempGraph")

        # adding the pages to stackedWidget
        self.stackedWidget.addWidget(self.dashboard)
        self.stackedWidget.addWidget(self.heatingPage)
        self.stackedWidget.addWidget(self.graphPage)

        # setting default page as dashboard
        self.stackedWidget.setCurrentIndex(0)

        ##### Page change widgets #########
        self.goToTempPageButton = self.findChild(QPushButton, "goToTempPageButton")
        self.goToTempPageButton.clicked.connect(lambda: self.change_page("heatingPage", self.goToTempPageButton))

        self.backToDashboardButton = self.findChild(QPushButton, "backToDashboardButton")
        self.backToDashboardButton.clicked.connect(lambda: self.change_page("dashboard", self.backToDashboardButton))

        self.goToTempGraphButton = self.findChild(QPushButton,"goToTempGraphButton")
        self.goToTempGraphButton.clicked.connect(lambda: self.change_page("graph",self.goToTempGraphButton))

   #################### graph ######################

    def setup_graph(self):
        self.graphWidget = self.findChild(pg.PlotWidget, "graphicsView")
        self.graphWidget.setTitle("Temperature graph")
        self.graphWidget.setLabel('bottom', 'Time')
        self.graphWidget.setLabel('left', 'Temperature')

        self.graph = Graph(self)





    ############################## recoater functions     #########################

    # function for taking recoater speed input and saving it
    def recoater_speed_edit(self, mode, widget):
     
        try:
     # for maintenance mode
            if mode == "m":
                self.rSpeed = int(self.recoaterSpeed_m.text())
    # for test loop mode
            elif mode == "cycle":
                self.rSpeed = int(self.cycleRecoaterSpeed.text())
    # for actual print cycle
            elif mode == "print":
                self.rSpeed = int(self.recoaterSpeed.text())

        except Exception as e:
            self.mech_logger.logger.error(f"E106 : Invalid input given!! \n {e}")
            self.update_console_signal.emit({"error":f"E106 : Invalid input given!! \n {e}"})
            widget.setStyleSheet(self.error_style)


        if self.rSpeed>=100 and self.rSpeed<=3000:
            self.recoater_speed = self.rSpeed
            self.mech_logger.logger.info(f"Recoater speed changed in GUI to {self.recoater_speed}")
            self.update_console_signal.emit({"info":f"Recoater speed changed in GUI to {self.recoater_speed}"})

        else:
            self.mech_logger.logger.error("E105 : Range Error!! - Given input out of range!!")
            self.update_console_signal.emit({"error":"E105 : Range Error!! - Given input out of range!!"})
            widget.setStyleSheet(self.error_style)

    # function for saving recoater direction given as input
    def recoater_dir(self, dir):
        # set recoater speed
        # self.recoater_pwm = self.speed_to_pwm(self.recoater_speed)
        # self.recoater_instance.set_recoater_speed()

        # send recoater direction
        if dir == "left":
            self.recoater_instance.recoater_go_left()
        else:
            self.recoater_instance.recoater_go_right()

    # function to convert speed input given by users to PWM;  returns a float  
    def speed_to_pwm(self,speed): 
    # Given speed and PWM values
        speeds = [
        80, 180, 280, 380, 480, 580, 680, 780, 880, 980, 
        1080, 1180, 1280, 1380, 1480, 1580, 1680, 1780, 
        1880, 1980, 2080, 2180, 2280, 2380, 2480, 2580, 
        2680, 2780, 2880, 2980, 3080, 3159
        ]
        pwms = [
        0.88, 0.86, 0.83, 0.80, 0.77, 0.75, 0.72, 0.69, 
        0.66, 0.63, 0.61, 0.58, 0.55, 0.52, 0.49, 0.47, 
        0.44, 0.41, 0.38, 0.35, 0.33, 0.30, 0.27, 0.24, 
        0.21, 0.19, 0.16, 0.13, 0.10, 0.07, 0.05, 0.00
        ]
    
        # If speed is outside the provided range
        if speed < speeds[0]:
            return pwms[0]
        elif speed > speeds[-1]:
            return pwms[-1]
    
        # Find the interval in which the speed falls
        for i in range(len(speeds) - 1):
            if speeds[i] <= speed <= speeds[i + 1]:
                # Linear interpolation
                m = (pwms[i + 1] - pwms[i]) / (speeds[i + 1] - speeds[i])
                c = pwms[i] - m * speeds[i]
                return m * speed + c
    
        # Fallback in case speed is exactly at one of the data points
        return pwms[speeds.index(speed)]

    ############################################## roller functions

    # function for taking roller speed input and saving it
    def roller_speed_edit(self, mode, widget):
        try:
         # for maintenance mode
            if mode == "m":
                self.roSpeed = int(self.rollerSpeed_m.text())
        # for test loop mode
            elif mode == "cycle":
                self.roSpeed = int(self.cycleRollerSpeed.text())
         # for actual print cycle
            elif mode == "print":
                self.roSpeed = int(self.rollerSpeed.text())
        except Exception as e:
            self.mech_logger.logger.error(f"E106 : Invalid input given!! \n {e}")
            self.update_console_signal.emit({"error":f"E106 : Invalid input given!! \n {e}"})
            widget.setStyleSheet(self.error_style)



        if self.roSpeed>=80 and self.roSpeed<=3000:
                self.roller_speed = self.roSpeed
                self.mech_logger.logger.info(f"Roller speed changed in GUI to {self.roller_speed}")
                self.update_console_signal.emit({"info":f"Roller speed changed in GUI to {self.roller_speed}"})


        else:
            self.mech_logger.logger.error("E105 : Range Error!! - Given input out of range!!")
            self.update_console_signal.emit({"error":"E105 : Range Error!! - Given input out of range!!"})
            widget.setStyleSheet(self.error_style)
            

    # function for saving roller direction given as input
    def roller_dir(self,dir):
        # set roller speed
        self.roller_pwm = self.speed_to_pwm(self.roller_speed)
        self.recoater_instance.set_roller_speed()

        # send roller direction
        if dir == "cw":
            
            self.recoater_instance.roller_cw()
        else:
            self.recoater_instance.roller_ccw()

    ############################################# hopper functions

    # function for saving hopper slot distance given as input
    def hDistance_edit(self):
    
        try:
            
            # reading value from ui input field
            self.hDt = float(self.hDistance.text())

            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.hDt>=0.1 and self.hDt<=10:
                # self.hopperDistance = self.hDt
                self.mech_logger.logger.info(f"Hopper distance changed in GUI to {self.hopperDistance}")
                self.update_console_signal.emit({"info":f"Hopper distance changed in GUI to {self.hopperDistance}"})

            else:
                self.mech_logger.logger.error("E105 : Range Error!! - Given input out of range!!")
                self.update_console_signal.emit({"error":"E105 : Range Error!! - Given input out of range!!"})
                self.hDistance.setStyleSheet(self.error_style)

        except Exception as e:
            self.mech_logger.logger.error(f"E106 : Invalid input given!! \n {e}") 
            self.update_console_signal.emit({"error":f"E106 : Invalid input given!! \n {e}"})
            self.hDistance.setStyleSheet(self.error_style)

    # function for saving hopper slot open duration given as input
    def hDuration_edit(self):
  
        try:
            # reading value from ui input field
            self.hDr = float(self.hDuration.text())

             # checking if value if within acceptable range, if it is then we save it as global variable
            if self.hDr>=0 and self.hDr<=999:
                self.hopperDuration = self.hDr
                self.mech_logger.logger.info(f"Hopper duration changed in GUI to {self.hopperDuration}")
                self.update_console_signal.emit({"info":f"Hopper duration changed in GUI to {self.hopperDuration}"})

            else:
                self.mech_logger.logger.error("E105 : Range Error!! - Given input out of range!!")
                self.update_console_signal.emit({"error":"E105 : Range Error!! - Given input out of range!!"})
                self.hDuration.setStyleSheet(self.error_style)

        except Exception as e:
            self.mech_logger.logger.error(f"E106 : Invalid input given!! \n {e}") 
            self.update_console_signal.emit({"error":f"E106 : Invalid input given!! \n {e}"})
            self.hDuration.setStyleSheet(self.error_style)


    # function activated when 'left' or 'right' hopper selection button is clicked
    def hopper_select(self, hop):
        self.hopper_choice = hop
        if hop == "left":
            self.mech_logger.logger.info("Left hopper selected")
            self.update_console_signal.emit({"info":"Left hopper selected"})
        
        else:
            self.mech_logger.logger.info("Right hopper selected")
            self.update_console_signal.emit({"info":"Right hopper selected"})

    # function activated when any of the hopper slot duration selection buttons are clicked
    def hTime(self, duration):
        self.hopperDuration = duration
        self.mech_logger.logger.info(f"Hopper slot time changed to {self.hopperDuration} sec")
        self.update_console_signal.emit({"info":f"Hopper slot time changed to {self.hopperDuration} sec"})


    # function activated when any of the hopper slot distance selection buttons are clicked
    def hDist(self, mm):
        # self.hopperDistance = mm
        self.mech_logger.logger.info(f"Hopper slot time changed to {self.hopperDistance} mm")
        self.print_to_console({"info":f"Hopper slot time changed to {self.hopperDistance} mm"})


    ############################################## Z functions #############

    def Z_offdist_m(self, dist): # for setting Z-offset according to button clicked 
        self.zOffset = dist
        self.mech_logger.logger.info(f"Z offset distance changed to {self.zOffset} mm")
        self.update_console_signal.emit({"info":f"Z offset distance changed to {self.zOffset} mm"})

    # function for updating sum of offsets on the ui screen
    def Z_offset_update(self):
        self.z_offset_sum = self.z_offset_sum + self.zOffset
        self.ZOffset_sum.setText(str(self.z_offset_sum))
#
     # function activated when the Z direction buttons are pressed
    def ZOffsetDirection(self, dir):
        if dir == "up":
            self.Z_instance.z_force_up(self.zOffset)
        else:
            self.Z_instance.z_force_down(self.zOffset)
        self.Z_offset_update() # this updation logic is flawed

        # update Z position
        self.update_Z_position()

    # function activated when the Z up button is pressed
    def Z_move_up(self):
        self.Z_instance.move_z_up(self.zOffset)

        # update Z position
        self.update_Z_position()

    # function activated when the Z down button is pressed
    def Z_move_down(self):
        self.Z_instance.move_z_down(self.zOffset)
        # update Z position
        self.update_Z_position()

    # function to fetch Z position from moonraker and update it on the gui
    def update_Z_position(self):

        # fetch Z position from moonraker
        Z_position = self.Z_instance.get_Z_position() 
        
        current_thread = QThread.currentThread()
        main_thread = QCoreApplication.instance().thread()

        # updating it on gui

        # check if function is called in main thread
        if current_thread == main_thread:
            self.update_console_signal.emit(str(Z_position))
            self.print_to_console({"info":f"Z position updated to {Z_position}"})

        # check if function is called in cycle loop thread
        elif current_thread.objectName() == "CycleLoopThread":
            self.worker.update_z_signal.emit(str(Z_position))
            self.print_to_console({"info":f"Z position updated to {Z_position}"})

        elif current_thread.objectName() == "PrintLoopThread":
            self.printWorker.update_z_signal.emit(str(Z_position))
            self.print_to_console({"info":f"Z position updated to {Z_position}"})


    # function to home Z
    def homing_z(self):

        # change icon color to grey to indicate that homing process is taking place
        self.homeButton.setIcon(QIcon("../ui assets/house-grey.svg"))

        # reset the variable tracking homing
        self.homed = False

        # home Z
        self.Z_instance.home_z()

        if self.homed:
                # change the icon color to green
                self.homeButton.setIcon(QIcon("../ui assets/house-green.svg"))
        else:
            self.homeButton.setIcon(QIcon("../ui assets/house-solid.svg"))

    # update Z position triggered in separate thread, this function does the work in main thread
    def update_z_widget(self,text):
        self.Z_current.setText(text)

    ############################### misc functions
    def change_page(self, page, widget):

        if page == 'dashboard':
            self.stackedWidget.setCurrentIndex(0)
            self.goToTempGraphButton.setStyleSheet(self.page_uncheck)
            self.goToTempPageButton.setStyleSheet(self.page_uncheck)
            
        elif page == 'heatingPage':
            self.stackedWidget.setCurrentIndex(1)
            self.backToDashboardButton.setStyleSheet(self.page_uncheck)
            self.goToTempGraphButton.setStyleSheet(self.page_uncheck)

        elif page == "graph":
            self.stackedWidget.setCurrentIndex(2)
            self.goToTempPageButton.setStyleSheet(self.page_uncheck)
            self.backToDashboardButton.setStyleSheet(self.page_uncheck)

        widget.setStyleSheet(self.page_chosen)

    # function to be notified of thread progress
    def handle_progress(self, value):
        self.print_to_console({"info":f"Task Completed with progress: {value}%"})

    # function to exit the main application after safely stopping the worker threads
    def closeEvent(self, event):
        # Stop and wait for network checker thread
        if self.network_checker.is_running:
            self.network_checker.stop()  # Stop the thread's loop
            self.network_checker.wait()  # Wait until the thread finishes

        # Stop and wait for scancard connection thread
        if self.scancard_checker.is_running:
            self.scancard_checker.stop()
            self.scancard_checker.wait()


        if self.temp_worker.is_running:
            self.temp_worker.stop()
            self.temp_worker.wait()


        # Proceed with closing the window
        event.accept()


    ################### console related functions

    # function to add sentences to console; in case of error, text is printed in red. Else it is printed in white        
    def addConsoleItem(self,console_widget, text, is_error=False):
        # Create a new QListWidgetItem
        item = QListWidgetItem(f"> {text}")
    
        # Set the color based on whether it's an error or not
        if is_error:
            item.setForeground(QColor("red"))  # Error color
        else:
            item.setForeground(QColor("white"))  # Regular log color
                
        # Add the item to the ListWidget
        console_widget.addItem(item)
        # scroll to bottom of list so that newly added line is visible
        console_widget.scrollToBottom()

    # function used to edit console from main thread and other threads
    def console_edit(self,dict):
        if "error" in dict.keys():
            self.addConsoleItem(self.consoleWidget, dict["error"], is_error=True)
        else:
            self.addConsoleItem(self.consoleWidget, dict["info"])


    def print_to_console(self, data):
        current_thread = QThread.currentThread()
        main_thread = QCoreApplication.instance().thread()

        # check if function is called in main thread
        if current_thread == main_thread:
            self.update_console_signal.emit(data)
        # check if function is called in cycle loop thread
        elif current_thread.objectName() == "CycleLoopThread":
            self.worker.update_console_signal.emit(data)
        elif current_thread.objectName() == "PrintLoopThread":
            self.printWorker.update_console_signal.emit(data)

    ################ heating functionality ############
    
    ########### Heater and temperature related functions 
    # function to take heating power input from ui
    def heatingPower_edit(self):
        try:
            # take input from ui
            self.heatingPower_value = int(self.heaterPower.text())/100

            # chack if value is in range
            if self.heatingPower_value <= 100 and self.heatingPower_value >= 0:
                self.laser_logger.logger.info(f"Heater power  value is updated to {self.heatingPower_value} ")
                self.update_console_signal.emit({"info":f"Heater power value is updated to {self.heatingPower_value} "})
            else:
                self.laser_logger.logger.error("E105: Heater power Input out of range!")
                self.update_console_signal.emit({"error":"E105: Heater power Input out of range!"})
                self.heaterPower.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E106: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E106: Invalid input given - Input must be integer \n {e}"})
            self.heaterPower.setStyleSheet(self.error_style)

    # function to take heating time input from ui
    def heatingTime_edit(self):
        try:
            # take input from ui
            self.heatingTime_value = int(self.heatingTime.text())

            # chack if value is in range
            if self.heatingTime_value <= 60 and self.heatingTime_value >= 1:
                self.laser_logger.logger.info(f"Heating time value is updated to {self.heatingTime_value} s")
                self.update_console_signal.emit({"info":f"Heating time value is updated to {self.heatingTime_value} s"})
            else:
                self.laser_logger.logger.error("E105: Heating time Input out of range!")
                self.update_console_signal.emit({"error":"E105: Heating time Input out of range!"})
                self.heatingTime.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E106: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E106: Invalid input given - Input must be integer \n {e}"})
            self.heatingTime.setStyleSheet(self.error_style)

    # function to take heating time input from ui
    def pwmCycleTime_edit(self):
        try:
            # take input from ui
            self.pwmCycleTime_value = float(self.pwmCycleTime.text())

            # chack if value is in range
            if self.pwmCycleTime_value <= 0.3 and self.pwmCycleTime_value >= 0:
                self.laser_logger.logger.info(f"PWM cycle time value is updated to {self.pwmCycleTime_value}")
                self.update_console_signal.emit({"info":f"PWM cycle time value is updated to {self.pwmCycleTime_value}"})
            else:
                self.laser_logger.logger.error("E105: PWM cycle time Input out of range!")
                self.update_console_signal.emit({"error":"E105: PWM cycle time Input out of range!"})
                self.pwmCycleTime.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E106: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E106: Invalid input given - Input must be integer \n {e}"})
            self.pwmCycleTime.setStyleSheet(self.error_style)

    def update_heating_settings(self):

        # set all the heater powers to single value given as input
        for i in range(17):
            setattr(self, f"hPower{i}_val", self.heatingPower_value)
    
        # print(self.hPower10_val)

        # set all PWM values to single value given as input
        for i in range(17):
            setattr(self, f"hPWM{i}_val", self.pwmCycleTime_value)

        # print(self.hPWM10_val)

        # now the actual updation process begins
        self.config_editor_worker.start()

        # firmware restart to enable updation
        # self.mech_code_handler_instance.firmware_restart()


    def update_heating_settings_2(self):
        try:
            self.config_editor_worker.start()
            # self.mech_code_handler_instance.firmware_restart()
        except Exception as e:
            self.mech_logger.logger.error("Error while changing pwm and power values of heater")
            self.print_to_console({"error":"Error while changing pwm and power values of heater"})

    def update_heater_power(self,lineEdit, var):
        try:
            var = float(lineEdit.text())

            if var<=1 and var>=0:
                self.print_to_console({"info":"Heater power value changed in GUI"})
                self.mech_logger.logger.info({"info":"Heater power value changed in GUI"})
            else:
                self.mech_logger.logger.error("E105: Heater power Input out of range!")
                self.print_to_console({"error":"E105: Heater power Input out of range!"})
                lineEdit.setStyleSheet(self.error_style_pink)


        except Exception as e:
            self.mech_logger.logger.info(f"E106: Invalid input given - Input must be integer \n {e}")
            self.print_to_console({"error":f"E106: Invalid input given - Input must be integer \n {e}"})
            lineEdit.setStyleSheet(self.error_style_pink)           

    def update_heater_pwm(self,lineEdit, var):
        try:
            var = float(lineEdit.text())

            if var<=0.3 and var>=0:
                self.print_to_console({"info":"Heater PWM value changed in GUI"})
                self.mech_logger.logger.info({"info":"Heater PWM value changed in GUI"})
            else:
                self.mech_logger.logger.error("E105: Heater PWM Input out of range!")
                self.print_to_console({"error":"E105: Heater PWM Input out of range!"})
                lineEdit.setStyleSheet(self.error_style_pink)


        except Exception as e:
            self.mech_logger.logger.info(f"E106: Invalid input given - Input must be integer \n {e}")
            self.print_to_console({"error":f"E106: Invalid input given - Input must be integer \n {e}"})
            lineEdit.setStyleSheet(self.error_style_pink)           

    # fetching PWM and power values and displaying it
    def update_pwm_power_display(self):
        data = self.config_editor.read_values()
        max_power=[]
        pwm_cycle_time=[]
        
        try:
            for key in data:
                max_power.append(data[key]['max_power'])
                pwm_cycle_time.append(data[key]['pwm_cycle_time'])

            self.hPower_1.setText(str(max_power[0]))
            self.hPower_2.setText(str(max_power[1]))
            self.hPower_3.setText(str(max_power[2]))
            self.hPower_4.setText(str(max_power[3]))
            self.hPower_5.setText(str(max_power[4]))
            self.hPower_6.setText(str(max_power[5]))
            self.hPower_7.setText(str(max_power[6]))
            self.hPower_9.setText(str(max_power[7]))
            self.hPower_10.setText(str(max_power[8]))
            self.hPower_11.setText(str(max_power[9]))
            self.hPower_12.setText(str(max_power[10]))
            self.hPower_13.setText(str(max_power[11]))
            self.hPower_14.setText(str(max_power[12]))
            self.hPower_15.setText(str(max_power[13]))
            self.hPower_16.setText(str(max_power[14]))
        
            self.hPWM_1.setText(str(pwm_cycle_time[0]))
            self.hPWM_2.setText(str(pwm_cycle_time[1]))
            self.hPWM_3.setText(str(pwm_cycle_time[2]))
            self.hPWM_4.setText(str(pwm_cycle_time[3]))
            self.hPWM_5.setText(str(pwm_cycle_time[4]))
            self.hPWM_6.setText(str(pwm_cycle_time[5]))
            self.hPWM_7.setText(str(pwm_cycle_time[6]))
            self.hPWM_9.setText(str(pwm_cycle_time[7]))
            self.hPWM_10.setText(str(pwm_cycle_time[8]))
            self.hPWM_11.setText(str(pwm_cycle_time[9]))
            self.hPWM_12.setText(str(pwm_cycle_time[10]))
            self.hPWM_13.setText(str(pwm_cycle_time[11]))
            self.hPWM_14.setText(str(pwm_cycle_time[12]))
            self.hPWM_15.setText(str(pwm_cycle_time[13]))
            self.hPWM_16.setText(str(pwm_cycle_time[14]))

        except Exception as e:
            self.mech_logger.logger.error({"Error in fetching initial heater power and pwm values \n {e}"})
            self.print_to_console({"error":"Error in fetching initial heater power and pwm values \n {e}"})

    # fetch and display temperature values
    def update_temperatures(self, value):
        tempValue = value[0]
        widget = value[1]

        page1_widget = widget[0]
        page2_widget = widget[1]


        if tempValue == "1984.0000":
            page1_widget.setText("No connection")
            page2_widget.setText("----")
        else:
            page1_widget.setText(str(tempValue))
            page2_widget.setText(str(tempValue))
    ###################### Cycle loop functions ############

    # function to take input for count field of gui
    def count_edit(self):
             
        try:
            # take input from ui
            self.num = int(self.cycleCount.text())

            # check whether given input is within range
            if self.num > 0 and self.num<101:
                self.count = self.num
                self.mech_logger.logger.info("Count value updated in GUI!")
                self.update_console_signal.emit({"info":"Count value updated in GUI!"})

            else:
                self.mech_logger.logger.error("E105 : Range Error!! - Given input out of range!!")
                self.update_console_signal.emit({"error":"E105 : Range Error!! - Given input out of range!!"})
                self.cycleCount.setStyleSheet(self.error_style)


        except Exception as e:
            self.mech_logger.logger.error(f"E106 : Invalid input given!! \n {e}")
            self.update_console_signal.emit({"error":f"E106 : Invalid input given!! \n {e}"})
            self.cycleCount.setStyleSheet(self.error_style)

    # function describing the cycle test automation loop
    def cycleStart(self):
        # do the speed to pwm conversion
        #self.recoater_pwm = self.speed_to_pwm(self.recoater_speed)
        #self.roller_pwm = self.speed_to_pwm(self.roller_speed)

        for i in range(self.count):
            self.worker.update_count_signal.emit(str(i+1))
            # self.hopper_choice = "left"
            # # self.hopper_instance.dose()
            # self.recoater_instance.set_recoater_speed()
            self.recoater_instance.recoater_go_right()
            time.sleep(3)
            self.Z_instance.move_z_down(0.1)

            # # self.hopper_choice = "right"
            # # self.hopper_instance.dose()
            self.recoater_instance.recoater_go_left()
            time.sleep(3)
            self.Z_instance.move_z_down(0.1)

     

    # function used to update count value in gui
    def update_count(self, text):
        self.currentCount.setText(text)

    # function which handles the cycle test automation loop
    def cycleLoop(self):
        self.worker.update_count_signal.connect(self.update_count)
        self.worker.update_z_signal.connect(self.update_z_widget)
        self.worker.start()


    # function activated when cycle stop button is pressed  
    def cycleStop(self):
        self.mech_logger.logger.info("Cycle loop STOP initiated")
        self.update_console_signal.emit({"error":"Cycle loop stop initiated"})

        # stop recoater
        self.recoater_instance.recoater_stop()

    ######## monitoring functions 
    def check_klipper_connection(self):
        self.mech_code_handler_instance.check_connection()

    def update_network_status(self, status):
        if status:
            self.mechStatus.setStyleSheet("""
                                          border-radius:7px;
                                            border:none;
                                            background-color: green;
                                          color:white;
                                          """)
        else:
            self.mechStatus.setStyleSheet("""
                                          border-radius:7px;
                                            border:none;
                                            background-color: red;
                                          color:white;
                                          """)
            
    def update_templogger_status(self, status):
        if status:
            self.tempStatus.setStyleSheet("""
                                          border-radius:7px;
                                            border:none;
                                            background-color: green;
                                          color:white;
                                          """)
        else:
            self.tempStatus.setStyleSheet("""
                                          border-radius:7px;
                                            border:none;
                                            background-color: red;
                                          color:white;
                                          """)
            
            self.ch1.setText("No Connection")
            self.ch2.setText("No Connection")
            self.ch3.setText("No Connection")
            self.ch4.setText("No Connection")
            self.ch5.setText("No Connection")
            self.ch6.setText("No Connection")
            self.ch7.setText("No Connection")
            self.ch8.setText("No Connection")
            self.ch9.setText("No Connection")
            self.ch10.setText("No Connection")
            self.ch11.setText("No Connection")
            self.ch12.setText("No Connection")
            self.ch13.setText("No Connection")
            self.ch14.setText("No Connection")
            self.ch15.setText("No Connection")
            self.ch16.setText("No Connection")
            


    def update_scancard_status(self, status):
        if status:
            self.scancardStatus.setStyleSheet("""
                                          border-radius:7px;
                                            border:none;
                                            background-color: green;
                                          color:white;
                                          """)
        else:
            self.scancardStatus.setStyleSheet("""
                                          border-radius:7px;
                                            border:none;
                                            background-color: red;
                                          color:white;
                                          """)




    ##### other mechanical control functions

    # function activated when laser window button is clicked
    def lWindow_button_click(self):
       
       # check current state of laser window
        if self.laserWindowOpen:
            # close window in case it was previously open
            self.mech_code_handler_instance.laser_window_close()
            
        else: 
            # open window in case it was previously closed
            self.mech_code_handler_instance.laser_window_open()

    def machine_shutdown(self):
        # stop the other threads running
        self.tempLoggerIsRunning = False
        self.networkCheckIsRunning = False
        self.scancardCheckIsRunning = False

        time.sleep(2)
        # turn off mechanical part of the machine
        self.mech_code_handler_instance.machine_shutdown()

    def emergency_stop(self):
        self.mech_code_handler_instance.emergency_stop()

        if self.printWorker.is_running:
            self.printWorker.terminate()
            self.printWorker.wait()
            self.print_to_console({"info":"Print Thread terminated"})

        self.chamber_instance.cooldownBuildChamber


   ########################### styling related ################

    # function to return to default styling after invalid input is erased
    def reset_line_edit_style(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                border-radius: 7px;
                border: none;
                background-color: #fef5f4;
                color: black;
            }
        """)

    def reset_line_edit_style_pink(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                border-radius: 7px;
                border: none;
                background-color: rgba(232,154,155,255);
                color: black;
            }
        """)

    # function for 'activated' effect for blue buttons
    def activate_button_z(self, widget):
        widget_list = [self.z001, self.z01,self.z1, self.z10, self.z100]

        for i in widget_list:
            if i == widget:
                      widget.setStyleSheet("""
                        background-color: #9ceefb;
                        border-radius:7px;
                        border:3px solid #9ceefb;
                        border-style: groove;
                    """)
            else:
                i.setStyleSheet("""
                    background-color: #9cd0ff;
                    border-radius:7px;
                    border:3px solid #9cd0ff;
                    border-style: groove;
            """)  
    
    def activate_button_hDistance(self, widget):
        widget_list = [self.h10mm, self.h8mm, self.h6mm]

        for i in widget_list:
            if i == widget:
                      widget.setStyleSheet("""
                        background-color: #9ceefb;
                        border-radius:7px;
                        border:3px solid #9ceefb;
                        border-style: groove;
                    """)
            else:
                i.setStyleSheet("""
                    background-color: #9cd0ff;
                    border-radius:7px;
                    border:3px solid #9cd0ff;
                    border-style: groove;
            """)  
                

    def activate_button_hTime(self, widget):
        widget_list = [self.h1sec, self.h3sec,self.h5sec]

        for i in widget_list:
            if i == widget:
                      widget.setStyleSheet("""
                        background-color: #9ceefb;
                        border-radius:7px;
                        border:3px solid #9ceefb;
                        border-style: groove;
                    """)
            else:
                i.setStyleSheet("""
                    background-color: #9cd0ff;
                    border-radius:7px;
                    border:3px solid #9cd0ff;
                    border-style: groove;
            """)  
                
    def activate_button_hSelect(self, widget):
        widget_list = [self.lHopper, self.rHopper]

        for i in widget_list:
            if i == widget:
                      widget.setStyleSheet("""            
border-radius:7px;
border:3px solid #a6a6a6;
background-color:#a6a6a6;
border-style: groove;

                    """)
            else:
                i.setStyleSheet("""
               border-radius:7px;
border:3px solid rgba(232,154,155,255);
background-color: rgba(232,154,155,255);
border-style: groove;
                    """)
                
########################## Laser operations ################

    # to upload file into ui
    def upload_file_button_click(self):
        print("Upload directory button clicked")
        self.dirName = QFileDialog.getExistingDirectory(self, "Select Directory")

        # if a directory is successfully selected
        if self.dirName:
            self.laser_logger.logger.info(f"Opening directory {self.dirName}...")
            self.update_console_signal.emit({"info": f"Opening directory {self.dirName}..."})
            self.scancard_instance.get_directory(self.dirName)  # Assuming `get_directory` handles directories


    # editing jump delay parameter
    def jDelay_edit(self):

        try:
            # reading value from ui input field
            self.jumpDelay = int(self.jDelay.text())

             # checking if value if within acceptable range, if it is then we save it as global variable
            if self.jumpDelay <= 5000 and self.jumpDelay>= 1:
                self.laser_logger.logger.info(f"GUI jump delay value is set to {self.jumpDelay}")
                self.update_console_signal.emit({"info":f"GUI jump delay value is set to {self.jumpDelay}"})
                
            else:
                self.laser_logger.logger.error("E206: Jump delay Input out of range!")
                self.update_console_signal.emit({"error":"E206: Jump delay Input out of range!"})
                self.jDelay.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.jDelay.setStyleSheet(self.error_style)
        
    # editing laser on delay parameter
    def LOnDelay_edit(self):
    
        try:
            # reading value from ui input field
            self.laserOnDelay = float(self.LOnDelay.text())

            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.laserOnDelay <= 5000 and self.laserOnDelay >= -500000:
                self.laser_logger.logger.info(f"GUI laser on delay value is set to {self.laserOnDelay}")
                self.update_console_signal.emit({"info":f"GUI laser on delay value is set to {self.laserOnDelay}"})

            else:
                self.laser_logger.logger.error("E206: laser on delay Input out of range!")
                self.update_console_signal({"error":"E206: laser on delay Input out of range!"})
                self.LOnDelay.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.LOnDelay.setStyleSheet(self.error_style)


    # editing laser off delay parameter
    def LOffDelay_edit(self):

        try:
            # reading value from ui input field
            self.laserOffDelay = int(self.LOffDelay.text())

            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.laserOffDelay <= 5000 and self.laserOffDelay >= 0:
                self.laser_logger.logger.info(f"GUI laser Off delay value is set to {self.laserOffDelay}")
                self.update_console_signal.emit({"info":f"GUI laser Off delay value is set to {self.laserOnDelay}"})
            else:
                self.laser_logger.logger.error("E206: laser Off delay Input out of range!")
                self.update_console_signal.emit({"error":"E206: laser Off delay Input out of range!"})
                self.LOffDelay.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.print_to_console({"error":"E207: Invalid input given - Input must be integer \n {e}"})
            self.LOffDelay.setStyleSheet(self.error_style)

    # editing polygonKillerTime parameter
    def pKiller_edit(self): 

        try:
            # reading value from ui input field
            self.polygonKillerTime = int(self.pkDelay.text())

            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.polygonKillerTime <= 1000 and self.polygonKillerTime >= 0:
                self.laser_logger.logger.info(f"GUI Pulse killer Time value is set to {self.polygonKillerTime}")
                self.update_console_signal.emit({"info":f"GUI Pulse killer Time value is set to {self.polygonKillerTime}"})
            else:
                self.laser_logger.logger.error("E206: Pulse killer Time Input out of range!")
                self.update_console_signal.emit({"error":"E206: Pulse killer Time Input out of range!"})
                self.pkDelay.setStyleSheet(self.error_style)
        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.pkDelay.setStyleSheet(self.error_style)

    # editing polygon delay parameter
    def pDelay_edit(self):

        try:
            # reading value from ui input field
            self.polygonDelay = int(self.pDelay.text())

            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.polygonDelay <= 2000 and self.polygonDelay >= 0.0001:
                self.laser_logger.logger.info(f"GUI Pulse delay value is set to {self.polygonDelay}")
                self.update_console_signal.emit({"info":f"GUI Pulse delay value is set to {self.polygonDelay}"})
            else:
                self.laser_logger.logger.error("E206: Pulse delay Input out of range!")
                self.update_console_signal.emit({"error":"E206: Pulse delay Input out of range!"})
                self.pDelay.setStyleSheet(self.error_style)
        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.pDelay.setStyleSheet(self.error_style)

    # editing first pulse width parameter
    def fpulsewidth_edit(self):

        try:
            # reading value from ui input field
            self.firstPulseWidth = int(self.fpWidth.text())


            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.firstPulseWidth <= 100 and self.firstPulseWidth >= 0.00063:
                self.laser_logger.logger.info(f"GUI First pulse width value is set to {self.firstPulseWidth}")
                self.update_console_signal.emit({"info":f"GUI First pulse width value is set to {self.firstPulseWidth}"})
            else:
                self.laser_logger.logger.error("E206: First pulse width Input out of range!")
                self.update_console_signal.emit({"error":"E206: First pulse width Input out of range!"})
                self.fpWidth.setStyleSheet(self.error_style)
        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.fpWidth.setStyleSheet(self.error_style)

    # editing first pulse killer length parameter
    def fpkLength_edit(self):

        try:
            # reading value from ui input field
            self.firstPulseKillerLength = int(self.fpkLength.text())

             # checking if value if within acceptable range, if it is then we save it as global variable
            if self.firstPulseKillerLength < 1000:
                self.laser_logger.logger.info(f"GUI First pulse killer length value is set to {self.firstPulseKillerLength}")
                self.update_console_signal.emit({"info":f"GUI First pulse killer length value is set to {self.firstPulseKillerLength}"})
            else:
                self.laser_logger.logger.error("E206: First pulse killer length Input out of range!")
                self.update_console_signal.emit({"error":"E206: First pulse killer length Input out of range!"})
                self.fpkLength.setStyleSheet(self.error_style)
        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.fpkLength.setStyleSheet(self.error_style)

    # editing pulse width parameter
    def pWidth_edit(self):

        try:
            # reading value from ui input field
            self.pulseWidth = int(self.pWidth.text())

             # checking if value if within acceptable range, if it is then we save it as global variable
            if self.pulseWidth <= 100 and self.pulseWidth >= 0.00063:
                self.laser_logger.logger.info(f"GUI Pulse width value is set to {self.pulseWidth}")
                self.update_console_signal.emit({"info":f"GUI Pulse width value is set to {self.pulseWidth}"})
            else:
                self.laser_logger.logger.error("E206: Pulse width Input out of range!")
                self.update_console_signal.emit({"error":"E206: Pulse width Input out of range!"})
                self.pWidth.setStyleSheet(self.error_style)
        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.pWidth.setStyleSheet(self.error_style)

    # editing laser frequency parameter
    def lFreq_edit(self):

        try:
             # reading value from ui input field
            self.laserfreq = int(self.lFreq.text())

             # checking if value if within acceptable range, if it is then we save it as global variable
            if self.laserfreq <= 50 and self.laserfreq>= 1:
                self.laser_logger.logger.info(f"GUI laser frequency value is set to {self.laserfreq}")
                self.update_console_signal.emit({"info":f"GUI laser frequency value is set to {self.laserfreq}"})
            else:
                self.laser_logger.logger.error("E206: laser frequency Input out of range!")
                self.update_console_signal.emit({"error":"E206: laser frequency Input out of range!"})
                self.lFreq.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.print_to_console({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.lFreq.setStyleSheet(self.error_style)

    # editing jump speed parameter
    def jSpeed_edit(self):

        try:
            # reading value from ui input field
            self.jumpSpeed = int(self.jSpeed.text())

            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.jumpSpeed <= 20000 and self.jumpSpeed >=2:
                self.laser_logger.logger.info(f"GUI jump speed value is set to {self.jumpSpeed}")
                self.update_console_signal.emit({"info":f"GUI jump speed value is set to {self.jumpSpeed}"})
            else:
                self.laser_logger.logger.error("E206: jump speed Input out of range!")
                self.update_console_signal.emit({"error":"E206: jump speed Input out of range!"})
                self.jSpeed.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.jSpeed.setStyleSheet(self.error_style)

    # editing mark speed parameter
    def mSpeed_edit(self):

        try:
            # reading value from ui input field
            self.markSpeed = int(self.mSpeed.text())

            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.markSpeed <= 20000 and self.markSpeed >= 2:
                self.laser_logger.logger.info(f"GUI Mark speed value is set to {self.markSpeed}")
                self.update_console_signal.emit({"info":f"GUI Mark speed value is set to {self.markSpeed}"})
            else:
                self.laser_logger.logger.error("E206: Mark speed Input out of range!")
                self.update_console_signal.emit({"error": "E206: Mark speed Input out of range!"})
                self.mSpeed.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.mSpeed.setStyleSheet(self.error_style)

    # editing increment step parameter
    def iStep_edit(self):

        try:
            # reading value from ui input field
            self.incrementStep = int(self.iStep.text())

            # checking if value if within acceptable range, if it is then we save it as global variable
            if self.incrementStep <=100 and self.incrementStep >= 1:
                self.laser_logger.logger.info(f"GUI increment step value is set to {self.incrementStep}")
                self.update_console_signal.emit({"info":f"GUI increment step value is set to {self.incrementStep}"})
            else:
                self.laser_logger.logger.error("E206: increment step Input out of range!")
                self.addConsoleItem({"error":"E206: increment step Input out of range!"})
                self.iStep.setStyleSheet(self.error_style)

        except Exception as e:
            self.laser_logger.logger.error(f"E207: Invalid input given - Input must be integer \n {e}")
            self.update_console_signal.emit({"error":f"E207: Invalid input given - Input must be integer \n {e}"})
            self.iStep.setStyleSheet(self.error_style)

    ######################## print loop related #################

    # start print thread
    def start_print_button_click(self):
        self.printWorker.start()
    

    def update_layer_numbers(self):
        self.cycleCount.setText(str(self.count))
        


    # function handling print loop
    def print_loop(self):
        self.initial_print_settings()

        self.print_to_console({"info":"Printing started"})
        self.print_to_console({"info":f"Total layers to print: {self.count}"})

        if self.count%2 == 0:
            loop_runs = self.count//2

            layer = 0
            self.layer_count = layer + 1
            for i in range(loop_runs):
                # update layer number and build percentage on gui
                self.printWorker.update_layer_signal.emit(str(i))
            


                ########## left ########



                self.move_z_012()
                self.dose_powder_left()
                # self.print_heating_process()
                # self.temp_check()
                self.laser_etching_for_one_layer()
                # self.post_marking_code()
            
                layer = layer + 1
                self.layer_count=+1
                self.printWorker.update_layer_signal.emit(str(layer))
                self.print_to_console({"info":f"Layer {str(layer)} printing done!!!"})
                ####### right #######

                self.move_z_012()
                self.dose_powder_right()
                # self.print_heating_process()
                # self.temp_check()
                self.laser_etching_for_one_layer()
                # self.post_marking_code()

                if i != loop_runs -1:
                    layer = layer + 1
                    self.layer_count=+1
                    self.printWorker.update_layer_signal.emit(str(layer))
                    self.print_to_console({"info":f"Layer {str(layer)} printing done!!!"})
                else:
                   self.print_to_console({"info":f"Printing done"}) 
                   self.buildPercentage.setText(f"100.0 %")

       

        else:
            loop_runs = self.count//2
            layer = 0
            self.layer_count = layer

            for i in range(loop_runs):
                # update layer number and build percentage on gui
                self.printWorker.update_layer_signal.emit(str(i))


                ########## left ########

                self.move_z_012()
                self.dose_powder_left()
                # self.print_heating_process()
                # self.temp_check()
                self.laser_etching_for_one_layer()
                # self.post_marking_code()
            
                layer = layer + 1
                self.layer_count=+1
                self.printWorker.update_layer_signal.emit(str(layer))
                self.print_to_console({"info":f"Layer {str(layer)} printing done!!!"})
                ####### right #######

                self.move_z_012()
                self.dose_powder_right()
                # self.print_heating_process()
                # self.temp_check()
                self.laser_etching_for_one_layer()
                # self.post_marking_code()

                self.move_z_012()
                layer = layer + 1
                self.layer_count=+1
                self.printWorker.update_layer_signal.emit(str(layer))
                self.print_to_console({"info":f"Layer {str(layer)} printing done!!!"})

            self.dose_powder_left()
            # self.temp_check()
            self.layer_count=+1
            self.laser_etching_for_one_layer()
            
            self.buildPercentage.setText(f"100.0 %")

    def move_z_012(self):
        try:
            self.mech_code_handler_instance.pre_layer_new_code("FORCE_MOVE stepper=stepper_z distance=0.12 velocity=2.5")
            # self.mech_code_handler_instance.pre_layer_new_code("G4 P1000") # delay
            # self.mech_code_handler_instance.pre_layer_new_code("FORCE_MOVE stepper=stepper_z distance=-10.0 velocity=2.5") # Z axis

        except Exception as e:
            self.mech_logger.logger.error("Error while executing pre layer new code")
            self.print_to_console({"error":"Error while executing pre layer new code"})


    def temp_check(self):
        while(abs(self.targetTemp- self.ch1_actual_temp) > 2 ):
            time.sleep(5)

        self.print_to_console({"info":f"Target temp {str(self.ch1_actual_temp)} reached"})
        self.mech_logger.logger.info(f"Target temp {str(self.ch1_actual_temp)} reached")



    def post_marking_code(self):
        # code to know if it is positive or negative slope
        temp_slope_decreasing = False

        while(temp_slope_decreasing!=True):
            time.sleep(5)
            if self.temp_slope < 0:
                temp_slope_decreasing = True
                break

        if (temp_slope_decreasing == True) and (self.ch1_actual_temp < self.targetTemp):
            if self.hopper_choice == "left":
                self.recoater_instance.recoater_go_right()
            else:
                self.recoater_instance.recoater_go_left()
            time.sleep(5)

    def setTargetTemp(self,temp):
        self.targetTemp = float(temp)



    def calculate_elapsed_time(self):
        elapsed = time.time() - self.start_time
        elapsed_time = (int(elapsed // 60),int(elapsed % 60))
        self.printWorker.update_elapsed_time.emit(elapsed_time)

    def update_layer(self,text):
        self.layerNum.setText(str((int(text) + 1)))
        self.buildPercentage_value = round(float(text)/self.count*100, 2)
        self.buildPercentage.setText(f"{str(self.buildPercentage_value)} %")

    def update_elapsed_time(self,tuple):
        min = tuple[0]
        sec = tuple[1]
        text = (f"{min:02}:{sec:02}")
        self.timeElapsed.setText(text)

    def dose_powder_left(self):
            self.hopper_choice = "left"
            self.calculate_elapsed_time() # after each command, update timer value on gui

            # self.hopper_instance.dose()
            self.calculate_elapsed_time()

            self.hopper_instance.open_LHopper()
            time.sleep(10)
            self.recoater_instance.recoater_go_right()
            time.sleep(5)
            # self.calculate_elapsed_time()

    def dose_powder_right(self):
        self.hopper_choice = "right"
        self.calculate_elapsed_time() # after each command, update timer value on gui

        # self.hopper_instance.dose()
        self.calculate_elapsed_time()

        self.hopper_instance.open_RHopper()
        time.sleep(10)
        self.recoater_instance.recoater_go_left()
        time.sleep(5)
        self.calculate_elapsed_time()

    def print_heating_process(self):

        pass

    def laser_etching_for_one_layer(self):
        self.calculate_elapsed_time() # after each command, update timer value on gui

        self.mech_code_handler_instance.laser_window_open()
        self.print_to_console({"info":"Laser window opened"})

        self.scancard_instance.one_layer_automation()
        self.calculate_elapsed_time()

        self.mech_code_handler_instance.laser_window_close()
        self.calculate_elapsed_time()

        # self.Z_instance.move_z_down(1)
        self.calculate_elapsed_time()

    def initial_print_settings(self):
        self.start_time = time.time()
        self.buildPercentage_value = 0
        self.Z_instance.home_z()
        self.print_to_console({"info":"Delay of 105 s"})
        self.mech_logger.logger.info("Delay of 105 s")
        time.sleep(105)
        self.recoater_instance.recoater_go_left()
        time.sleep(5)

        # # heater on
        self.chamber_instance.setChamberPIDTemp()

        # self.temp_check()




    # function to stop print
    def stop_print_button_click(self):
        # print("Stop print button pressed!!")
        self.scancard_instance.stop_mark()


if __name__ == "__main__":
    app=QApplication(sys.argv)
    UI = gui("main")
    app.exec_()