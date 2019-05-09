#!/usr/bin/python3
# Written by Nikolay Budin, 2017

import time
import sys
import colorama

colorama.init()

"""
start: s
accept: ac
reject: rj
blank: _
s _ -> ac _ ^
s 0 -> a _ >
a 0 -> b _ >
b 0 -> a _ >
a _ -> rj _ ^
b _ -> ac _ ^

"""

name = sys.argv[1]
f_inp = sys.argv[2]
delay = 1
if (len(sys.argv) > 3):
    delay = float(sys.argv[3])

def get_dir(act):
    if (act == "<"):
        return -1
    if (act == "^"):
        return 0
    if (act == ">"):
        return 1
    return 2

prog = open(name, "r")

accept = "AC"
reject = "RJ"
cur = "S"
blank = "_"

graph = dict()
nodes = set()

c = 0
for s in prog:
    if (c == 0 and s[:-1].isdecimal()):
        if (int(s) != 1):
            print("Sorry, i can't run multi-tape machine")
            exit(0)
    elif (s.startswith("start:")):
        cur = s[s.find(":") + 1:].strip()
    elif (s.startswith("accept:")):
        accept = s[s.find(":") + 1:].strip()
    elif (s.startswith("reject:")):
        reject = s[s.find(":") + 1:].strip()
    elif (s.startswith("blank:")):
        blank = s[s.find(":") + 1:].strip()
    elif (s.strip() != ""):
        tmp = s.split()
        if (len(tmp) != 6):
            print("Parse failed on line: \"" + s[:-1] + "\"")
            exit(0)
        fr = tmp[0].strip()
        ch = tmp[1].strip()
        if (tmp[2] != "->"):
            print("Parse failed on line: \"" + s[:-1] + "\"")
            exit(0)
        to = tmp[3].strip()
        new_ch = tmp[4].strip()
        act = tmp[5].strip()
        if (act == 2):
            print("Parse failed on line: \"" + s[:-1] + "\"")
            exit(0)
        graph[(fr, ch)] = [to, new_ch, get_dir(act)]
        nodes.add(fr)
    c += 1

for p in graph:
    if (graph[p][0] != reject and graph[p][0] != accept and not graph[p][0] in nodes):
        print("Warning: There's an edge leading to node \"" + graph[p][0] + "\", but this node doesn't exist")

inp = open(f_inp, "r")

pos = 0
tape_positive = inp.readline().split()
if (len(tape_positive) == 0):
    tape_positive.append(blank)
tape_negative = []

prev_l = 0

cnt_steps = 0
flag = True
while (True):
    
    cur_s = " "
    cur_symbol = ""
    if (pos < 0):
        cur_symbol = tape_negative[-pos - 1]
    else:
        cur_symbol = tape_positive[pos]

    if (flag):
        sys.stdout.write("\r")
        for i in range(len(tape_negative) - 1, -1, -1):
            if (-i - 1 == pos):
                cur_s += colorama.Fore.GREEN + colorama.Style.BRIGHT + tape_negative[i] + colorama.Style.RESET_ALL + " "
            else:
                cur_s += tape_negative[i] + " "

        for i in range(len(tape_positive)):
            if (i == pos):
                cur_s += colorama.Fore.GREEN + colorama.Style.BRIGHT + tape_positive[i] + colorama.Style.RESET_ALL + " "
                
            else:
                cur_s += tape_positive[i] + " "

        cur_s += "   current node: " + cur

        if (len(cur_s) < prev_l):
            cur_s += " " * (prev_l - len(cur_s))
        sys.stdout.write(cur_s)

        prev_l = len(cur_s)

    if (cur == accept):
        sys.stdout.write("\n" + colorama.Fore.GREEN + "Accepted" + colorama.Style.RESET_ALL + "\n")
        break
    if (cur == reject):
        sys.stdout.write("\n" + colorama.Fore.RED + "Rejected" + colorama.Style.RESET_ALL + "\n")
        break

    if ((cur, cur_symbol) in graph):
        cnt_steps += 1
        tmp = graph[(cur, cur_symbol)]
        cur = tmp[0]
        if (pos < 0):
            tape_negative[-pos - 1] = tmp[1]
        else:
            tape_positive[pos] = tmp[1]
        pos += tmp[2]

        if (pos < 0):
            if (-pos - 1 == len(tape_negative)):
                tape_negative.append(blank)
        else:
            if (pos == len(tape_positive)):
                tape_positive.append(blank)
    else:
        sys.stdout.write("\n" + colorama.Fore.RED + "Failed, No edge by this state: (" + cur + ", " + cur_symbol + "), from current node, Rejected" + colorama.Style.RESET_ALL + "\n")
        cur = reject
        break

    time.sleep(delay)


sys.stdout.write("Total steps: " + str(cnt_steps) + "\n")
