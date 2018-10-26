from collections import defaultdict


class User:

	@property
	def votes(self):
		return (sum(self._count_votes(self.voted_by).values()) + 100) / 100

	def __init__(self):
		self.post_id = None
		self.name = None
		self.voted_by = {}
		self.voted_for = {}
		self.pinned_at = None
		self.view_comments = []
		self.comments = []
		self.submission = None

	def __eq__(self, other):
		return self.name.lower() == other.name.lower()

	def __hash__(self):
		return hash(self.name.lower())

	def __lt__(self, other):
		return self.votes < other.votes 

	def __repr__(self):
		return 'User({})'.format(self.name)

	def __str__(self):
		return '({}, {})'.format(self.name, self.votes)

	def _count_votes(self, dictionary):
		received = defaultdict(int)
		for name, percent_voters in dictionary.items():
			percentage, voters = percent_voters
			received[name] += percentage
			if voters:
				for voter_name, percent in self._count_votes(voters).items():
					received[voter_name] += (percent * percentage) / 100
		for name, percentage in received.items():
			if percentage > 100:
				received[name] = 100
		return received

	def add_comment(self, comment, is_view=True):
		if is_view:
			self.view_comments.append(comment)
			self.view_comments = sorted(self.view_comments, 
										key=lambda comment: comment.created_utc,
										reverse=True)
		else:
			self.comments.append(comment)
			self.comments = sorted(self.comments,
								   key=lambda comment: len(comment.body),
								   reverse=True)

	def get_comment(self):
		if self.view_comments:
			return self.view_comments[0]
		elif self.comments:
			return self.comments[0]
		elif self.submission is not None:
			return self.submission

	def remove_comment(self, comment):
		try:
			self.comments.remove(comment)
		except ValueError:
			self.view_comments.remove(comment)
