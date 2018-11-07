import time
from collections import deque

from praw.models import Comment


class PushshiftStream:

	def __init__(self, reddit, subreddit_name, last_seen=None):
		self.reddit = reddit
		self.subreddit_name = subreddit_name
		self._url = 'https://api.pushshift.io/reddit/comment/search/'
		self._last_req_time = 0
		self._last_seen = last_seen or deque(maxlen=100)
		self._size = 500
		if self._last_seen:
			self._after = int(self._last_seen[-1].created_utc) - 1
		else:
			self._after = int(time.time())
		self._params = {'subreddit': self.subreddit_name,
						'size'     : self._size,
						'after'    : self._after}

	def comments(self):
		while True:
			diff = time.time() - self._last_req_time
			if diff < 1:
				time.sleep(1 - diff)
			req = self.reddit.get(self._url, params=self._params)
			self._last_req_time = time.time()
			pushshift_comments = req['data']
			new_praw_comments = []
			for pushshift_comment in pushshift_comments:
				comment = Comment(self.reddit, _data=pushshift_comment)
				if comment not in self._last_seen:
					new_praw_comments.append(comment)
			if new_praw_comments:
				for comment in new_praw_comments:
					self._last_seen.append(comment)
					yield comment
				self._params['after'] = comment.created_utc - 1
			else:
				yield None
