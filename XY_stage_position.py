import clr
import sys
import os
import time
import threading
from System import Decimal

KINESIS_PATH = r"C:\Program Files\Thorlabs\Kinesis"
SERIAL_Y = "27600149"
SERIAL_X = "27750395"
STAGE_RANGE_MM = 50.0

sys.path.append(KINESIS_PATH)
os.chdir(KINESIS_PATH)
clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.DeviceManagerCLI.dll"))
clr.AddReference(os.path.join(KINESIS_PATH, "Thorlabs.MotionControl.KCube.DCServoCLI.dll"))

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo

DeviceManagerCLI.BuildDeviceList()

def setup_device(serial):
    device = KCubeDCServo.CreateKCubeDCServo(serial)
    device.Connect(serial)
    device.LoadMotorConfiguration(serial)
    device.StartPolling(250)
    device.EnableDevice()
    time.sleep(0.5)
    return device

def home_device(device, label):
    print(f"Homing {label}-axis...")
    device.Home(60000)

def move_device(device, target, label):
    print(f"Moving {label}-axis to {target:.2f} mm...")
    device.MoveTo(Decimal(target), 60000)

device_y = setup_device(SERIAL_Y)
device_x = setup_device(SERIAL_X)

thread_y = threading.Thread(target=home_device, args=(device_y, 'Y'))
thread_x = threading.Thread(target=home_device, args=(device_x, 'X'))
thread_y.start()
thread_x.start()
thread_y.join()
thread_x.join()

while True:
    try:
        target_y = float(input(f"Enter Y target (0 to {STAGE_RANGE_MM} mm): "))
        if not (0 <= target_y <= STAGE_RANGE_MM):
            print("Y value out of range.")
            continue

        target_x = float(input(f"Enter X target (0 to {STAGE_RANGE_MM} mm): "))
        if not (0 <= target_x <= STAGE_RANGE_MM):
            print("X value out of range.")
            continue

        thread_y = threading.Thread(target=move_device, args=(device_y, target_y, 'Y'))
        thread_x = threading.Thread(target=move_device, args=(device_x, target_x, 'X'))
        thread_y.start()
        thread_x.start()
        thread_y.join()
        thread_x.join()

    except ValueError:
        print("Invalid input. Please enter a number.")
        continue

    choice = input("Do you want to return both axes to 0 mm (Y/N)? ").strip().upper()
    if choice == 'Y':
        thread_y = threading.Thread(target=home_device, args=(device_y, 'Y'))
        thread_x = threading.Thread(target=home_device, args=(device_x, 'X'))
        thread_y.start()
        thread_x.start()
        thread_y.join()
        thread_x.join()
        break
    elif choice == 'N':
        continue
    else:
        print("Invalid input. Assuming 'N'.")
        continue

device_y.StopPolling()
device_y.Disconnect()
device_x.StopPolling()
device_x.Disconnect()
print("Both stages disconnected. Done.")
