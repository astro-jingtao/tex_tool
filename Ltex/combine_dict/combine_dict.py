with open("./dict1.txt") as f:
    dict1 = f.readlines()

with open("./dict2.txt") as f:
    dict2 = f.readlines()

dict_combine = list(set(dict1) | set(dict2))

with open("./dict_combine.txt", "w") as f:
    f.writelines(dict_combine)
