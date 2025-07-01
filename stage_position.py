import clr
import sys
import os
import time
from System import Decimal

KINESIS_PATH = r"C:\Program Files\Thorlabs\Kinesis"
SERIAL_NUMBER = "27600149"
STAGE_RANGE_MM = 50.0

sys.path.append(KINESIS_PATH)
os.chdir(KINESIS_PATH)
clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.DeviceManagerCLI.dll"))
clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.KCube.DCServoCLI.dll"))

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo

DeviceManagerCLI.BuildDeviceList()
device = KCubeDCServo.CreateKCubeDCServo(SERIAL_NUMBER)
device.Connect(SERIAL_NUMBER)
device.LoadMotorConfiguration(SERIAL_NUMBER)
device.StartPolling(250)
device.EnableDevice()
time.sleep(0.5)

print("Homing stage to position 0.0 mm...")
device.Home(60000)
time.sleep(0.5)

while True:
    try:
        target = float(input(f"Enter target position (0 to {STAGE_RANGE_MM} mm): "))
        if 0 <= target <= STAGE_RANGE_MM:
            print(f"Moving to {target:.2f} mm...")
            device.MoveTo(Decimal(target), 60000)
            time.sleep(0.5)
        else:
            print(f"Please enter a value between 0 and {STAGE_RANGE_MM}.")
            continue
    except ValueError:
        print("Invalid input. Please enter a number.")
        continue

    choice = input("Do you want to return to 0 mm (Y/N)? ").strip().upper()
    if choice == 'Y':
        print("Homing back to 0.0 mm...")
        device.Home(60000)
        break 
    elif choice == 'N':
        continue
    else:
        print("Invalid input. Assuming 'N'.")
        continue

device.StopPolling()
device.Disconnect()
print("Stage disconnected. Done.")
