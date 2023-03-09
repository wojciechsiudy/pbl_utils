import math, csv
from geopy.distance import geodesic

rows = []

while True:
    xa = input("xa")
    if xa == 'q':
        break
    xa = float(xa)
    ya = float(input("ya"))

    xb = float(input("xb"))
    yb = float(input("yb"))

    xs = float(input("sa"))
    ys = float(input("sa"))

    #a = math.sqrt((xs - xa)**2 + (ys - ya)**2) *60 *1852
    a = geodesic((xs, ys), (xa, ya)).m
    #b = math.sqrt((sxs - xb)**2 + (ys - yb)**2) *60 *1852
    b = geodesic((xs, ys), (xb, yb)).m

    row = (xa, ya, a, xb, yb, b, xs, ys)

    rows.append(row)

csv_name = input("\nEnter csv name\n")

with open((csv_name + '.csv'),'a+') as out:
    csv_out=csv.writer(out)
    csv_out.writerow(['xa','ya', 'a', 'xb', 'yb', 'b', 'xs', 'ys'])
    for line in rows:
        csv_out.writerow(line)

print("Saved to " + csv_name + '.csv')
    message_1 = str(current_address) + str(FRAMES_AMOUNT)