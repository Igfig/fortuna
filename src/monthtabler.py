"""
make an html table organizing the activities of the month
"""

import re, os, collections


""" static variables """

fname_pat = re.compile("(?P<month>[^_]+)_(?P<day>\d+)_(?P<number>\d+)_(?P<cast>[^.]+)")
player_order = ['f','g','r','v']
tab_depth = 5;

files = os.listdir("../logs/eberron2/month")

""" helper functions """

def get_file_a(file):
	return '<a href="log.html?log=month/' + file + '">' + \
		re.match(fname_pat, file).groupdict()['number'] + "</a>"
		

""" Assemble the database """

days = collections.OrderedDict()

for file in files:
	groups = re.match(fname_pat, file).groupdict()
	
	day_name = groups['month'] + " " + groups['day']
	
	if day_name not in days:
		days[day_name] = [[],[],[],[]]
	
	for character in groups['cast']:
		days[day_name][player_order.index(character)].append(file)
		
""" Print out the html """
		
for day, players in days.items():
	print("\t" * tab_depth + "<tr>")
	print("\t" * (tab_depth + 1) +'<th scope="row">{}</th>'.format(day.title()))
	
	for player in players:
		print("\t" * (tab_depth + 1) + "<td>", end='')
		
		print(("\n" + "\t" * (tab_depth + 2)).join(
						[get_file_a(file) for file in player]), end='')
		
		print("</td>")
	print("\t" * tab_depth + "</tr>")

	