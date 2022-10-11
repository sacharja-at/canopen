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

def tabalign(text):
	"Align every column of a text of monospaced type, so that "\
	"every \\t gets vertically aligned. Also, "\
	"fill any spaces with the last character of the previous word."

	# break text into lines (by \n) and those into words (by \t)
	table = []    # contains the cells of the resulting table
	n = 0         # maximum number of words of any line

	for line in text.split("\n"):
		table.append( [] )    # start a new line
		words = line.split("\t")
		if len(words) > n: n = len(words)

		# add words to this line
		for word in words: table[-1].append(word)

		# add termination to line
		table[-1].append(None)

	table.append([])   # add termination to text

	# get maximum width of each column
	mwc = []
	for i in range(n): mwc.append(0)

	for line in table:
		i = 0
		for word in line:
			if not word: continue
			if len(word) > mwc[i]: mwc[i] = len(word)
			i += 1

	# now do the alignment
	result = ""
	li = 0    # line index
	for line in table:
		if not table[li]: continue

		wi = 0    # word index
		for word in line:
			if not word: continue

			result += word

			if line[wi+1]:
				result += word[-1] * (mwc[wi]-len(word))

			wi += 1

		li += 1
		if table[li]: result += "\n"

	return result


class Canopen:
	"everything canopen does is completely contained within this class, "+ \
	"main() below does basically nothing"

	def bye(self, exitcode):
		"exit, but flush out output buffer in .messages first"

		out = sys.stdout
		if exitcode: out = sys.stderr

		if self.messages:
			if len(self.messages) == 1:
				# if there is only one message, add a “canopen: ” to that line
				text = self.name+": "+self.messages[0]+"\n"
			else:
				text = ""
				for line in self.messages: text += line+"\n"
				text += "\n"

			# if an external messenger has been configured, use that
			if "messenger" in self.setting:
				messenger = self.setting["messenger"].split()

				try:
					pr = subprocess.run(messenger+[text])
				except:
					out.write(text)
					sys.stderr.write("{0}: messenger command failed: {1}".format(self.name, messenger))
					exitcode = 1
			else:
				out.write(text)

		sys.exit(exitcode)



	def message(self, message, exitcode=1):
		"save a message to .messages[], and translate it if possible "+ \
		"using .translations{}; do not flush out that buffer, however "+ \
		".bye will do that, which is called if exitcode != 0"

		self.messages.append(message)
		if exitcode: self.bye(exitcode)



	def config_load(self, path="", ext_config="", ext_line=0):
		"figure out which configuration file to load and load it, if path"+ \
		"begins with “./” or “/”, a local or absolute path will be loaded, "+ \
		"otherwise, path will be loaded from ~/.config/canopen/"
		my_path = ""

		valid_settings = ["fallback", "messenger", "runtype", "loadconfig"]

		if path:
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
			if ext_config:
				self.message("line {0} in {1}: {2} has already been loaded".format(ext_line, ext_config, my_path))
			else:
				self.message("{0} has already been loaded".format(my_path))

		self.loaded_configs.append(my_path)

		# now load that configuration file
		try:
			fp = open(my_path, "r")
		except FileNotFoundError:
			self.message("could not load {0}".format(my_path))

		raw = fp.read()
		fp.close

		if self.options["verbose"][0]: self.message("loading configuration: {0}".format(my_path), 0)

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
				current = key

				while current in self.alias:
					if key == self.alias[current]:
						self.message("line {0} in {1}: alias “{2}” creates a loop".format(n, my_path, key))

					current = self.alias[current]

			# if it is a setting, check for proper key
			if keyword == "setting":
				if key not in valid_settings:
					self.message("line {0} in {1}: invalid setting “{2}”\nvalid keys for settings are: “{3}”".format(n, my_path, key, "”, “".join(valid_settings)))

				if key == "runtype":
					if value not in ["terminal", "gui"]:
						self.message("line {0} in {1}: invalid value for “runtype”, valid values are “terminal” and “gui”".format(n, my_path))

				# handle setting for loadconfig immediately
				if key == "loadconfig":
					self.config_load(value, my_path, n)



	def get_mime(self, path):
		"return the mediatype of path in the form type/subtype without any additional information"

		if not os.path.exists(path):
			self.message("could not open {0}".format(path))

		p = subprocess.run(["file", "-Lbi", path], capture_output=True)
		output = p.stdout.decode("utf-8")
		if ";" in output: output = output.split(";")[0]

		if "/" not in output:
			self.message(" ".join(["file", "-Lbi", path]), 0)
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
			my_len = 0

			for item in complete:
				if my_len < len(complete[item]): my_len = len(complete[item])

			for item in complete:
				self.message("{0} {1}... {2}".format(complete[item], "."*(my_len-len(complete[item])), item), 0)

			self.bye(0)

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
				self.message("\n"+c, 0)
				for thing in commands[c]:
					self.message("  "+thing, 0)
			else:
				cmd = c.split()+commands[c]
				try:
					if "runtype" in self.setting and self.setting["runtype"] == "terminal":
						subprocess.run(cmd)
					else:
						subprocess.Popen(cmd)

				except FileNotFoundError:
					self.message("could not execute command: {0}".format(" ".join(cmd)))

		self.bye(0)    # call this to flush anything in self.messages



	def print_usage(self):
		usagetext = "canopen – a small, versatile script to open files with external programs\n"+ \
		"\n"+ \
		"Usage: {0} [OPTION]... PATH...\n"+ \
		"\n"+ \
		"Options:\n".format(self.name)

		optionstext = ""

		for option in self.options:
			parameter = self.options[option][1]
			description = self.options[option][-1]
			optionstext += "  --{0} {1} ...\t {2}\n".format(option, parameter, description)

		self.message(usagetext + tabalign(optionstext))
		self.bye(0)



	def __init__(self, argv):
		self.messages = [] # to contain the lines of output, see .message and .bye
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

		# load config
		self.config_load()

		if self.options["help"][0]:
			self.print_usage()
			sys.exit(0)

		if not self.files:
			self.message("no files to open, use option “{0} --help” for more information".format(self.name))

		# run
		self.run()



def main(): Canopen(sys.argv)


if __name__ == "__main__": main()
