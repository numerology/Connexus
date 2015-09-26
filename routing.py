__author__ = 'Jiaxiao Zheng'

from handlers import *
from api_handler import *
from api_handler import image
from api_handler import stream
import webapp2

routes = [
  #  webapp2.Route(r'/api/stream_list', handler = ListStreamHandler, name = 'list_api'),
    webapp2.Route(r'/api/create_stream', handler = CreateStreamHandler, name = 'list_api'),
    webapp2.Route(r'/api/change_freq', handler = TrendingFrequencyHandler, name = 'change_freq_api'),

    webapp2.Route(r'/', handler = MainPage, name = 'mainpage'),
    webapp2.Route(r'/management', handler = ManagementHandler, name = 'management'),
    webapp2.Route(r'/stream_create', handler = CstreamHandler, name = 'createstream'),
   # webapp2.Route(r'/stream_view', handler = VstreamHandler, name = 'viewstream'),
    webapp2.Route(r'/stream_list', handler = LstreamHandler, name = 'liststream'),
    webapp2.Route(r'/stream_search', handler = SstreamHandler, name = 'searchstream'),
    webapp2.Route(r'/stream_trending', handler = TstreamHandler, name = 'trendinngstream'),
    webapp2.Route(r'/error', handler = ErrorHandler, name = 'error'),
    webapp2.Route(r'/view/<id:[\w-]+>', handler = ViewStreamHandler, name = 'viewsingle'),
    webapp2.Route(r'/upload_fig', handler = UploadHandler, name = 'uploadpage'),
    webapp2.Route(r'/upload_photo', handler = PhotoUploadHandler, name = 'uploadapi'),
    webapp2.Route(r'/report_trend/<freq:[\w-]+>', handler = TrendReportHandler, name = 'uploadapi')

]
app = webapp2.WSGIApplication(routes = routes, debug = True)