"""Bot's configuration settings."""
import os


# Bot's account credentials.
CLIENT_ID = '' or os.environ['reddit_client_id']
CLIENT_SECRET = '' or os.environ['reddit_client_secret']
USER_AGENT = 'r/ConsensusDebate bot (by /u/gourari)'
USERNAME = '' or os.environ['reddit_username']
PASSWORD = '' or os.environ['reddit_password']

SUBREDDIT_NAME = 'gouraritest'  # Without the prefix "r/".

USER_FLAIR_TEXT_TEMPLATE = '{hours_average} Hours Won - {votes_average}% Avg. Votes'

POST_FLAIR_TEXT_TEMPLATE = '{voters} Users Voted / {votes_cast} Votes Cast'

COMMANDS_PREFIX = '!' or '#'

VOTE_KEYWORD = 'vote' or 'v'
UNVOTE_KEYWORD = 'unvote' or 'uv'
VIEW_KEYWORD = 'view' or 'vi'
DISABLE_VOTE_KEYWORD = 'disablevote'

# If a thread's age is less than this
# duration, pinned comments are checkd almost
# constantly.
PINNED_CHECK_DURATION = 7  # In days.

# Number of times pinned comments are checked per day once a
# thread's age is past the PINNED_CHECK_DURATION.
CHECKS_PER_DAY = 10

# Number of users showed in the chart.
CHART_LIMIT = 5

CHARACTER_LIMIT = 5000  # Number of charachters of the pinned comment.

SAVE_DATA_EVERY = 10  # In minutes.

FLAIR_IGNORE = [
	'Chackoony',
	'False1512',
	'Gourari',
]

with open('sticky comment template.txt') as f:
	STICKY_COMMENT_TEMPLATE = f.read().strip()
