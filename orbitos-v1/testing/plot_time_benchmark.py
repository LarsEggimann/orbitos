import numpy as np
import pandas as pd
import plotly.express as px

df_non_optimized = pd.read_csv(
    r"code/testing/numb_of_datapoints_vs_time_to_read_before_optimization.csv"
)
df_optimized = pd.read_csv(
    r"code/testing/numb_of_datapoints_vs_time_to_read_after_optimization.csv"
)

df_non_optimized["optimized"] = False
df_optimized["optimized"] = True
df = pd.concat([df_non_optimized, df_optimized])
print(df)

fig = px.scatter(
    df,
    x="numb_of_points",
    y="time",
    labels={"numb_of_points": "Number of Data Points", "time": "Time to Read [s]"},
    title="Number of Data Points vs Time to Read Before Optimization",
    color="optimized",
)
fig.show()

# calculate the average time to read after 5000 data points for the optimized and non-optimized version
df_5000 = df[df["numb_of_points"] >= 5000]

average_time_non_optimized = df_5000[df_5000["optimized"] == False]["time"].mean()
average_time_optimized = df_5000[df_5000["optimized"] == True]["time"].mean()

print(
    f"Average time to after more than 5000 data points before optimization: {average_time_non_optimized}"
)
print(
    f"Average time to after more than 5000 data points after optimization: {average_time_optimized}"
)

# calculate the percentage of times it took less than 0.001s to read the data for the optimized and non-optimized version
df_less_than_001 = df[df["time"] < 0.001]

percentage_less_than_001_non_optimized = (
    df_less_than_001[df_less_than_001["optimized"] == False].shape[0]
    / df[df["optimized"] == False].shape[0]
    * 100
)
percentage_less_than_001_optimized = (
    df_less_than_001[df_less_than_001["optimized"] == True].shape[0]
    / df[df["optimized"] == True].shape[0]
    * 100
)

print(
    f"Percentage of times it took less than 0.001s to read the data before optimization: {percentage_less_than_001_non_optimized}%"
)
print(
    f"Percentage of times it took less than 0.001s to read the data after optimization: {percentage_less_than_001_optimized}%"
)
