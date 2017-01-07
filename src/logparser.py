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

import re, os, configparser, tkinter.filedialog

CONFIG_PATH = "../logparser.ini"

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
	"""
	TODO special cases for linked images, videos, and possibly music.
		Ideally: download images, and put all of them inline if possible.
		Possibly just as thumbnails.
	"""
	return "<a href='" + linkmatch.group(0) + "' target='_blank'>" \
			+ linkmatch.group(0) + "</a>"

def normalize_name(s):
	return '^' + s.lower() + '$'

class LogParser():
	def __init__(self, config):
		self.bot_pattern = self._get_bot_pattern(config)
		self.gm_pattern = self._get_gm_pattern(config)
		
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
					elif self.bot_pattern.search(speaker) or re.search(dicepat, text):
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
	
	def _get_bot_pattern(self, config):
		bot_names = [normalize_name(bot_name) for bot_name in config["BOTS"]]
		return re.compile("|".join(bot_names))
	
	def _get_gm_pattern(self, config):
		base_pattern = "^(dm|gm)|(dm|gm)$"
		gm_names = [base_pattern] + \
				[normalize_name(gm_name) for gm_name in config["GMS"]]
		return re.compile("|".join(gm_names))
	
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
		elif self.bot_pattern.search(speaker):
			speaker_class = "bot "
		elif self.gm_pattern.search(speaker):
			speaker_class = "gm "
		else:
			speaker_class = ""
		
		return speaker_class
	
	def sanitize_text(self, text):
		"""
		process text to mark up links, and maybe images and styling?
		Also converts symbols to entity strings.
		
		TODO might be able to do some of this with string.translate
		FIXME links with "&" in them will get messed up
		...actually maybe they don't, these look fine.
		"""
		markedup_text = re.sub("&", "&amp;", text)
		markedup_text = re.sub('—', "&mdash;", markedup_text)
		markedup_text = markedup_text.replace('<', "&lt;")
		markedup_text = markedup_text.replace('>', "&gt;")
		markedup_text = re.sub(linkpat, wrap_link, markedup_text)
		
		return markedup_text


def main():
	tkinter.Tk().withdraw()
	
	filenames = tkinter.filedialog.askopenfilenames()
	basenames = [get_basename(f) for f in filenames]
	
	config = configparser.ConfigParser(allow_no_value=True)
	config.read(CONFIG_PATH)
	
	logparser = LogParser(config)
	logparser.parse_logs(*filenames)
	
	save_path = config["MISC"]["save path"]
	if not save_path.endswith('/'):
		save_path += '/'
	
	try:
		out = save_path + basenames[0] + ".html"
	except IndexError:
		return
	
	logparser.write_lines(out)
	
	print(len(logparser.parsed_lines), "lines parsed")


if __name__ == "__main__":
	main()