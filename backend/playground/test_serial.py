import pylablib as pll



listt = pll.list_backend_resources("serial")

print("Available serial resources:")
for i, res in enumerate(listt):
    print(f"{i}: {res}")

from pylablib.devices import Arcus

stage1 = stage2 = Arcus.Performax4EXStage(conn = "COM4")

print(f"axis name {stage1._axis_parameter_name}")