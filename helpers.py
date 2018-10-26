

def is_deleted(thing):
	try:
		content = thing.body
	except AttributeError:
		content = thing.selftext
	return thing.author is None and content == '[deleted]'


def del_key(dictionary, key):
	return {k: (v[0], del_key(v[1], key)) 
			for k, v in dictionary.items() if k != key}