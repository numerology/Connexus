__author__ = 'Jiaxiao Zheng'

from handlers import *
import webapp2

routes = [
    webapp2.Route(r'/', handler = MainPage, name = 'mainpage'),
    webapp2.Route(r'/management', handler = ManagementHandler, name = 'management'),
    webapp2.Route(r'/stream_create', handler = CstreamHandler, name = 'createstream'),
    webapp2.Route(r'/stream_view', handler = VstreamHandler, name = 'viewstream'),
    webapp2.Route(r'/stream_list', handler = LstreamHandler, name = 'liststream'),
    webapp2.Route(r'/stream_search', handler = SstreamHandler, name = 'searchstream'),
    webapp2.Route(r'/stream_trending', handler = TstreamHandler, name = 'trendinngstream'),
    webapp2.Route(r'/error', handler = ErrorHandler, name = 'error'),
]
app = webapp2.WSGIApplication(routes = routes, debug = True)