import logging
import os
import csv
from datetime import datetime

class CSVLogger:
    def __init__(self):
        # Create custom logger and set the level
        self.heater_logger = logging.getLogger(__name__)
        self.heater_logger.setLevel(logging.INFO)

        ########### for heater logs
        # Define the CSV header
        self.header = ['Timestamp', 'Heater', 'Max Power', 'PWM Cycle Time','ch1','ch2','ch3','ch4','ch5','ch6','ch7','ch8','ch9','ch10','ch11','ch12','ch13','ch14','ch15','ch16']

        # Formatter for logging
        self.formatter = logging.Formatter(
            "{asctime},{message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Avoid duplicate handlers
        if self.heater_logger.hasHandlers():
            self.heater_logger.handlers.clear()

        # Prevent logger from propagating to the root logger
        self.heater_logger.propagate = False

        # Create directory for CSV logs if it doesn't exist
        if not os.path.exists('heater_logs'):
            os.makedirs('heater_logs')

        # Get the current timestamp and create a filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"heaterLog_{timestamp}.csv"

        # Define the path for the CSV file
        self.log_file_path = os.path.join("heater_logs", log_filename)

        # Create the CSV file and write the header
        with open(self.log_file_path, mode='w', newline='', encoding='utf-8') as heater_file:
            csv_writer = csv.writer(heater_file)
            csv_writer.writerow(self.header)

        # Set the file handler to log to CSV file
        self.file_handler = logging.FileHandler(self.log_file_path, mode="a", encoding="utf-8")
        self.file_handler.setFormatter(self.formatter)

        # Add the file handler to the logger
        self.heater_logger.addHandler(self.file_handler)

    def log_heater_config(self, heater, max_power, pwm_cycle_time):
        # Format the message with the provided values
        message = f"{heater},{max_power},{pwm_cycle_time}, , , , , , , , , , , , , , , , "
        # Log the message
        self.heater_logger.info(message)
        # Flush the logger to ensure data is written to the file
        for handler in self.heater_logger.handlers:
            handler.flush()


    def log_temp(self, temp_list):
        # Format the message with the provided values
        message = f" , , ,{temp_list[0]},{temp_list[1]},{temp_list[2]},{temp_list[3]},{temp_list[4]},{temp_list[5]},{temp_list[6]},{temp_list[7]},{temp_list[8]},{temp_list[9]},{temp_list[10]},{temp_list[11]},{temp_list[12]},{temp_list[13]},{temp_list[14]}"
        
        # Log the message
        self.heater_logger.info(message)



# Example usage
if __name__ == "__main__":
    csv_logger = CSVLogger()
    csv_logger.log_heater_config('chamber heater 1', '0.25','0.10')

    t = [26,26,26,26,26,26,26,26,26,26,26,26,26,26,26]
    csv_logger.log_temp(t)