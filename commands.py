import re


class Commands:

	def __init__(self, commands_prefix, **commands_keywords):
		regex_strings = {
			'vote'		 : r'{}\s*(?P<vcmd>{})\s*'
						   r'((0*(?P<fv>(1(?!\s*%|\d|[.,]\d))|(0[.,]\d\d?)))|'
						   r'(0*(?P<pv>\d+)\s*%?)|'
						   r'(\\#\s*0*(?P<nv>\d+)))?',
			'unvote'	 : r'{}\s*(?P<unvcmd>{})',
			'view'		 : r'{}\s*{}',
			'disablevote': r'{}\s*{}',
		}
		for command_name, regex_string in regex_strings.items():
			command_keyword = commands_keywords.get(command_name)
			formatted_regex_string = regex_string.format(commands_prefix,
														 command_keyword)
			setattr(self,
					f'{command_name}_regex',
					re.compile(formatted_regex_string, re.I))

	def is_valid(self, command_name, text):
		return getattr(self, f'{command_name}_regex').search(text) is not None

	def percentage(self, text, votes):
		match = self.vote_regex.search(text)
		nvotes = match.group('nv')
		floatv = match.group('fv')
		percent = match.group('pv')
		if floatv is not None:
			n = int(float(floatv.replace(',', '.')) * 100)
		elif percent is not None:
			n = int(percent)
		elif nvotes is not None:
			n = int((int(nvotes) * 100) / votes) 
		else:
			n = 100
		if n > 100:
			n = 100
		elif n < 1:
			return None
		return n
