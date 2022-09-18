#!/usr/bin/python3
# -*- coding: utf-8 -*-

LICENSE = """
  canopen – a small, versatile script to open files with external programs

  Copyright © 2022 Zacharias Korsalka <sacharja@sacharja.at>

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:

  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
  ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
  POSSIBILITY OF SUCH DAMAGE.
"""


import fnmatch, os, subprocess, sys

class Canopen:
	"everything canopen does is completely contained within this class"

	def message(self, message, exitcode=1):
		"put out an error message, either with an external program or on stderr, exit if exitcode is set"

		# if there is an external messenger found in settings, use it
		if "messenger" in self.setting:
			messenger = self.setting["messenger"].split()

			try:
				p = subprocess.run(messenger+[message])
			except:
				sys.stderr.write(self.name+": messenger command failed: "+" ".join(messenger)+"\n")
				sys.exit(1)

			if p.returncode:
				sys.stderr.write(self.name+": messenger command returned error code {0}: ".format(p.returncode)+" ".join(messenger)+"\n")
				sys.exit(1)

			if exitcode: sys.exit(exitcode)

			return

		# if there is no external messenger, output goes to sys.stderr
		sys.stderr.write(self.name+": "+message+"\n")
		if exitcode: sys.exit(exitcode)



	def config_load(self, path="", from_loadconfig=""):
		"figure out which configuration file to load and load it, "
		"if path begins with “./” or “/”, a local or absolute path will be loaded, "
		"otherwise, path will be loaded from ~/.config/canopen"
		my_path = ""

		# TODO: that thing with ./ or / is not yet documented, and a bit weird anyway

		valid_settings = ["fallback", "messenger", "loadconfig"]

		if path:
			if path.startswith("./") or path.startswith("/"):
				my_path = path
			else:
				if "HOME" not in os.environ: self.message("{0}: no such environment variable".format("HOME"))
				my_path = os.path.join(os.environ["HOME"], ".config/canopen", path)

			if not os.path.exists(my_path):
				self.message("could not load configuration, no such file {0}".format(my_path))

		if not my_path:
			if "CANOPEN" in os.environ or self.options["environment"][0]:
				if self.options["environment"][0]:
					my_path = os.path.join(os.environ["HOME"], ".config/canopen", self.options["environment"][0])
				else:
					my_path = os.path.join(os.environ["HOME"], ".config/canopen", os.environ["CANOPEN"])
			else:
				my_path = os.path.join(os.environ["HOME"], ".config/canopen", self.name)

		# have we already seen that configuration?
		if my_path in self.loaded_configs:
			self.message("{0}{1} has already been loaded".format(from_loadconfig, my_path))

		self.loaded_configs.append(my_path)

		# now load that configuration file
		try:
			fp = open(my_path, "r")
		except FileNotFoundError:
			self.message("could not load {0}".format(my_path))

		raw = fp.read()
		fp.close

		if self.options["verbose"][0]: print("loading configuration: {0}".format(my_path))

		assignment = {
			"alias":   self.alias,
			"mime":    self.mime,
			"pattern": self.pattern,
			"setting": self.setting
		}

		n = 0
		for line in raw.split("\n"):
			n += 1

			if "#" in line: line = line.split("#")[0]
			line = line.strip()
			if not line: continue
			line = line.replace("\t", " ")   # forgive the use of tabs

			# get (and check) the keyword of the line
			keyword = line.split(" ", 1)[0]

			if keyword not in ["alias", "mime", "pattern", "setting"]:
				self.message("line {0} in {1}: invalid keyword “{2}”\nvalid keywords are: “alias”, “mime”, “pattern” and “setting”".format(n, my_path, keyword))

			line = line[len(keyword):].strip()

			# get key
			key = line.split(" ", 1)[0]
			line = line[len(key):].strip()

			if not key:
				self.message("line {0} in {1}: key missing after keyword".format(n, my_path))

			# get value
			value = line

			if not value:
				self.message("line {0} in {1}: value missing after keyword and key".format(n, my_path))

			# warn of duplicates
			if self.options["no-overwrites"][0]:
				if key in assignment[keyword] and key != "loadconfig":
					self.message("line {0} in {1}: value “{2}” for duplicate {4} overwrites previous {4} “{3}”".format(n, my_path, value, key, keyword))

			# put the stuff where it belongs
			assignment[keyword][key] = value

			# if it is an alias, check for loops
			if keyword == "alias":
				pass
				current = key

				while current in self.alias:
					if key == self.alias[current]:
						self.message("line {0} in {1}: alias “{2}” creates a loop".format(n, my_path, key))

					current = self.alias[current]

			# if it is an setting, check for a proper key
			if keyword == "setting":
				if key not in valid_settings:
					self.message("line {0} in {1}: invalid setting “{2}”\nvalid keys for settings are: “{3}”".format(n, my_path, key, "”, “".join(valid_settings)))

				# handle setting for loadconfig immediately
				if key == "loadconfig":
					self.config_load(value, from_loadconfig="line {0} in {1}: ".format(n, my_path))



	def get_mime(self, path):
		"return the mediatype of path in the form type/subtype without any additional information"

		if not os.path.exists(path):
			self.message("could not open {0}".format(path))

		p = subprocess.run(["file", "-Lbi", path], capture_output=True)
		output = p.stdout.decode("utf-8")
		if ";" in output: output = output.split(";")[0]

		if "/" not in output:
			sys.stderr.write(" ".join(["file", "-Lbi", path]))
			self.message("the above command did not generate valid output")

		return output



	def run(self):
		"determine, which file to open with which command, and run it"
		opener = {}   # which file to be opened by which command
		for item in self.files: opener[item] = ""

		# but before that, divide self.mime into basic mimes and complete ones
		# for the latter have priority over the first ones
		self.basic, self.complete = {}, {}

		for item in self.mime:
			if "/" in item:
				self.complete[item] = self.mime[item]
			else:
				self.basic[item] = self.mime[item]

		# get a basic and complete mime-type for each file
		complete, basic = {}, {}
		for item in self.files:
			mime_type = self.get_mime(item)
			complete[item] = mime_type
			basic[item] = mime_type.split("/")[0]

		if self.options["show-mimes"][0]:
			for item in complete:
				print("{0} ... {1}".format(item, complete[item]))
			sys.exit(0)

		# does any pattern match the path of the file?
		for item in opener:
			for p in self.pattern:
				if fnmatch.fnmatch(os.path.basename(item), p):
					opener[item] = self.pattern[p]
					break

		# for all still unmatched files:
		# according to complete mime-type, open which file with what?
		for item in opener:
			if opener[item]: continue

			if complete[item] in self.mime:
				opener[item] = self.mime[ complete[item] ]

		# for all still unmatched files:
		# according to basic mime-type, open which file with what?
		for item in opener:
			if opener[item]: continue

			if basic[item] in self.mime:
				opener[item] = self.mime[ basic[item] ]

		# handle all files still unmatched
		unhandleables = []

		for item in opener:
			if opener[item]: continue

			if "fallback" in self.setting:
				opener[item] = self.setting["fallback"]
			else:
				unhandleables.append(item)

		if unhandleables:
			self.message("do not know how to open:\n{0}".format("\n".join(unhandleables)), 0)

		# resolve aliases for all files
		for item in opener:
			if not opener[item]: continue

			command = opener[item]
			while command in self.alias: command = self.alias[command]
			opener[item] = command

		# group files by command with which it is to be opened
		commands = {}

		for item in opener:
			if not opener[item]: continue

			c = opener[item]
			if c not in commands:
				commands[c] = [item]
			else:
				commands[c].append(item)

		for c in commands:
			if self.options["simulate"][0]:
				print("\n"+c)
				for thing in commands[c]:
					print("  "+thing)
			else:
				cmd = c.split()+commands[c]
				subprocess.Popen(cmd)



	def print_usage(self):
		lines = [
			"",
			"canopen – a small, versatile script to open files with external programs",
			"",
			"Usage: {0} [OPTION]... PATH...".format(self.name),
			"",
			"Options:",
		]

		tab1, tab2 = 0, 0

		for option in self.options:
			if len(option) > tab1: tab1 = len(option)
			if len(self.options[option][1]) > tab2: tab2 = len(self.options[option][1])

		for option in self.options:
			parameter = self.options[option][1]
			description = self.options[option][-1]

			spacer = "."*(tab1+tab2-len(option)-len(parameter)+1)

			lines.append("  --{0} {1} {2} {3}".format(option, parameter, spacer, description))

		lines.append("")

		print("\n".join(lines))



	def __init__(self, argv):
		self.alias, self.mime, self.pattern, self.setting = {}, {}, {}, {}

		self.loaded_configs = []
		self.files = []
		self.options = {
			"help": [
				False,
				"",
				"put out this help-text and exit",
			],

			"show-mimes": [
				False,
				"",
				"show mime-types of files, do not do anything else",
			],

			"simulate": [
				False,
				"",
				"only say what you do, do not actually do it",
			],

			"verbose": [
				False,
				"",
				"put out additional information",
			],

			"environment": [
				"",
				"NAME",
				"act as if environment CANOPEN was set to NAME",
			],

			"no-overwrites": [
				False,
				"",
				"abort, if keys in configuration are overwritten by later entries",
			],
		}

		# cleanup the name of the call
		self.name = os.path.basename(sys.argv[0])
		if "." in self.name: self.name = self.name.split(".")[0]

		# parse command line
		no_more_options = False    # if True, no more options are parsed
		expected = None              # expected type of parameter

		for item in argv[1:]:
			if no_more_options:
				self.files.append(item)
				continue

			if expected:
				self.options[option][0] = item
				expected = None
				continue

			if item == "--":
				if expected: self.message("“--” cannot be a parameter of any option")

				no_more_options = True
				continue

			if item.startswith("--"):    # canopen only knows long options
				option = item[2:]

				if option not in self.options:
					self.message("unknown option “{0}”".format(item))

				param = self.options[option][0]

				# boolean options have no parameters
				if type(param) == bool:
					self.options[option][0] = True
					continue

				# for others, set expected type
				expected = type(param)
				continue

			self.files.append(item)

		if self.options["help"][0]:
			self.print_usage()
			sys.exit(0)

		if not self.files:
			self.message("no files to open, use option “{0} --help” for more information".format(self.name))

		# load config
		self.config_load()

		# run
		self.run()



def main(): Canopen(sys.argv)


if __name__ == "__main__": main()

