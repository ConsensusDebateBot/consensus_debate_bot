from nltk.tokenize import sent_tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class Sentiment(object):
    vader = None

    def __init__(self, **kwargs):
        self.vader = SentimentIntensityAnalyzer(**kwargs)

    def get_all_sentiments(self, body):
        ret = []
        for sentence in sent_tokenize(body):
            ret.append(self.vader.polarity_scores(sentence))
        return ret
