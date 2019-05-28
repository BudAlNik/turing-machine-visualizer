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
paused = False
for i in range(3, len(sys.argv)):
    if sys.argv[i] == '-p':
        paused = True
    try:
        delay = float(sys.argv[i])
    except:
        pass

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
tapes_number = 1

graph = dict()
nodes = set()

c = 0

for s in prog:
    if c == 0 and s.strip().isdecimal():
        tapes_number = int(s.strip())
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
        if len(tmp) != 3 + tapes_number * 3:
            print("Parse failed on line: \"%s\"" % s.strip(), file=sys.stderr)
            exit(1)

        fr = tmp[0]
        ch = tuple(tmp[1:tapes_number + 1])
        if tmp[tapes_number + 1] != "->":
            print("Parse failed on line: \"%s\"" % s.strip(), file=sys.stderr)
            exit(1)

        to = tmp[tapes_number + 2]
        new_ch = []
        moves = []
        for i in range(tapes_number):
            new_ch.append(tmp[tapes_number + 3 + i * 2])
            moves.append(get_dir(tmp[tapes_number + 3 + i * 2 + 1]))

        graph[(fr, ch)] = [to, new_ch, moves]
        nodes.add(fr)

    c += 1

for p in graph:
    if graph[p][0] != reject and graph[p][0] != accept and not graph[p][0] in nodes:
        print("Warning: There's an edge leading to node \"%s\", but there's no edge going from this node" % graph[p][0])

inp = open(f_inp, "r")

carriage_positions = [0] * tapes_number
input_data = inp.readline().split()
tapes = [dict() for _ in range(tapes_number)]

for i in range(len(input_data)):
    tapes[0][i] = input_data[i]

prev_l = 0

try:
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.use_default_colors()
    stdscr.nodelay(1)
    stdscr.keypad(True)
    height, width = stdscr.getmaxyx()
    curses.init_pair(1, curses.COLOR_BLUE, -1)

    steps_cnt = 0
    flag = True

    gap = 5
    cells_to_show = width // 2

    lborder = [carriage_positions[i] - gap for i in range(tapes_number)]

    outcome = ""

    while (True):
        stdscr.clear()
        stdscr.addstr(height - 1, 0, "Press 'q' to interrupt, Press space to pause/resume")
        line_cnt = 0
        cur_symbols = []
        for i in range(tapes_number):
            if carriage_positions[i] - lborder[i] < gap:
                lborder[i] = carriage_positions[i] - gap
            elif lborder[i] + cells_to_show - carriage_positions[i] < gap:
                lborder[i] = carriage_positions[i] + gap - cells_to_show

            to_show = []

            for j in range(cells_to_show):
                if not lborder[i] + j in tapes[i]:
                    tapes[i][lborder[i] + j] = blank
                to_show.append(tapes[i][lborder[i] + j])

            cur_symbols.append(tapes[i][carriage_positions[i]])

            stdscr.addstr(line_cnt, 0, " ".join(to_show)[:width])
            carriage_pos = carriage_positions[i] - lborder[i]
            carriage_shift = sum(len(sym) + 1 for sym in to_show[:carriage_pos])
            stdscr.addstr(line_cnt + 1, carriage_shift, "^")
            stdscr.addstr(line_cnt + 2, carriage_shift, str(carriage_positions[i]))

            line_cnt += 3
        
        line_cnt += 1
        stdscr.addstr(line_cnt, 0, "Current node: %s" % cur)
        stdscr.addstr(line_cnt + 1, 0, "Steps done: %d" % steps_cnt)
        line_cnt += 3

        stdscr.refresh()

        cur_symbols = tuple(cur_symbols)

        if (cur == accept):
            outcome = colorama.Fore.GREEN + "Accepted" + colorama.Style.RESET_ALL
            break
        if (cur == reject):
            outcome = colorama.Fore.RED + "Rejected" + colorama.Style.RESET_ALL
            break

        if not (cur, cur_symbols) in graph:
            outcome = colorama.Fore.RED + "Failed, No edge from %s by symbols (%s), Rejected" % (cur, ", ".join(cur_symbols)) + colorama.Style.RESET_ALL
            cur = reject
            break

        if paused:
            stdscr.addstr(line_cnt, 0, "Paused (press space to resume, press right-arrow to proceed to the next state)", curses.color_pair(1))

        was = float(time.time())
        interupted = False
        while time.time() - was < delay or paused:
            key = stdscr.getch()
            
            if key == ord('q'):
                outcome = colorama.Fore.YELLOW + "Interrupted by user" + colorama.Style.RESET_ALL
                interupted = True
                break

            if key == ord(' '):
                paused ^= 1
                if paused:
                    stdscr.addstr(line_cnt, 0, "Paused (press space to resume, press right-arrow to proceed to the next state)", curses.color_pair(1))
                else:
                    stdscr.addstr(line_cnt, 0, " " * 30)

                stdscr.refresh()

            if key == curses.KEY_RIGHT:
                break

            time.sleep(0.01)

        if interupted:
            break

        steps_cnt += 1
        tmp = graph[(cur, cur_symbols)]
        cur = tmp[0]

        for i in range(tapes_number):
            tapes[i][carriage_positions[i]] = tmp[1][i]
            carriage_positions[i] += tmp[2][i]

    curses.endwin()

    print("Final state of the tapes:")
    for i in range(tapes_number):
        tape_output = []
        for pos in tapes[i]:
            tape_output.append((pos, tapes[i][pos]))

        tape_output.sort()
        l = tape_output[0][0]
        tape_output = list(map(lambda x : x[1], tape_output))

        while len(tape_output) and tape_output[0] == '_' and l < carriage_positions[i]:
            tape_output = tape_output[1:]
            l += 1

        while len(tape_output) and tape_output[-1] == '_' and carriage_positions[i] + 1 < l + len(tape_output):
            tape_output = tape_output[:-1]

        tape_output = ["_", "_"] + tape_output + ["_", "_"]
        l -= 2

        removed_from_left = False
        removed_from_right = False

        while len(tape_output) > cells_to_show:
            if carriage_positions[i] - l > l + len(tape_output) - carriage_positions[i]:
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

        carriage_pos = carriage_positions[i] - l
        carriage_shift = sum(len(sym) + 1 for sym in tape_output[:carriage_pos])
        if not removed_from_left:
            output_carriage_pos = carriage_shift
        else:
            output_carriage_pos = carriage_shift + 4

        print(" " * output_carriage_pos + "^")

    print(outcome)
    print("Total steps: %d" % steps_cnt)
except KeyboardInterrupt as e:
    pass
except Exception as error:
    curses.endwin()
    print(error)
    print("Something went wrong")
