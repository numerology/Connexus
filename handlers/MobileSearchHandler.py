__author__ = 'Yicong'
from google.appengine.ext import ndb
import json
import webapp2
import re
from api_handler import parse_search_keyword
from api_handler import stream
import constants


class MobileSearchHandler(webapp2.RequestHandler):
    def get(self):
        original_keyword_string = self.request.get('search_keywords')
        print ('MobileSearchHandler: original string: '+original_keyword_string)
        keywords = parse_search_keyword(original_keyword_string)
        queried_keywords = (keywords['plain_keywords'] + keywords['tags'])
        return_result = {"StreamNames": [], "CoverUrls": []}
        if queried_keywords:
            # allow to check matching part of the string
            all_streams = stream.query().order(-stream.num_of_view, -stream.num_of_pics)
            for temp_stream in all_streams:
                temp_stream_words = []
                temp_stream_words.extend(filter(None, re.split(r'[\s]', temp_stream.name)))
                temp_stream_words.extend(temp_stream.tags)
                temp_stream_string = " ".join(list(set(temp_stream_words) - constants.CACHED_STOP_WORDS)).lower()
                if any(temp_keyword.lower() in temp_stream_string for temp_keyword in queried_keywords):
                    return_result["StreamNames"].append(str(temp_stream.name))
                    if temp_stream.cover_url:
                        return_result["CoverUrls"].append(str(temp_stream.cover_url))
                    else:
                        return_result["CoverUrls"].append("")
        self.response.write(json.dumps(return_result))
