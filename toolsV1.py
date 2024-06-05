import os



def ceil(value):
	return int(value) + bool(value % 1)


def multireplace(string: str, replacement_dictionary: dict):
	for k, v in replacement_dictionary.items():
		string = string.replace(k, v)
	return string


def enclose(string, enclosing_characters):
	return enclosing_characters + string + enclosing_characters


def file_exists(filename):
	result = os.path.isfile(filename)
	return result

def swapaxes(array):
	return list(zip(*array))