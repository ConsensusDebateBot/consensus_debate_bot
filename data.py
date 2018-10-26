import time
import pickle
import math
from collections import defaultdict, deque

from thread import Thread


class UserFlair:

	def __init__(self):
		self.pinned_for = defaultdict(int)
		self.received = []


class Data:

	def __init__(self, save_rate=60):
		self._last_saved = 0
		self._last_cleaned = 0
		self._clean_rate = 86400
		self._seen = deque(maxlen=100)
		self.save_rate = save_rate * 60
		self.threads = defaultdict(Thread)
		self.flair_infos = defaultdict(UserFlair)

	def archived_threads(self):
		archived = []
		now = time.time()
		for post_id, thread in self.threads.items():
			try:
				if ((now - thread.submission.created_utc) / 86400) >= 180:
					archived.append(thread)
			except TypeError:
				continue
		return archived
	
	def save(self, force=False, last_seen=None):
		if force or (time.time() - self._last_saved) >= self.save_rate:
			with open('data.pkl', 'wb') as fp:
				data = (self.threads, self.flair_infos, last_seen)
				pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)

	def load(self):
		try:
			with open('data.pkl', 'rb') as fp:
				self.threads, self.flair_infos, self._seen = pickle.load(fp)
		except (FileNotFoundError, EOFError):
			return None

	def clean(self):
		if (time.time() - self._last_cleaned) < self._clean_rate:
			return None
		for thread in self.archived_threads():
			for user in thread:
				user_flair_info = self.flair_infos[user.name]
				average_received = user.votes / thread.total_voters
				user_flair_info.received.append(average_received)
				if user.pinned_at is not None:
					pinned_time = time.time() - thread.pinned_at
					user_flair_info.pinned_for[thread.id] += pinned_time
			self.threads.pop(thread.id)
		self._last_cleaned = time.time()

	def thread(self, submission):
		thread = self.threads[submission.id]
		if thread.submission is None:
			submission._fetch()
			thread.submission = submission
		if submission.fullname not in thread.ids_authors:
			thread.ids_authors[submission.fullname] = submission.author.name
		return thread 

	def user_flair_averages(self, username):
		votes_averages = []
		pinned_for = defaultdict(int)
		hours_average = 0
		votes_average = 0
		now = time.time()
		for _id, thread in self.threads.items():
			if username in thread.users:
				user = thread.user(username)
				if user.pinned_at is not None:
					pinned_for[_id] = now - user.pinned_at
				if user.voted_by:
					votes_averages.append(user.votes / thread.total_voters)
		votes_averages += self.flair_infos[username].received
		for id_, duration in self.flair_infos[username].pinned_for.items():
			pinned_for[id_] += duration
		if votes_averages:
			votes_average = sum(votes_averages) * 100 / len(votes_averages)
		if pinned_for:
			hours_average = (sum(pinned_for.values()) / 3600) / len(pinned_for)
		return ('{:.2f}'.format(hours_average),
				'{:.2f}'.format(votes_average))

	def fullnames(self, duration, checks):
		fullnames = []
		now = time.time()
		if checks == 0:
			nchecks = math.inf
		else:
			nchecks = 1 / checks
		for id_, thread in self.threads.items():
			pasted = thread.pasted
			if (pasted is not None and
					((now - thread.submission.created_utc) / 86400 < duration or
					 ((now - thread.last_checked) / 86400) >= nchecks)):
				fullnames.append(pasted.fullname)
		return fullnames