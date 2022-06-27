import random
reader = open("./data/tox21.csv", "r")
lines = reader.readlines()
reader.close()
num_class = 10

for i in range(len(lines)):
    index = lines[i].index(",")
    random_class = random.randint(0, num_class)
    lines[i] = lines[i][:index+1] + str(random_class)

writer = open("./data/tox21class.csv", "w")
for line in lines:
    writer.write(line + "\n")

writer.close()