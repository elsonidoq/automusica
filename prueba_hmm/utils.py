
def tab_string(obj, number_of_tabs= 1):
	""" le agrega tabs a un string """
	if not isinstance(obj,str):
		obj= repr(obj)

	res= ""
	for line in obj.split("\n"):
		line= '\t'*number_of_tabs + line
		res+= line + '\n'

	return res

def find(list, item, comparition= lambda x,y:x==y):
	for elem in list:
		if comparition(elem, item):
			return elem

	return None

