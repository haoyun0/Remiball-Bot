import os
import random


def get_random_file(path):
    myList = []
    for root, dirs, files in os.walk(path):
        for name in files:
            myList.append(os.path.join(root, name))
    print(myList)
    return random.choice(myList)


file = get_random_file(r"D:\Data\gallery\黑猫")
print(file)
