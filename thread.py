from collections import defaultdict

from user import User
from helpers import del_key


class Thread:
	
	def __init__(self):
		self.submission = None
		self.users = defaultdict(User)
		self.ids_authors = {}
		self.sticky_comment = None
		self.pasted = None
		self.pinned_users = set()
		self.last_checked = 0
		self.total_voters = 0
		self.casted_votes = 0
		self.disabled = False

	def __iter__(self):
		return iter(self.users.values())

	def __repr__(self):
		return 'Thread({})'.format(self.id)

	def _vote_loop(self, current_name, other_names_values, seen=None):
		stack = [(current_name, other_name, value) 
				 for other_name, value in other_names_values.items()]
		while stack:
			current_name, other_name, value = stack.pop()
			if other_name not in seen:
				current = self.user(current_name)
				other = self.user(other_name)
				updated_voted_by = del_key(current.voted_by, other_name)
				other.voted_by[current_name] = (value, updated_voted_by)
				seen.add(other_name)
				stack += [(other_name, name, percentage)
						  for name, percentage in other.voted_for.items()]

	def update_votes(self, voter_name, parent_name, fullname=None,
					 value=100, unvote=False):
		voter = self.user(voter_name)
		if unvote:
			other = self.user(parent_name)
			other.voted_by.pop(voter_name)
			_seen = {parent_name}
			self._vote_loop(parent_name, other.voted_for, seen=_seen)
			voter.voted_for.pop(parent_name)
			if not voter.voted_for:
				self.total_voters -= 1
			self.casted_votes -=1
		else:
			if not voter.voted_for:
				self.total_voters += 1
			self._vote_loop(voter_name, {parent_name: value}, seen=set())
			voter.voted_for[parent_name] = value
			self.casted_votes += 1

	def sorted_users(self):
		valid_users = [user for user in self if user.votes != 1]
		return sorted(valid_users, reverse=True)

	def user(self, username):
		user = self.users[username]
		if username == self.submission.author.name:
			user.submission = self.submission
		user.name = username
		user.post_id = self.submission.id
		return user

	def top_user(self, sorted_users_list=None):
		if sorted_users_list is None:
			sorted_users_list = self.sorted_users()
		for user in sorted_users_list:
			if user.get_comment() is not None:
				return user

	def top_users(self, sorted_users_list=None):
		_top_users = set()
		if sorted_users_list is None:
			sorted_users_list = self.sorted_users()
		top_user = self.top_user(sorted_users_list=sorted_users_list)
		for user in sorted_users_list:
			if user.votes == top_user.votes and user.get_comment() is not None:
				_top_users.add(user)
		return _top_users
		
	def parent(self, parent_id):
		return self.ids_authors[parent_id]

	def chart(self, chart_limit, sorted_users_list=None):
		columns = ('username | comment link | votes\n'
				   '---|---|---\n')
		rows = ''
		for user in sorted_users_list[:chart_limit]:
			user_comment = user.get_comment()
			if user_comment is None:
				permalink = 'None'
			else:
				permalink = f'[link]({user_comment.permalink})'
			rows += f'u/{user.name} | {permalink} | {user.votes}\n'
		return columns + rows

	def get_body(self, comment_template, char_limit, chart_limit,
				 top_user=None, sorted_users_list=None):
		if sorted_users_list is None:
			sorted_users_list = self.sorted_users()
		if top_user is None:
			top_user = self.top_user(sorted_users_list=sorted_users_list)
		view_comment = top_user.get_comment()
		try:
			body = view_comment.body
		except AttributeError:
			body = view_comment.selftext
		if len(body) > char_limit:
			body = body[:char_limit]
		_chart = self.chart(chart_limit, sorted_users_list=sorted_users_list)
		keywords = {
			'{permalink}'  : view_comment.permalink,
			'{author_name}': view_comment.author.name,
			'{votes}'      : str(top_user.votes),
			'{body}'       : body,
			'{chart}'      : _chart
		}
		for keyword, value in keywords.items():
			comment_template = comment_template.replace(keyword, value)
		return comment_template
