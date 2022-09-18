#!/usr/bin/python3
# -*- coding: utf-8 -*-

# this script puts out a table of contents of markdown-files you give to it as an argument
# it ignores level-1 headers
# it is as quick and dirty as they come
# it does not reach any required treshold of originality to be copyrighted in any way

import sys

for arg in sys.argv[1:]:
	raw = open(arg, "r").read()
	for line in raw.split("\n"):
		if not line.startswith("#") and "# " not in line: continue
		count = -1 + len(line.split("# ", 1)[0])
		if count < 0: continue   # as I said, forget level-1 headers!
		label = line.split("# ", 1)[1]
		link = label.lower().replace(" ", "-")
		print("  "*count+"* ["+label+"](#"+link+")")


