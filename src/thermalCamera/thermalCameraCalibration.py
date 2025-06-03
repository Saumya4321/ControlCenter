import time
import logging
import numpy as np
import cv2 as cv

from thermal_camera import ThermalCamera  # Replace with correct import if different

logging.basicConfig(level=logging.INFO)

def get_reference_temperature():
    """Prompt the user for a known reference temperature."""
    try:
        return float(input("Enter known reference temperature (°C): "))
    except ValueError:
        logging.warning("Invalid input. Skipping calibration.")
        return None

def apply_calibration_to_temps(temps, factor):
    """Scales all temperature readings using the calibration factor."""
    return {k: v * factor for k, v in temps.items()}

import time
import numpy as np

def wait_for_stable_temperature(camera, threshold=0.2, samples=5, wait_time=1):
    """
    Wait until the temperature readings from the camera stabilize.
    Returns the stable average temperature.
    """
    stable = False
    print("Waiting for temperature to stabilize...")

    while not stable:
        temps = [np.mean(camera.get_avg_temperatures().values()) for _ in range(samples)]
        temp_range = max(temps) - min(temps)
        if temp_range < threshold:
            stable = True
            stable_temp = np.mean(temps)  # Average temperature when stable
        else:
            print(f"Temperature not stable yet (range={temp_range:.2f}°C). Retrying in {wait_time}s...")
            time.sleep(wait_time)
    print(f"Temperature stabilized at approximately {stable_temp:.2f}°C.")
    return stable_temp


def main():
    # Start the camera (in its own thread)
    camera = ThermalCamera()
    camera.start()

    stable_temperature = wait_for_stable_temperature(camera)
    print(f"Proceeding with calibration at stable temperature: {stable_temperature:.2f}°C")

    # Let the camera warm up and fill temp data
    logging.info("Warming up camera...")
    time.sleep(3)

    # Get average temperatures before calibration
    raw_temps = camera.get_avg_temperatures()
    observed_temp = raw_temps.get("middle-center")

    if observed_temp is None or observed_temp <= 0:
        logging.error("Could not read middle-center temperature for calibration.")
        return

    # Ask user for reference
    reference_temp = get_reference_temperature()
    if reference_temp is None:
        calibration_factor = 1.0
    else:
        calibration_factor = reference_temp / observed_temp
        logging.info(f"Calibration factor: {calibration_factor:.4f} (Reference: {reference_temp}, Observed: {observed_temp:.2f})")

    # Main loop: display corrected thermal feed
    while True:
        if camera.latest_frame is not None:
            # Clone to avoid modifying the original frame
            frame = camera.latest_frame.copy()
            temps = apply_calibration_to_temps(camera.get_avg_temperatures(), calibration_factor)

            # Overlay corrected temps
            y_offset = 20
            for k, v in temps.items():
                label = f"{k}: {v:.2f}°C"
                cv.putText(frame, label, (10, y_offset), cv.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                y_offset += 25

            # Show frame
            cv.imshow("Calibrated Thermal View", frame)
        
        key = cv.waitKey(1)
        if key == 27:  # ESC to exit
            break

    camera.stop()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()

# from utils import connect_senxor

# mi48, port, _ = connect_senxor(src='COM4')  # Replace 'COM3' with your actual port
# print(f"Connected to port: {port}, mi48 object: {mi48}")


