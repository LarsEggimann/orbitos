import pytrinamic
from pytrinamic.connections import ConnectionManager
from pytrinamic.modules import TMCM1240
import time
import serial.tools.list_ports # type: ignore

pytrinamic.show_info()
# com_ports = serial.tools.list_ports.comports()
# print("Available COM ports:")
# for port in com_ports:
#     print(f" - {port.device}: {port.description}")

with ConnectionManager("--interface usb_tmcl --port /dev/ttyACM0 --data-rate 115200").connect() as my_interface:
    print(my_interface)


    module = TMCM1240(my_interface)
    motor = module.motors[0]

    print("Preparing parameters...")

    # preparing drive settings
    motor.drive_settings.max_current = 50
    motor.drive_settings.standby_current = 0
    motor.drive_settings.boost_current = 0
    motor.drive_settings.microstep_resolution = motor.ENUM.MicrostepResolution256Microsteps
    print(motor.drive_settings)

    # reference search settings
    motor.set_axis_parameter(motor.AP.ReferenceSearchMode, 8) # 8 = Search home switch in negative direction, ignore end switches.
    motor.set_axis_parameter(motor.AP.ReferenceSearchSpeed, 2000) # speed for reference search in pps
    motor.set_axis_parameter(motor.AP.ReferenceSwitchSpeed, 200) # speed for reference search in pps

    # preparing linear ramp settings
    motor.linear_ramp.max_velocity = 20000
    motor.linear_ramp.max_acceleration = 40000
    print(motor.linear_ramp)

    time.sleep(1.0)

    # set move_by relative to the actual position = 1, last target position = 0
    motor.set_axis_parameter(motor.AP.RelativePositioningOption, 0)

    # # clear position counter
    # motor.actual_position = 0

    # start rotating motor for 5 sek
    print("Rotating...")
    motor.rotate(20000)
    time.sleep(2)

    # stop rotating motor
    print("Stopping...")
    motor.stop()

    # read actual position
    print("ActualPosition = {}".format(motor.actual_position))


    print("start reference search ...")
    my_interface.reference_search(
        command_type=0, # 0 starts the search, 1 stops the search, and 2 returns the status.
        motor=0 # motor index, in this case we have only one motor, so the index is 0
    )
    
    print("Waiting for reference search to complete...")
    while not motor.get_position_reached():
        print("target position: " + str(motor.target_position) + " actual position: " + str(motor.actual_position))
        time.sleep(0.2)
    

    # read actual position
    print("ActualPosition = {}".format(motor.actual_position))

    # # short delay and move back to start
    # time.sleep(1)
    # print("Moving back to 0...")
    # motor.move_to(0, 20000)

    # # wait until position 0 is reached
    # while motor.get_position_reached() != 1:
    #     print("target position: " + str(motor.target_position) + " actual position: " + str(motor.actual_position))
    #     time.sleep(0.2)

    print("Reached reference position and set to zero")

print("\nFertig!")