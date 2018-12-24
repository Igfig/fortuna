import inspect
import traveller.terrain_types as tt
terrains = dict(inspect.getmembers(tt))

# Specify the number and width of lines to generate
length = 12
width = 48
# TODO move these to the config, and perhaps also let them be specified in the command


def travel(terrain):
	try:
		return terrains[terrain].travel(length, width)
	except KeyError:
		return f"Error: {terrain} is not a valid terrain type."


#   CHOOSE ONE OF THE FOLLOWING    #
# and leave the rest commented out #
#     (i.e. with a # in front)     #
if __name__ == '__main__':
	print("\n".join(terrains['forest'].travel(length, width)))
	# mountain.travel(length, width)
	# desert.travel(length, width)
	# hills.travel(length, width)
	# plains.travel(length, width)
	# sea.travel(length, width)
