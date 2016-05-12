#-*- coding: utf-8 -*-

'''
Created on Jan 4, 2015

@author: Ira

Converts plaintext logs into HTML, and marks IC for lines beginning with `.

Then we'll have a second, interactive round done in Javascript with a more 
intuitive UI.

TODO: permit regex in the parser configs, so we can, say, automatically 
	mark anyone with "DM" in their name as a DM

TODO: preface a line with $ to mark it as a spoiler; in the logs it will
        be made illegible (blurred out, maybe) unless the Show Spoilers box
        is checked. IC, print in white.
        And I guess if Fortuna is sent a roll with a $, she'll return it with
        a $ as well? And print that line in white too.
        Actually it might be possible to just detect if a line is in white or not.
'''

import re, os

BOTS = []
GMS = []

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

def load_configs(filename, loadinto):
	with open("../parserconfigs/" + filename, 'r') as infile:
		for line in infile:
			if line:
				loadinto.append(line.strip().lower())


def replace_ampersands(line):
	#return re.sub("(?:^|>)[^<]*(&)(?!gt;|lt;|amp;)[^>]*(?:$|<)", "&amp;", line)				
	return re.sub("&", "&amp;", line)

def replace_arrows(line):
	line = line.replace('<', "&lt;")
	line = line.replace('>', "&gt;")
	return line

def replace_emdashes(line):
	return re.sub('—', "&mdash;", line)

def update_configs(filename, newline):
	with open("../parserconfigs/" + filename, 'a') as outfile:
		outfile.write("\n" + newline)

def wrap_link(linkmatch):
	return "<a href='" + linkmatch.group(0) +"' target='_blank'>" + linkmatch.group(0) + "</a>"
		


load_configs("bots.txt", BOTS)
load_configs("gms.txt", GMS)



for filename in os.listdir("../logs/eberron2/month/"):
	
	parsed_lines = []

	with open("../logs/eberron2/month/" + filename, 'r') as infile:
					
		for line in infile:
			speaker, text = divide_line(line)
			speaker = speaker.lower()
			
			if speaker == "server":
				speaker_class = "server "
			elif speaker in BOTS:
				speaker_class = "bot "
			elif speaker in GMS or speaker.startswith(("dm", "gm")) or speaker.endswith(("dm", "gm")):
				speaker_class = "gm "
			else:
				speaker_class = ""
			
			retmatch = re.match(retpat, text)
			
			if retmatch: #mark a line as actually IC
				lines_to_go_back = len(retmatch.group(1))
				
				if retmatch.group(2):
					lines_to_go_back += min(int(retmatch.group(2)) - 1, 0)
				
				for line in reversed(parsed_lines):
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
			elif speaker.lower() in BOTS or re.search(dicepat, text):
				line_class = "ic"
			else:
				line_class = "ooc"
				#line_class = "ic"
			
			
			#sanitize > and <
			markedup_text =  replace_arrows(text)
			
			#process text to mark up links, and maybe images and styling?
			markedup_text = re.sub(linkpat, wrap_link, markedup_text)
			
			#sanitize & and �
			markedup_text = replace_ampersands(markedup_text)
			markedup_text = replace_emdashes(markedup_text)
			
			parsed_lines.append({	"speaker": speaker,
									"speaker_class": speaker_class,
									"line_class": line_class,
									"markedup_text": markedup_text })
				
				
				
	with open("C:/xampp/htdocs/irasite/rpg/logs/parsedlogs/month/" + filename[:-4] + ".html", 'w') as outfile:
		for line in parsed_lines:		
			outfile.write("\t<blockquote class='" + line["speaker_class"] + line["line_class"] + "'><cite>" + 
							line["speaker"] + ":</cite><p>" + line["markedup_text"] + "</p></blockquote>\n")
				
				


	print(len(parsed_lines), "lines parsed")

