
def find(list, item, comparition= lambda x,y:x==y):
	for elem in list:
		if comparition(elem, item):
			return elem

	return None

