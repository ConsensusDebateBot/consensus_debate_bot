import time

from praw.models import Submission, Comment

from data import Data
from stream import PushshiftStream
from commands import Commands
from helpers import is_deleted


class Bot:

	@property
	def mods(self):
		if ((time.time() - self._mods_updated_at) / 3600 >=
				self._mods_refresh_rate):
			self._mods = self.subreddit.moderator()
			self._mods_updated_at = time.time()
		return self._mods

	def __init__(self, reddit, subreddit_name, **options):
		self.reddit = reddit
		self.subreddit = self.reddit.subreddit(subreddit_name)
		self.me = self.reddit.user.me()
		self.post_flair_template_id = None
		self.data = Data(save_rate=options.get('save_data_every', 10))
		self.data.load()
		self.stream = PushshiftStream(reddit, subreddit_name, self.data._seen)
		self.commands = Commands(**options)
		self.comment_template = options.get('sticky_comment_template')
		self.comment_template = self.comment_template.replace('{message_link}',
		f'https://www.reddit.com/message/compose?to=%2Fr%2F{self.subreddit.display_name}')
		self.user_flair_template = options.get('user_flair_text_template')
		self.post_flair_template = options.get('post_flair_text_template')
		self.pinned_check_duration = options.get('pinned_check_duration', 7)
		self.checks_per_day = options.get('checks_per_day', 1)
		self.chart_limit = options.get('chart_limit', 5)
		self.character_limit = options.get('character_limit', 1000)
		self.flair_ignore = options.get('flair_ignore')
		self.sleep_time = options.get('sleep_time')
		self._mods = self.subreddit.moderator()
		self._mods_updated_at = time.time()
		self._mods_refresh_rate = 6

	def update_sticky(self, thread):
		now = time.time()
		sorted_users = thread.sorted_users()
		top_user = thread.top_user(sorted_users_list=sorted_users)
		if top_user is None:
			if thread.sticky_comment is not None:
				thread.sticky_comment.delete()
				for user in thread.pinned_users:
					pinned_time = now - user.pinned_at
					user_flair_info = self.data.flair_infos[user.name]
					user_flair_info.pinned_for[thread.submission.id] += pinned_time
					user.pinned_at = None
				thread.sticky_comment = None
				thread.pasted = None
				thread.pinned_users = set()
			return None
		top_users = thread.top_users(sorted_users_list=sorted_users)
		top_user = sorted(list(top_users), key=lambda u: u.get_comment().created_utc, reverse=True)[0]
		view_comment = top_user.get_comment()
		body = thread.get_body(self.comment_template, self.character_limit,
							   self.chart_limit, top_user=top_user,
							   sorted_users_list=sorted_users)
		if thread.sticky_comment is None:
			try:
				submission = view_comment.submission
			except AttributeError:
				submission = view_comment
			thread.sticky_comment = submission.reply(body)
			try:
			    thread.sticky_comment.mod.distinguish(how='yes', sticky=True)
			except Exception:
			    pass
			for user in top_users:
				user.pinned_at = now
		elif thread.sticky_comment.body != body:
			thread.sticky_comment.edit(body)
			for user in top_users - thread.pinned_users:
				user.pinned_at = now
			for user in thread.pinned_users - top_users:
				pinned_time = now - user.pinned_at
				user_flair_info = self.data.flair_infos[user.name]
				user_flair_info.pinned_for[thread.submission.id] += pinned_time
				user.pinned_at = None
		else:
			return None
		thread.pasted = view_comment
		thread.pinned_users = top_users

	def vote_handler(self, comment):
		thread = self.data.thread(comment.submission)
		if thread.disabled:
			return None
		voter_name = comment.author.name
		parent_name = thread.parent(comment.parent_id)
		if parent_name is None:
			return None
		voter = thread.user(voter_name)
		prev_total = thread.total_voters
		prev_casts = thread.casted_votes
		if parent_name == self.me:
			if thread.pasted is not None:
				parent_name = thread.pasted.author.name
			else:
				return None
		if (self.commands.is_valid('vote', comment.body) and
				self.commands.percentage(comment.body, voter.votes) is not None and
				parent_name != voter_name):
			percentage = self.commands.percentage(comment.body, voter.votes)
			if parent_name in voter.voted_for:
				thread.update_votes(voter_name, parent_name, unvote=True)
			thread.update_votes(voter_name, parent_name, value=percentage,
								fullname=comment.fullname)
		elif (self.commands.is_valid('unvote', comment.body) and
			  parent_name in voter.voted_for):
			thread.update_votes(voter_name, parent_name, unvote=True)
		else:
			return None
		self.update_sticky(thread)
		if (prev_casts != thread.casted_votes or
				prev_total != thread.total_voters):
			self.update_post_flair(comment.submission, thread)

	def update_post_flair(self, submission, thread):
		if self.post_flair_template_id is None:
			choices = submission.flair.choices()
			try:
				self.post_flair_template_id = choices[0]['flair_template_id']
			except IndexError:
				return None
		flair = self.post_flair_template.format(voters=thread.total_voters,
												votes_cast=thread.casted_votes)
		submission.flair.select(self.post_flair_template_id, text=flair)

	def comment_handler(self, comment):
		thread = self.data.thread(comment.submission)
		if thread.disabled:
			return None
		author_name = comment.author.name
		if self.commands.is_valid('view', comment.body):
			thread.user(author_name).add_comment(comment)
		else:
			thread.user(author_name).add_comment(comment, is_view=False)
		self.update_sticky(thread)

	def retreived(self):
		updated_p = []
		updated_v = []
		p_fullnames, v_fullnames = self.data.fullnames(
										self.pinned_check_duration,
										self.checks_per_day)
		if p_fullnames or v_fullnames:
			updated = list(self.reddit.info(p_fullnames + v_fullnames))
			updated_p = updated[:len(p_fullnames)]
			updated_v = updated[len(p_fullnames):]
		return(updated_p, updated_v)

	def update_pinned(self, p_things):
		_threads = set()
		for thing in p_things:
			if isinstance(thing, Comment):
				submission = thing.submission
				body = thing.body
			else:
				submission = thing
				body = thing.selftext
			thread = self.data.thread(submission)
			if isinstance(thread.pasted, Comment):
				pasted_body = thread.pasted.body
			else:
				pasted_body = thread.pasted.selftext
			if pasted_body != body:
				username = thread.pasted.author.name
				user = thread.user(username)
				if isinstance(thread.pasted, Comment):
					user.remove_comment(thread.pasted)
				else:
					user.submission = None
				if not is_deleted(thing) and not thing.removed:
					is_view = self.commands.is_valid('view', body)
					if isinstance(thing, Comment):
						user.add_comment(thing, is_view=is_view)
					else:
						thread.submission = thing
						user.submission = thing
						user.is_view = is_view
						thread.is_view = is_view
				_threads.add(thread)
			thread.last_checked = time.time()
		return _threads

	def update_v(self, v_comments):
		to_update_flair = set()
		_threads = set()
		for comment in v_comments:
			thread = self.data.thread(comment.submission)
			username = thread.ids_authors[comment.fullname]
			user = thread.user(username)
			for name, value_fullname in user.voted_for.items():
				value, fullname = value_fullname
				if fullname == comment.fullname:
					break
			if (is_deleted(comment) or
					self.commands.is_valid('unvote', comment.body) or
					not self.commands.is_valid('vote', comment.body)):
				thread.update_votes(username, name, unvote=True)
				_threads.add(thread)
				to_update_flair.add(thread)
			elif (self.commands.is_valid('vote', comment.body) and
				  self.commands.percentage(comment.body, user.votes) is not None):
				percentage = self.commands.percentage(comment.body, user.votes)
				if percentage != value:
					thread.update_votes(username, name, unvote=True)
					thread.update_votes(username, name, value=percentage, fullname=comment.fullname)
					_threads.add(thread)
			thread.last_checked = time.time()
		return (_threads, to_update_flair)

	def update_all(self):
		p_things, v_comments = self.retreived()
		to_update_p = self.update_pinned(p_things)
		to_update_v, to_update_flair = self.update_v(v_comments)
		to_update = to_update_p | to_update_v
		for thread in to_update:
			self.update_sticky(thread)
		for thread in to_update_flair:
			self.update_post_flair(thread.submission, thread)

	def update_users_flair(self, usernames):
		mappings = []
		for username in usernames:
			if username not in self.flair_ignore:
				h, v = self.data.user_flair_averages(username)
				flair = self.user_flair_template.format(hours_average=h,
														votes_average=v)
				mappings.append({'user': username, 'flair_text': flair})
		if mappings:
			self.subreddit.flair.update(mappings)

	def main(self):
		comments_stream = self.stream.comments()
		while True:
			to_flair = set()
			for comment in comments_stream:
				if comment is not None:
					thread = self.data.thread(comment.submission)
					if thread.submission is not None:
						thread.is_view = self.commands.is_valid('view', thread.submission.selftext)
					thread.ids_authors[comment.fullname] = comment.author.name
				else:
					break
				if comment.author == self.me:
					continue
				elif (self.commands.is_valid('vote', comment.body) or
					  self.commands.is_valid('unvote', comment.body)):
					self.vote_handler(comment)
				elif (self.commands.is_valid('disablevote', comment.body) and
					  comment.author in self.mods):
					thread = self.data.thread(comment.submission)
					thread.disabled = True
				self.comment_handler(comment)
				to_flair.add(comment.author.name)
			self.update_users_flair(to_flair)
			self.update_all()
			self.data.clean()
			self.data.save(last_seen=self.stream._last_seen)
			time.sleep(self.sleep_time * 60)
