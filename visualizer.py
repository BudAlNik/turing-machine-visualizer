#!/usr/bin/python3
# Written by Nikolay Budin, 2017

import time
import sys
import colorama
import curses

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
    print("'%s' is not a correct direction" % act, file=sys.stderr)
    exit(1)

prog = open(name, "r")

accept = "AC"
reject = "RJ"
cur = "S"
blank = "_"

graph = dict()
nodes = set()

c = 0
for s in prog:
    if c == 0 and s.strip().isdecimal():
        if (int(s) != 1):
            print("Sorry, i can't run multi-tape machine", file=sys.stderr)
            exit(1)
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
            print("Parse failed on line: \"%s\"" % s.strip(), file=sys.stderr)
            exit(1)
        fr = tmp[0]
        ch = tmp[1]
        if tmp[2] != "->":
            print("Parse failed on line: \"%s\"" % s.strip(), file=sys.stderr)
            exit(1)
        to = tmp[3]
        new_ch = tmp[4]
        act = tmp[5]
        graph[(fr, ch)] = [to, new_ch, get_dir(act)]
        nodes.add(fr)
    c += 1

for p in graph:
    if graph[p][0] != reject and graph[p][0] != accept and not graph[p][0] in nodes:
        print("Warning: There's an edge leading to node \"%s\", but there's no edge going from this node" % graph[p][0])

inp = open(f_inp, "r")

carriage_pos = 0
input_data = inp.readline().split()
tape = dict()

for i in range(len(input_data)):
    tape[i] = input_data[i]

prev_l = 0

try:
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.use_default_colors()
    stdscr.nodelay(1)
    height, width = stdscr.getmaxyx()
    curses.init_pair(1, curses.COLOR_BLUE, -1)

    cnt_steps = 0
    flag = True

    gap = 5
    cells_to_show = width // 2

    lborder = carriage_pos - gap
    rborder = lborder + cells_to_show

    outcome = ""

    while (True):
        if carriage_pos - lborder < gap:
            lborder = carriage_pos - gap
            rborder = lborder + cells_to_show
        elif rborder - carriage_pos < gap:
            rborder = carriage_pos + gap
            lborder = rborder - cells_to_show

        to_show = []

        for i in range(cells_to_show):
            if not lborder + i in tape:
                tape[lborder + i] = blank
            to_show.append(tape[lborder + i])

        stdscr.clear()
        stdscr.addstr(height - 1, 0, "Press 'q' to interrupt, Press space to pause/resume")
        stdscr.addstr(0, 0, " ".join(to_show))
        stdscr.addstr(1, (carriage_pos - lborder) * 2, "^")
        stdscr.addstr(2, (carriage_pos - lborder) * 2, str(carriage_pos))
        stdscr.addstr(5, 0, "Current node: %s" % cur)

        stdscr.refresh()

        cur_symbol = tape[carriage_pos]
        
        if (cur == accept):
            outcome = colorama.Fore.GREEN + "Accepted" + colorama.Style.RESET_ALL
            break
        if (cur == reject):
            outcome = colorama.Fore.RED + "Rejected" + colorama.Style.RESET_ALL
            break

        if not (cur, cur_symbol) in graph:
            outcome = colorama.Fore.RED + "Failed, No edge from %s by symbol %s, Rejected" % (cur, cur_symbol) + colorama.Style.RESET_ALL
            cur = reject
            break

        was = float(time.time())
        interupted = False
        paused = False
        while time.time() - was < delay or paused:
            key = stdscr.getch()
            if key == ord('q'):
                outcome = colorama.Fore.YELLOW + "Interrupted by user" + colorama.Style.RESET_ALL
                interupted = True
                break

            if key == ord(' '):
                paused ^= 1
                if paused:
                    stdscr.addstr(7, 0, "Paused (press space to resume)", curses.color_pair(1))
                else:
                    stdscr.addstr(6, 0, " " * 30)

                stdscr.refresh()

                while stdscr.getch() == ord(' '):
                    pass
        
        if interupted:
            break

        cnt_steps += 1
        tmp = graph[(cur, cur_symbol)]
        cur = tmp[0]
        tape[carriage_pos] = tmp[1]
        carriage_pos += tmp[2]


    curses.endwin()

    print("Final state of the tape:")
    tape_output = []
    for pos in tape:
        tape_output.append((pos, tape[pos]))

    tape_output.sort()
    l = tape_output[0][0]
    tape_output = list(map(lambda x : x[1], tape_output))

    while len(tape_output) and tape_output[0] == '_' and l < carriage_pos:
        tape_output = tape_output[1:]
        l += 1

    while len(tape_output) and tape_output[-1] == '_' and carriage_pos + 1 < l + len(tape_output):
        tape_output = tape_output[:-1]

    tape_output = ["_", "_"] + tape_output + ["_", "_"]
    l -= 2

    removed_from_left = False
    removed_from_right = False

    while len(tape_output) > cells_to_show:
        if carriage_pos - l > l + len(tape_output) - carriage_pos:
            if tape_output[0] != '_' and not removed_from_left:
                removed_from_left = True
                cells_to_show -= 2

            tape_output = tape_output[1:]
            l += 1
        else:
            if tape_output[-1] != '_' and not removed_from_right:
                removed_from_right = True
                cells_to_show -= 2

            tape_output = tape_output[:-1]

    if removed_from_left:
        tape_output = ["..."] + tape_output

    if removed_from_right:
        tape_output = tape_output + ["..."]

    print(" ".join(tape_output))

    if not removed_from_left:
        output_carriage_pos = (carriage_pos - l) * 2
    else:
        output_carriage_pos = (carriage_pos - l) * 2 + 4

    print(" " * output_carriage_pos + "^")

    print(outcome)
    print("Total steps: %d" % cnt_steps)
except KeyboardInterrupt as e:
    pass
except Exception as error:
    curses.endwin()
    print(error)
    print("Something went wrong")
