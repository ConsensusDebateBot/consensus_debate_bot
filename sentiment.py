from nltk.tokenize import sent_tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class Sentiment(object):
    vader = None

    def __init__(self, *args, **kwargs):
        # TODO: pass lexicon_file and emoji_lexicon kwargs to vader if needed
        self.vader = SentimentIntensityAnalyzer()

    def get_sentiment(self, body, condense=False):
        ret = []
        for sentence in sent_tokenize(body):
            ret.append(self.vader.polarity_scores(sentence))

        if not condense:
            return ret

        final_sent = {}
        for s in ret:
            for k, v in s.items():
                if k not in final_sent:
                    final_sent[k] = v
                    continue
                final_sent[k] += v
        return final_sent
