import matplotlib.pyplot as plt

points_x = []
points_y = []

with open("data.txt", "r") as file:
    for line in file.readlines():
        if "TAG" in line:
            line = line.split(" ")
            points_x.append(float(line[1]))
            points_y.append(float(line[3]))

with open("calculated.csv", "w") as file:
    for i, x in enumerate(points_x):
        file.write(str(x) + "," + str(points_y[i]) + "\n")

plt.plot(points_x, points_y, "ro")

plt.show()