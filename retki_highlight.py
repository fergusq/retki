# Retki
# Copyright (C) 2018 Iikka Hauhio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import argparse

class HTMLHighlighter:
	def __init__(self):
		self.buffer_stack = ["", "", ""]
		self.in_string = False
	
	def endParagraph(self):
		self.endLine()
		self.buffer_stack.pop() # line buffer
		if self.buffer_stack[-1]:
			buffer = self.buffer_stack.pop()
			if buffer.strip().startswith("<ol>"):
				self.buffer_stack[-1] += buffer
			elif buffer.strip():
				self.buffer_stack[-1] += "<p>" + buffer + "</p>\n"
			
			self.buffer_stack.append("")
		
		self.buffer_stack.append("")
	
	def endLine(self):
		if len(self.buffer_stack) == 3:
			self.buffer_stack[1] += " " + self.buffer_stack[2]
			self.buffer_stack[2] = ""
		else:
			if self.buffer_stack[-1]:
				buffer = self.buffer_stack.pop()
				if buffer.strip():
					self.buffer_stack[-1] += '<li><span class="text">' + buffer + "</span></li>\n"
			
				self.buffer_stack.append("")
	
	def indent(self):
		if len(self.buffer_stack) == 3:
			self.endParagraph()
		
		self.buffer_stack += ["", ""]
	
	def dedent(self):
		self.endLine()
		self.buffer_stack.pop() # line buffer
		buffer = self.buffer_stack.pop()
		self.buffer_stack[-1] += "<ol>" + buffer + "</ol>\n"
		
		if len(self.buffer_stack) == 3:
			self.endParagraph()
	
	def startNamespace(self):
		self.endParagraph()
		self.buffer_stack[0] += "<blockquote>\n"
	
	def endNamespace(self):
		self.endParagraph()
		self.buffer_stack[0] += "</blockquote>\n"
	
	def largeHeading(self, text):
		self.endParagraph()
		self.buffer_stack[0] += "<h2>" + text + "</h2>\n"
	
	def smallHeading(self, text):
		self.endParagraph()
		self.buffer_stack[0] += "<h3>" + text + "</h3>\n"
	
	def pre(self, text):
		self.endParagraph()
		self.buffer_stack[0] += "<pre>" + text + "</pre>\n"
	
	def comment(self, text):
		if len(self.buffer_stack) == 3:
			self.endParagraph()
			self.buffer_stack[0] += '<p class="comment"><em>' + text + "</em></p>"
		else:
			self.endLine()
			self.buffer_stack[-2] += '<li class="no-bullet"><span class="comment"><em>' + text + "</em></span></li>"
	
	def ruleName(self, text):
		if len(self.buffer_stack) == 3:
			self.endParagraph()
			self.buffer_stack[0] += '<p class="comment">(<em>' + text + "</em>)</p>"
		else:
			self.endLine()
			self.buffer_stack[-2] += '<li class="no-bullet"><span class="rule-name">(<em>' + text + "</em>)</span></li>"
	
	def startString(self):
		self.in_string = True
		self.buffer_stack[-1] += '<span class="string">'
	
	def endString(self):
		self.in_string = False
		self.buffer_stack[-1] += '</span>'
	
	def startInterpolation(self):
		self.buffer_stack[-1] += '<span class="interpolation">'
	
	def endInterpolation(self):
		self.buffer_stack[-1] += '</span>'
	
	def addCharacter(self, char):
		if not self.in_string and char in "[]":
			self.buffer_stack[-1] += '<span class="disemph">' + char + '</span>'
		else:
			self.buffer_stack[-1] += char
	
	def addStrongWord(self, word):
		self.buffer_stack[-1] += "<strong>" + word + "</strong>"
	
	def addEmphasis(self, word):
		self.buffer_stack[-1] += "<em>" + word + "</em>"
	
	def output(self):
		self.endParagraph()
		return """
		<html>
			<head>
				<meta charset="utf8" />
				<style>
				* {
					box-sizing: border-box;
				}
				body {
					font-family: "Garamond", "EB Garamond", "Palatino", "Times", serif;
					font-size: 22px;
					background-color: #ffe;
				}
				div.content {
					box-shadow: 0px 1px 2px;
					margin-left: auto;
					margin-right: auto;
					max-width: 70rem;
					background-color: white;
					padding: 10px;
				}
				span.string {
					color: blue;
				}
				span.interpolation {
					color: #77f;
				}
				span.disemph {
					color: lightgray;
				}
				span.text {
					color: black;
				}
				span.rule-name {
					color: #478d5b;
				}
				span.comment {
					padding: 5px;
					background-color: #ffc;
					color: black;
				}
				@counter-style stmt-counter {
					system: extends decimal;
					prefix: "(";
					suffix: ") ";
				}
				ol {
					padding-top: 0px;
					margin-top: 0px;
					list-style: stmt-counter;
				}
				ol > li {
					color: lightgray;
				}
				p {
					margin-bottom: 0px;
				}
				li.no-bullet {
					list-style: none;
				}
				pre {
					font-family: "Fira Code", monospace;
					line-height: 1em;
				}
				p.comment, pre {
					margin-left: 20px;
					margin-right: 20px;
					margin-bottom: initial;
					padding: 5px;
					background-color: #ffc;
				}
				blockquote {
					margin-left: 0;
					border-left: 1px solid gray;
					padding-left: 1em;
				}
				</style>
			</head>
			<body><div class="content">
			""" + self.buffer_stack[0] + """
			</div></body>
		</html>
		"""

def takeChars(string, chars):
	ans = ""
	while string and string[0] in chars:
		ans += string[0]
		string = string[1:]
	return ans

def parseFile(file):
	lines = []
	indent_stack = [""]
	for line in file:
		if line.endswith("\n"):
			line = line[:-1]
		
		if line.strip() == "":
			if len(indent_stack) == 1:
				lines.append("<break>")
			
			continue
		
		if lines:
			prev_comment = takeChars(lines[-1], ">|")
			comment = takeChars(line, ">|")
			if comment and comment == prev_comment:
				lines[-1] += "\n" + line[len(comment):]
				continue
		
		indent = takeChars(line, " \t")
		if len(indent) > len(indent_stack[-1]):
			lines.append("<indent>")
			indent_stack.append(indent)
			lines.append(line.strip())
		else:
			while len(indent) < len(indent_stack[-1]):
				lines.append("<dedent>")
				indent_stack.pop()
			lines.append(line.strip())
	
	lines += ["<dedent>"]*(len(indent_stack)-1)
	
	#print("\n".join(lines))
	
	return lines

def highlight(file):
	lines = parseFile(file)
	highlighter = HTMLHighlighter()
	comment_styles = [
	#        CODE   METHOD                    STRIP
		(">>>", highlighter.largeHeading, True),
		(">>",  highlighter.smallHeading, True),
		(">|",  highlighter.pre,          False),
		(">",   highlighter.comment,      True),
	]
	
	for line in lines:
		cont = False
		for code, method, strip in comment_styles:
			if line.startswith(code):
				line = line.strip()[len(code):]
				if strip:
					line = line.strip()
				
				method(line)
				cont = True
				break
		
		if cont:
			continue
		elif line == "<break>":
			highlighter.endParagraph()
		elif line == "<indent>":
			highlighter.indent()
		elif line == "<dedent>":
			highlighter.dedent()
		elif line.startswith("(") and line.endswith(")"):
			highlighter.ruleName(line[1:-1])
		elif line.startswith("Avaa nimiavaruus"):
			highlighter.endLine()
			highlighter.addStrongWord("Avaa nimiavaruus")
			line = line[17:]
			if line.startswith("(") and line.endswith(")."):
				highlighter.addCharacter(" (")
				highlighter.addEmphasis(line[1:-2])
				highlighter.addCharacter(")")
			highlighter.addStrongWord(".")
			highlighter.startNamespace()
		elif line == "Sulje nimiavaruus.":
			highlighter.endNamespace()
			highlighter.addStrongWord("Sulje nimiavaruus.")
		else:
			highlighter.endLine()
			if line.startswith("Määritelmä. "):
				highlighter.addStrongWord("Määritelmä. ")
				line = line[12:]
			
			in_string = False
			for char in line:
				if char == '"':
					in_string = not in_string
					if in_string:
						highlighter.startString()
						highlighter.addCharacter(char)
					else:
						highlighter.addCharacter(char)
						highlighter.endString()
					
					continue
				if in_string:
					if char == "[":
						highlighter.startInterpolation()
						highlighter.addCharacter(char)
						continue
					
					if char == "]":
						highlighter.addCharacter(char)
						highlighter.endInterpolation()
						continue
				
				highlighter.addCharacter(char)
	
	print(highlighter.output().strip())

def main():
	parser = argparse.ArgumentParser(description="Retki syntax highlighter")
	parser.add_argument("file", type=str, help="file to be highlighted")
	args = parser.parse_args()
	
	with open(args.file, "r") as file:
		highlight(file)

if __name__ == "__main__":
	main()
