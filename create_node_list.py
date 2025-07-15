with open('node_list.txt', 'w') as f:
    for i in range(1, 16):
        f.write(f"volta{i}")
        f.write("\n")
    for i in range(1, 4):
        f.write(f"sws-2a100-0{i}")
        f.write("\n")
    for i in range(1, 9):
        f.write(f"sws-2a40-0{i}")
        f.write("\n")
    for i in range(1, 6):
        f.write(f"sws-2h100-0{i}")
        f.write("\n")
    for i in range(1, 3):
        f.write(f"sws-2l40-0{i}")
        f.write("\n")