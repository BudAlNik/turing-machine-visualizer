#!/usr/bin/python3
# Written by Nikolay Budin, 2017
# Rewritten by Nikolay Budin, 2019
# Updated by Nikolay Budin, 2020

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

machine_desc_path = sys.argv[1]
input_path = sys.argv[2]
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
	if act == "<":
		return -1
	if act == "^":
		return 0
	if act == ">":
		return 1
	raise Exception("'%s' is not a correct direction" % act)

machine_desc = open(machine_desc_path, "r")

accept = "AC"
reject = "RJ"
cur = "S"
blank = "_"
tapes_number = 1

graph = dict()
nodes = set()

c = 0

symb_len = 1

for s in machine_desc:
	if c == 0 and s.strip().isdecimal():
		tapes_number = int(s.strip())
	elif s.startswith("start:"):
		cur = s[s.find(":") + 1:].strip()
	elif s.startswith("accept:"):
		accept = s[s.find(":") + 1:].strip()
	elif s.startswith("reject:"):
		reject = s[s.find(":") + 1:].strip()
	elif s.startswith("blank:"):
		blank = s[s.find(":") + 1:].strip()
	elif s.strip() != "":
		tmp = s.split()
		if len(tmp) != 3 + tapes_number * 3:
			raise Exception("Parse failed on line: \"%s\"" % s.strip())

		fr = tmp[0]
		ch = tuple(tmp[1:tapes_number + 1])
		if tmp[tapes_number + 1] != "->":
			raise Exception("Parse failed on line: \"%s\"" % s.strip())

		to = tmp[tapes_number + 2]
		new_ch = []
		moves = []
		for i in range(tapes_number):
			new_ch.append(tmp[tapes_number + 3 + i * 2])
			symb_len = max(symb_len, len(new_ch[-1]))
			moves.append(get_dir(tmp[tapes_number + 3 + i * 2 + 1]))

		graph[(fr, ch)] = [to, new_ch, moves]
		nodes.add(fr)

	c += 1

for p in graph:
	if graph[p][0] != reject and graph[p][0] != accept and not graph[p][0] in nodes:
		print("Warning: There's an edge leading to node \"%s\", but there's no edge going from this node" % graph[p][0])

inp = open(input_path, "r")

carriages_position = [0] * tapes_number
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

	if height < tapes_number * 3 + 5:
		raise Exception("Terminal window has to be at least %d characters height" % (tapes_number * 3 + 5))

	curses.init_pair(1, curses.COLOR_BLUE, -1)

	steps_cnt = 0
	flag = True

	gap = 5
	cells_to_show = (width + 1) // (1 + symb_len)

	if cells_to_show < gap * 2 + 1:
		raise Exception("Terminal window has to be at least %d characters width" % ((gap * 2 + 1) * cells_to_show - 1))

	lborder = [carriages_position[i] - gap for i in range(tapes_number)]

	def get_carriage_shift(carriage_pos):
		return carriage_pos * (symb_len + 1) + (symb_len - 1) // 2

	def fix_symb_len(symb):
		left_free = symb_len - len(symb)
		return " " * (left_free // 2) + symb + " " * ((left_free + 1) // 2)

	outcome = ""

	pause_message = "Paused (press space to resume, press right-arrow to proceed to the next state)"
	info_message = "Press 'q' to interrupt, Press space to pause/resume"

	while (True):
		stdscr.clear()
		stdscr.addstr(tapes_number * 3 + 4, 0, info_message)
		line_cnt = 0
		cur_symbols = []
		for i in range(tapes_number):
			if carriages_position[i] - lborder[i] < gap:
				lborder[i] = carriages_position[i] - gap
			elif lborder[i] + cells_to_show - carriages_position[i] < gap:
				lborder[i] = carriages_position[i] + gap - cells_to_show

			to_show = []

			for j in range(cells_to_show):
				if not lborder[i] + j in tapes[i]:
					tapes[i][lborder[i] + j] = blank
				to_show.append(tapes[i][lborder[i] + j])

			cur_symbols.append(tapes[i][carriages_position[i]])

			stdscr.addstr(line_cnt, 0, " ".join(map(fix_symb_len, to_show)))
			carriage_pos = carriages_position[i] - lborder[i]
			carriage_shift = get_carriage_shift(carriage_pos)
			stdscr.addstr(line_cnt + 1, carriage_shift, "^")
			stdscr.addstr(line_cnt + 2, carriage_shift - (len(str(carriages_position[i])) - 1) // 2, str(carriages_position[i]))

			line_cnt += 3
		
		line_cnt += 1
		stdscr.addstr(line_cnt, 0, "Current node: %s" % cur)
		stdscr.addstr(line_cnt + 1, 0, "Steps done: %d" % steps_cnt)
		line_cnt += 3

		stdscr.refresh()

		cur_symbols = tuple(cur_symbols)

		if cur == accept:
			outcome = colorama.Fore.GREEN + "Accepted" + colorama.Style.RESET_ALL
			break
		if cur == reject:
			outcome = colorama.Fore.RED + "Rejected" + colorama.Style.RESET_ALL
			break

		if not (cur, cur_symbols) in graph:
			if tapes_number == 1:
				outcome = colorama.Fore.RED + "Failed, No edge from %s by symbol %s, Rejected" % (cur, cur_symbols[0]) + colorama.Style.RESET_ALL
			else:
				outcome = colorama.Fore.RED + "Failed, No edge from %s by symbols (%s), Rejected" % (cur, ", ".join(cur_symbols)) + colorama.Style.RESET_ALL
			cur = reject
			break

		if paused:
			stdscr.addstr(tapes_number * 3 + 4, 0, pause_message, curses.color_pair(1))

		time_was = float(time.time())
		interupted = False
		while time.time() - time_was < delay or paused:
			key = stdscr.getch()
			
			if key == ord('q'):
				outcome = colorama.Fore.YELLOW + "Interrupted by user" + colorama.Style.RESET_ALL
				interupted = True
				break

			if key == ord(' '):
				paused ^= 1
				if paused:
					stdscr.addstr(tapes_number * 3 + 4, 0, pause_message, curses.color_pair(1))
				else:
					stdscr.addstr(tapes_number * 3 + 4, 0, " " * len(pause_message))
					stdscr.addstr(tapes_number * 3 + 4, 0, info_message)

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
			tapes[i][carriages_position[i]] = tmp[1][i]
			carriages_position[i] += tmp[2][i]

	curses.endwin()

	print("Final state of the tapes:")
	for i in range(tapes_number):
		tape_output = []
		for pos in tapes[i]:
			tape_output.append((pos, tapes[i][pos]))

		tape_output.sort()
		left_ind = tape_output[0][0]
		tape_output = list(map(lambda x : x[1], tape_output))

		while len(tape_output) and tape_output[0] == '_' and left_ind < carriages_position[i]:
			tape_output = tape_output[1:]
			left_ind += 1

		while len(tape_output) and tape_output[-1] == '_' and carriages_position[i] + 1 < left_ind + len(tape_output):
			tape_output = tape_output[:-1]

		tape_output = ["_", "_"] + tape_output + ["_", "_"]
		tape_output = list(map(fix_symb_len, tape_output))
		left_ind -= 2

		removed_from_left = False
		removed_from_right = False

		will_add_len = 0

		while len(tape_output) * (symb_len + 1) - 1 + will_add_len > width:
			if carriages_position[i] - left_ind > left_ind + len(tape_output) - 1 - carriages_position[i]:
				if tape_output[0] != '_' and not removed_from_left:
					removed_from_left = True
					will_add_len += 4

				tape_output = tape_output[1:]
				left_ind += 1
			else:
				if tape_output[-1] != '_' and not removed_from_right:
					removed_from_right = True
					will_add_len += 4

				tape_output = tape_output[:-1]

		if removed_from_left:
			tape_output = ["..."] + tape_output

		if removed_from_right:
			tape_output = tape_output + ["..."]

		print(" ".join(tape_output))

		carriage_pos = carriages_position[i] - left_ind
		carriage_shift = get_carriage_shift(carriage_pos)
		if removed_from_left:
			carriage_shift += 4

		print(" " * carriage_shift + "^")

	print(outcome)
	print("Total steps: %d" % steps_cnt)
except KeyboardInterrupt as e:
	pass
except Exception as error:
	curses.endwin()
	raise error
