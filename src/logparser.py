#-*- coding: utf-8 -*-

"""
Created on Jan 4, 2015

@author: Ira

Converts plaintext logs into HTML, and marks IC for lines beginning with `.

Then we'll have a second, interactive round done in Javascript with a more 
intuitive UI.

TODO: preface a line with $ to mark it as a spoiler; in the logs it will
        be made illegible (blurred out, maybe) unless the Show Spoilers box
        is checked. IC, print in white.
        And I guess if Fortuna is sent a roll with a $, she'll return it with
        a $ as well? And print that line in white too.
        Actually it might be possible to just detect if a line is in white or not.
TODO merge config into one file
TODO add config options for the patterns for IC, OOC, spoilers I guess
"""

import re, os, tkinter.filedialog

LOGS_PATH = "C:/xampp/htdocs/irasite/rpg/logs/parsedlogs/"
#LOGS_PATH = "/Applications/XAMPP/xamppfiles/htdocs/irasite/rpg/logs/parsedlogs/"

linepat = re.compile("(^[^:]*:)(.*)")
linkpat = re.compile("http(?:s)?://\S*")
dicepat = re.compile("^\s*(\d+#\s*)?\d+\s*d\s*\d+", re.I)
retpat  = re.compile("^`(<+)(\d*)")	# markers for whether a previous line is IC

def divide_line(line):
	match = re.match(linepat, line.strip())
	if not match:
		# this is probably a server command
		return ("server", line.strip())
	
	speaker = match.group(1)[:-1] #[:-1] to cut off the colon at the end
	text = match.group(2).strip()
	
	return (speaker, text)


def get_basename(filename):
	pathless_name = os.path.basename(filename)
	basename, _, _ = pathless_name.rpartition(".")
	#Because of some quirks of rpartition, basename will be empty if no . is found.
	
	if basename:
		return basename
	else:
		return pathless_name


def update_configs(filename, newline):
	with open("../parserconfigs/" + filename, 'a') as outfile:
		outfile.write("\n" + newline)


def wrap_link(linkmatch):
	return "<a href='" + linkmatch.group(0) + "' target='_blank'>" \
			+ linkmatch.group(0) + "</a>"


class LogParser():
	def __init__(self):
		self.bots = self.get_configs("bots.txt")
		gms = self.get_configs("gms.txt")
		self.gm_pat = re.compile("|".join(gms))
		self.parsed_lines = []
		
	def parse_logs(self, *filenames):
		self.parsed_lines = []
		
		for filename in filenames:
			with open(filename, 'r') as infile:
							
				for line in infile:
					speaker, text = divide_line(line)
					speaker = speaker.lower()
					speaker_class = self.get_speaker_class(speaker)
					retmatch = re.match(retpat, text)
					
					if retmatch: #mark a line as actually IC
						lines_to_go_back = len(retmatch.group(1))
						
						if retmatch.group(2):
							lines_to_go_back += min(int(retmatch.group(2)) - 1, 0)
						
						for line in reversed(self.parsed_lines):
							if line["speaker"] == speaker:
								lines_to_go_back -= 1;
							
								if not lines_to_go_back:
									line["line_class"] = "ic"
									break
									
						continue
					
					elif text[0] in ("`", "'"):
						line_class = "ic" #the space is for joining to the other classes
						text = text[1:].strip()
					elif text[0] == '"':
						line_class = "ic"
					elif speaker == "server":
						line_class = "ic"
					elif speaker.lower() in self.bots or re.search(dicepat, text):
						line_class = "ic"
					else:
						line_class = "ooc"
					
					markedup_text = self.sanitize_text(text)
					
					self.parsed_lines.append({ 	  "speaker": speaker,
											"speaker_class": speaker_class,
											   "line_class": line_class,
											"markedup_text": markedup_text })
		return self.parsed_lines
	
	def write_lines(self, out):
		with open(out, "w") as outfile:
			for line in self.parsed_lines:		
				outfile.write("\t<blockquote class='" + line["speaker_class"] 
						+ line["line_class"] + "'><cite>" + line["speaker"] 
						+ ":</cite><p>" + line["markedup_text"] 
						+ "</p></blockquote>\n")
	
	def get_configs(self, filename):
		loadinto = []
		
		with open("../parserconfigs/" + filename, 'r') as infile:
			for line in infile:
				if line:
					loadinto.append(line.strip().lower())
		
		return loadinto

	def get_speaker_class(self, speaker):
		if speaker == "server":
			speaker_class = "server "
		elif speaker in self.bots:
			speaker_class = "bot "
		elif self.gm_pat.search(speaker):
			speaker_class = "gm "
		else:
			speaker_class = ""
		
		return speaker_class
	
	def sanitize_text(self, text):
		"""
		process text to mark up links, and maybe images and styling?
		Also converts symbols to entity strings.
		
		TODO might be able to do some of this with string.translate
		"""
		markedup_text = re.sub(linkpat, wrap_link, text)
		markedup_text = re.sub("&", "&amp;", markedup_text)
		markedup_text = re.sub('—', "&mdash;", markedup_text)
		markedup_text = markedup_text.replace('<', "&lt;")
		markedup_text = markedup_text.replace('>', "&gt;")

		return markedup_text


def main():
	tkinter.Tk().withdraw()
	
	filenames = tkinter.filedialog.askopenfilenames()
	basenames = [get_basename(f) for f in filenames]
	
	logparser = LogParser()
	logparser.parse_logs(*filenames)
	
	try:
		out = LOGS_PATH + basenames[0] + ".html"
	except IndexError:
		return
	
	logparser.write_lines(out)
	
	print(len(logparser.parsed_lines), "lines parsed")


if __name__ == "__main__":
	main()