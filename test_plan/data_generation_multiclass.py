import random
reader = open("./data/tox21.csv", "r")
lines = reader.readlines()
reader.close()
num_class = 10
num_data = 300

import random

lines[0] = "smiles,task1,task2,task3"

for i in range(1, num_data):
    index = lines[i].index(",")
    random_1 = random.randint(0, num_class-1)
    random_2 = random.randint(0, num_class-1)
    random_3 = random.randint(0, num_class-1)
    lines[i] = lines[i][:index] + "," + str(random_1) + "," + str(random_2) + "," + str(random_3)

writer = open("./data/tox21_3class1.csv", "w")
for line in lines[:100]:
    writer.write(line + "\n")

writer.close()

writer = open("./data/tox21_3class2.csv", "w")
writer.write(lines[0]+"\n")
for line in lines[100:200]:
    writer.write(line + "\n")

writer.close()

writer = open("./data/tox21_3class3.csv", "w")
writer.write(lines[0]+"\n")
for line in lines[200:300]:
    writer.write(line + "\n")

writer.close()