import traceback
import logging

import praw
import prawcore

from bot import Bot


def run():
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.ERROR)
	formatter = logging.Formatter('%(asctime)s [%(levelname)s] '
								  '%(message)s')
	file_handler = logging.FileHandler('logs.log')
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)
	print('!!! Press "Ctrl + C" to save data and stop the bot.\n')
	while True:
		try:
			print('>>> Running...', end='\r')
			bot.main()
		except KeyboardInterrupt:
			print('>>> Saving data...', end='\r')
			bot.data.save(force=True, last_seen=bot.stream._last_seen)
			print('>>> Done.         ')
			break
		except Exception:
			logger.exception('Runtime Error')
			bot.data.save(force=True, last_seen=bot.stream._last_seen)
			print('An error has occurred, check "logs.log" for details.\n')


if __name__ == '__main__':
	try:
		print('\n>>> Loading...', end='\r')
		from configuration import (CLIENT_ID, CLIENT_SECRET, USER_AGENT,
								   USERNAME, PASSWORD, SUBREDDIT_NAME,
								   USER_FLAIR_TEXT_TEMPLATE, COMMANDS_PREFIX,
								   POST_FLAIR_TEXT_TEMPLATE, VOTE_KEYWORD,
								   UNVOTE_KEYWORD, VIEW_KEYWORD,
								   DISABLE_VOTE_KEYWORD, PINNED_CHECK_DURATION,
								   CHECKS_PER_DAY, CHART_LIMIT, CHARACTER_LIMIT,
								   SAVE_DATA_EVERY, FLAIR_IGNORE, 
								   STICKY_COMMENT_TEMPLATE,)
		reddit = praw.Reddit(client_id=CLIENT_ID,
							 client_secret=CLIENT_SECRET,
							 user_agent=USER_AGENT,
							 username=USERNAME,
							 password=PASSWORD,)
		bot = Bot(
			reddit, SUBREDDIT_NAME,
			sticky_comment_template=STICKY_COMMENT_TEMPLATE,
			user_flair_text_template=USER_FLAIR_TEXT_TEMPLATE,
			post_flair_text_template=POST_FLAIR_TEXT_TEMPLATE,
			commands_prefix=COMMANDS_PREFIX,
			vote=VOTE_KEYWORD,
			unvote=UNVOTE_KEYWORD,
			view=VIEW_KEYWORD,
			disablevote=DISABLE_VOTE_KEYWORD,
			pinned_check_duration=PINNED_CHECK_DURATION,
			checks_per_day=CHECKS_PER_DAY,
			chart_limit=CHART_LIMIT,
			character_limit=CHARACTER_LIMIT,
			flair_ignore=FLAIR_IGNORE,
			save_data_every=SAVE_DATA_EVERY,
				  )
	except ImportError as ie:
		input('Unable to load configuration: {}'.format(ie))
	except prawcore.exceptions.RequestException:
		input('Unable to make an HTTP connection.')
	except prawcore.exceptions.ResponseException:
		input('Incorrect client id or client secrect.')
	except prawcore.exceptions.OAuthException:
		input('Incorrect username or password.')
	except Exception:
		print('Initialization Error: \n')
		traceback.print_exc()
		input()
	else:
		run()
