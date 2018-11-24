import time
from collections import deque

from data import Data

from praw.models import Comment


class PushshiftStream:

	def __init__(self, reddit, subreddit_name, last_seen=None, **options):
		self.reddit = reddit
		self.subreddit_name = subreddit_name
		self.data = Data(save_rate=options.get('save_data_every', 10))
		self.data.load()
		self._url = 'https://api.pushshift.io/reddit/comment/search/'
		self._link_id_url = 'https://api.pushshift.io/reddit/search/submission/'
		self._comment_ids_url = 'https://api.pushshift.io/reddit/submission/comment_ids/'
		self._last_req_time = 0
		self._last_seen = last_seen or deque(maxlen=100)
		self._size = 500
		if self._last_seen:
			self._after = int(self._last_seen[-1].created_utc) - 1
		else:
			self._after = int(time.time())
		self._params = {#'subreddit': self.subreddit_name,
						'size'     : self._size,
						'after'    : self._after}

	def comments(self):
		while True:
			diff = time.time() - self._last_req_time
			if diff < 1:
				time.sleep(1 - diff)
			twoweekstime = 1209600
			twoweeksago = time.time() - twoweekstime
			mention_comments = []
			req = self.reddit.get(self._url, params=self._params)
			self._last_req_time = time.time()
			def bot_stream_comments(self, thread):
			    try:
			        botmentionreq = self.reddit.get(self._url, params= {'author' : 'ConsensusDebateBot',
			                                                        'after'  : twoweeksago})
			        botmentiondata = botmentionreq['data']
			        for botreqcomment in botmentiondata:
				        if botreqcomment.subreddit != self.subreddit:
				            thread.sticky_comment = botreqcomment
			    except Exception:
				    pass
			mentionpostreq = self.reddit.get(self._url, params= {'q' : 'u/ConsensusDebateBot', 'after' : 1541786417})
			mentionpostdata = mentionpostreq['data']
			for mentionpost in mentionpostdata:
			    mentioncomment = Comment(self.reddit, _data=mentionpost)
			    print(mentioncomment.submission)
			    mentionpostcommentids = self.reddit.get(self._comment_ids_url, params= {'link_id' : mentioncomment.submission})
			    mentionpostcomments = self.reddit.get(self._url, params= {'ids' : mentionpostcommentids})
			    mention_comments.extend(mentionpostcomments)
			    print(mentionpostcomments)
			pushshift_comments = req['data']
			pushshift_comments.extend(mention_comments)
			final_pushshift_comments = []
			for pushshift_comment in pushshift_comments:
			    if pushshift_comment not in final_pushshift_comments:
			        final_pushshift_comments.append(pushshift_comment)
			pushshift_comments = final_pushshift_comments
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
