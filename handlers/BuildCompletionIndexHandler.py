__author__ = 'Yicong'
import webapp2
from google.appengine.ext import ndb
from api_handler import *
from handlers import *
from nltk.corpus import stopwords
import constants

CACHED_STOP_WORDS = set(stopwords.words("english"))


class CompletionIndex(ndb.model):
    keywords = ndb.StringProperty(repeated=True, indexed=False)


class BuildCompletionIndexHandler(webapp2.RequestHandler):
    def post(self):
        keywords = []
        known_keywords = []
        completionindex = CompletionIndex.query().get()
        if not completionindex:
            # No completionindex existing
            completionindex=CompletionIndex(keywords=[])
        streams = stream.query(-stream.viewsnum_of_view, -stream.num_of_pics)
        for temp_stream in streams:
            for temp_word in extract_stream_keywords(temp_stream):
                if temp_word in known_keywords:
                    continue
                keywords.append(temp_word)
                known_keywords.add(temp_word)

        completionindex.keywords = keywords
        completionindex.put()
        constants.AUTO_COMPLETION_INDEX = completionindex


def extract_stream_keywords(temp_stream):
    raw_keywords = []
    if temp_stream:
        raw_keywords.append(filter(None, re.split(r'[,;\t\r\n\s]',str(temp_stream.name))))
        raw_keywords.append(tags)
    keywords = list(set(raw_keywords)-CACHED_STOP_WORDS)
    return keywords
