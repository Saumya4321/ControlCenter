import paramiko
import re
from ErrorLogging3 import ErrorLogger

class ConfigEditor:

    def __init__(self, parent=None):
        # Define variables
        self.REMOTE_USER = "pi"
        self.REMOTE_HOST = "192.168.0.231"
        self.PASSWORD = "pi"  # Password for SSH
        self.parent = parent

        ##### Initializing the loggers needed #####

        # Initialize the Error Logger
        self.mech_error_logger = ErrorLogger()  # Initialize this first

        # Assign the logger to the parent if a parent is provided
        if self.parent:
            self.mech_error_logger = self.parent.mech_logger


    def execute_ssh_command(self, ssh, command):
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Wait for the command to complete
        return stdout.read().decode(), stderr.read().decode()
    
    def fetch_data_from_file(self,filepath):
        # Path to the file
        file_path = filepath

        # Variables to store the data
        heater_data = {}

        # Regular expressions to match section, max_power, and pwm_cycle_time
        section_regex = re.compile(r"\[(.+?)\]")
        max_power_regex = re.compile(r"max_power:\s*([0-9.]+)")
        pwm_cycle_time_regex = re.compile(r"pwm_cycle_time:\s*([0-9.]+)")

        # Reading the file
        with open(file_path, "r") as file:
            current_section = None
            for line in file:
                # Check for section headers
                section_match = section_regex.match(line)
                if section_match:
                    current_section = section_match.group(1)
                    heater_data[current_section] = {"max_power": None, "pwm_cycle_time": None}
        
                # Check for max_power
                max_power_match = max_power_regex.search(line)
                if max_power_match and current_section:
                    heater_data[current_section]["max_power"] = float(max_power_match.group(1))

                # Check for pwm_cycle_time
                pwm_cycle_time_match = pwm_cycle_time_regex.search(line)
                if pwm_cycle_time_match and current_section:
                    heater_data[current_section]["pwm_cycle_time"] = float(pwm_cycle_time_match.group(1))

        del heater_data['virtual_sdcard']
        return heater_data



    def main_function(self):
        try:
            # Connect to the remote host
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.REMOTE_HOST, username=self.REMOTE_USER, password=self.PASSWORD)

            message = "Connected to the remote host.\n"
            self.mech_error_logger.logger.info(message)
            self.parent.print_to_console({"info": message})

            commands = []

            heater_template = """
[heater_generic chamber_heater{number}]
max_power: {max_power}
pwm_cycle_time: {pwm_cycle_time}
"""
            other_elements_template = """
[{element}]
max_power: {max_power}
pwm_cycle_time: {pwm_cycle_time}
"""
            # Heater parameters
            heaters = [
                {'number': 1, 'max_power': self.parent.hPower1_val, 'pwm_cycle_time': self.parent.hPWM1_val},
                {'number': 2, 'max_power': self.parent.hPower2_val, 'pwm_cycle_time': self.parent.hPWM2_val},
                {'number': 3, 'max_power': self.parent.hPower3_val, 'pwm_cycle_time': self.parent.hPWM3_val},
                {'number': 4, 'max_power': self.parent.hPower4_val, 'pwm_cycle_time': self.parent.hPWM4_val},
                {'number': 5, 'max_power': self.parent.hPower5_val, 'pwm_cycle_time': self.parent.hPWM5_val},
                {'number': 6, 'max_power': self.parent.hPower6_val, 'pwm_cycle_time': self.parent.hPWM6_val},
                {'number': 7, 'max_power': self.parent.hPower7_val, 'pwm_cycle_time': self.parent.hPWM7_val},
                {'number': 9, 'max_power': self.parent.hPower9_val, 'pwm_cycle_time': self.parent.hPWM9_val},
                {'number': 10, 'max_power': self.parent.hPower10_val, 'pwm_cycle_time': self.parent.hPWM10_val},
                {'number': 11, 'max_power': self.parent.hPower11_val, 'pwm_cycle_time': self.parent.hPWM11_val},
                {'number': 12, 'max_power': self.parent.hPower12_val, 'pwm_cycle_time': self.parent.hPWM12_val},
                {'number': 13, 'max_power': self.parent.hPower13_val, 'pwm_cycle_time': self.parent.hPWM13_val},
                {'number': 14, 'max_power': self.parent.hPower14_val, 'pwm_cycle_time': self.parent.hPWM14_val}
            ]
            other_elements = [
                {'element': 'extruder', 'max_power': self.parent.hPower15_val, 'pwm_cycle_time': self.parent.hPWM15_val},
                {'element': 'extruder1', 'max_power': self.parent.hPower16_val, 'pwm_cycle_time': self.parent.hPWM16_val}
            ]
            content = """
[virtual_sdcard]

#path: /home/dell/printer_1_data/gcodes
on_error_gcode: CANCEL_PRINT

#######Chamber IR Heater parameters###!####

""" + ''.join(heater_template.format(**heater) for heater in heaters) + ''.join(other_elements_template.format(**element) for element in other_elements)

            with open("config.cfg", "w") as file:
                file.write(content)

            with open("config.cfg", "r") as file:
                content_list = file.readlines()

            commands.append('truncate -s 0 /home/pi/printer_data/config/heater.cfg')

            for line in content_list:
                commands.append(f'echo "{line}" >> /home/pi/printer_data/config/heater.cfg')

            for command in commands:
                message = f"Executing command: {command}\n"
                self.mech_error_logger.logger.info(message)
                self.parent.print_to_console({"info": message})
                stdout, stderr = self.execute_ssh_command(ssh, command)
                if stderr:
                    message = f"Command failed: {command}\nError: {stderr}\n"
                    self.mech_error_logger.logger.error(message)
                    self.parent.print_to_console({"error": message})
                    return
                message = f"Command output: {stdout}\n"
                self.mech_error_logger.logger.info(message)
                self.parent.print_to_console({"info": message})

            message = "Operation completed successfully.\n"
            self.mech_error_logger.logger.info(message)
            self.parent.print_to_console({"info": message})

            ####### logging part ########
         
            # log changes if successful
            for entry in heaters:
                self.parent.csv_logger.log_heater_config("chamber heater" + str(entry['number']), str(entry['max_power']), str(entry['pwm_cycle_time']))
                print("chamber heater" + str(entry['number']), str(entry['max_power']), str(entry['pwm_cycle_time']))

            for entry in other_elements:
                if str(entry['element']) == 'extruder':
                    self.parent.csv_logger.log_heater_config("chamber heater15", str(entry['max_power']), str(entry['pwm_cycle_time']))
                elif str(entry['element']) == 'extruder1':
                    self.parent.csv_logger.log_heater_config("chamber heater16", str(entry['max_power']), str(entry['pwm_cycle_time']))

        except Exception as e:
            message = f"An error occurred: {str(e)}\n"
            self.mech_error_logger.logger.error(message)
            self.parent.print_to_console({"error": message})
        finally:
            ssh.close()
            message = "SSH connection closed.\n"
            self.mech_error_logger.logger.info(message)
            self.parent.print_to_console({"info": message})

    def read_values(self):
        try:
            # Connect to the remote host
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.REMOTE_HOST, username=self.REMOTE_USER, password=self.PASSWORD)

            message = "Connected to the remote host.\n"
            self.mech_error_logger.logger.info(message)

            # Use SFTP to copy the file from the remote host to the local machine
            sftp = ssh.open_sftp()
            remote_file_path = "/home/pi/printer_data/config/heater.cfg"
            local_file_path = "heater_copy.cfg"
        
            message = f"Copying file from {remote_file_path} to {local_file_path}\n"
            self.mech_error_logger.logger.info(message)
            self.parent.print_to_console({"info": message})

            # Perform the file transfer
            sftp.get(remote_file_path, local_file_path)

            message = "File transfer completed successfully.\n"
            self.mech_error_logger.logger.info(message)
            self.parent.print_to_console({"info": message})

            # Close the SFTP session
            sftp.close()
            print("closing sftp session")
            
            return self.fetch_data_from_file("heater_copy.cfg")

        except Exception as e:
            message = f"Couldn't connect to RPi\n {e}"
            self.mech_error_logger.logger.error(message)
            self.parent.print_to_console({"error":message})

        finally:
            ssh.close()

