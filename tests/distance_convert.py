import pandas as pd
from geopy.distance import geodesic

df = pd.read_csv("./tests/regular.csv")

for index, row in df.iterrows():
    row['xa'] /= 100
    row['ya'] /= 100

    row['xb'] /= 100
    row['yb'] /= 100

    row['xs'] /= 100
    row['ys'] /= 100

    row['a'] = geodesic((row['xs'], row['ys']), (row['xa'], row['ya'])).m
    row['b'] = geodesic((row['xs'], row['ys']), (row['xb'], row['yb'])).m
    
df.to_csv("regular_recalculated.csv")