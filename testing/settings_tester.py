#!/usr/bin/env python3

from util.settings_handler import SettingsHandler
import numpy as np
import time
import matplotlib.pyplot as plt

settings_handler = SettingsHandler("cw_settings.json", additional_path="cw")

times = []
num = 1000
for i in range(num):
    print(f"iteration {i}/{num}", end="\r")
    start = time.time()
    settings_handler.change_setting("velocity", i)
    end = time.time()
    times.append(end - start)


plt.title("Time to change setting")
plt.plot(times)
plt.show()

print(f"Average time to change setting: {np.mean(times)}")


times.clear()

for i in range(num):
    print(f"iteration {i}/{num}", end="\r")
    start = time.time()
    settings_handler.read_settings()
    end = time.time()
    times.append(end - start)

plt.title("Time to read settings")
plt.plot(times)
plt.show()

print(f"Average time to read settings: {np.mean(times)}")

times.clear()

for i in range(num):
    print(f"iteration {i}/{num}", end="\r")
    start = time.time()
    settings_handler.change_setting("velocity", i)
    test = settings_handler.get_changed_settings()
    print(test, end="\r")
    end = time.time()
    times.append(end - start)


plt.title("Time to change setting and get changed settings")
plt.plot(times)
plt.show()

print(f"Average time to change setting and get changed settings: {np.mean(times)}")
