from os import getcwd
with open(getcwd() + "/test.text", "w+") as file:
	for i in range(1, 10000, 1):
		file.write("Test \n")