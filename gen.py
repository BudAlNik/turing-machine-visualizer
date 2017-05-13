#!/usr/bin/python3
# Written by Nikolay Budin, 2017

import sys
adr = sys.argv[1]

name = ""
if (len(sys.argv) > 2):
    name = sys.argv[2]

f = open(adr)

res = ""
for s in f:
    s2 = s.strip()
    if (s2 != ""):
        res += s2 + "\\n"

if ("/" in adr):
    d = adr[: adr.rfind("/")]
    if (name == ""):
        name = adr[adr.rfind("/") + 1:]
else:
    d = "./"
    if (name == ""):
        name = adr


print("print(\"" + res + "\", file=open(\"" + name + ".out\", \"w\"))", file=open(d + "/" + name + ".py", "w"))