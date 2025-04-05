#!/usr/bin/env python3

from pylablib.devices import Arcus  # type: ignore
import pylablib as pll  # type: ignore
from pathlib import Path

work_dir = Path(__file__).parent.parent.parent
print(str(work_dir))
dir = str(work_dir / "controllers" / "stage" / "dll")
pll.par["devices/dlls/arcus_performax"] = dir
print(Arcus.list_usb_performax_devices())
jsa00 = Arcus.PerformaxDMXJSAStage(1)
jsa01 = Arcus.PerformaxDMXJSAStage(0)

jsa01.open()
jsa01.move_by(10000)

while jsa01.is_moving():
    print(jsa01.get_position())

print(jsa01.get_position())

jsa01.move_to(0)
while jsa01.is_moving():
    print(jsa01.get_position())

jsa01.close()
