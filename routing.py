__author__ = 'Jiaxiao Zheng'

from handlers.ExtensionUploadHandler import *
from handlers.AutoCompleteHandler import *
from handlers.BuildCompletionIndexHandler import *
from handlers.handlers import *
from handlers.api_handler import *
from handlers.api_handler import image
from handlers.api_handler import stream
import webapp2



routes = [
  #  webapp2.Route(r'/api/stream_list', handler = ListStreamHandler, name = 'list_api'),
    webapp2.Route(r'/api/create_stream', handler = CreateStreamHandler, name = 'list_api'),
    webapp2.Route(r'/api/change_freq', handler = TrendingFrequencyHandler, name = 'change_freq_api'),
    webapp2.Route(r'/api/stream_search', handler = SearchHandler, name = 'search_api'),
    webapp2.Route(r'/api/confirm_subscribe', handler = ConfirmSubscribeStreamHandler, name = 'confirm_subscribe_api'),
    webapp2.Route(r'/api/delete_stream/<id:[\w-]+>', handler = DeleteStreamHandler, name = 'delete_api'),
    webapp2.Route(r'/api/delete_fig/<id:[\w-]+>/<fig_key:[\S-]+>', handler = DeleteFigHandler, name = 'delete_api'),
    webapp2.Route(r'/api/delete_fig_partial/<id:[\w-]+>/<fig_key:[\S-]+>', handler = MiniDeleteFigHandler, name = 'delete_api'),
    webapp2.Route(r'/api/unsubscribe_stream', handler = UnsubscribeStreamHandler, name = 'unsubscribe_api'),
  # YW: Add autocomplete handler
    webapp2.Route(r'/api/autocomplete', handler=AutoCompleteHandler, name='autocomplete'),
    webapp2.Route(r'/api/stream_autocomplete', handler=StreamAutoCompleteHandler, name='streamautocomplete'),  # autocomplete for stream name
    webapp2.Route(r'/api/build_completion_index', handler=BuildCompletionIndexHandler, name='build_completion_index'),

    webapp2.Route(r'/api/upload_image_from_extension', handler = UploadFromExtensionHandler),


    webapp2.Route(r'/', handler = MainPage, name = 'mainpage'),
    webapp2.Route(r'/management', handler = ManagementHandler, name = 'management'),
    webapp2.Route(r'/stream_create', handler = CstreamHandler, name = 'createstream'),
   # webapp2.Route(r'/stream_view', handler = VstreamHandler, name = 'viewstream'),
    webapp2.Route(r'/stream_list', handler = LstreamHandler, name = 'liststream'),
    #YW: change handler for stream search
    webapp2.Route(r'/stream_search', handler = SearchHandler, name = 'searchstream'),
   # webapp2.Route(r'/stream_search', handler = SstreamHandler, name = 'searchstream'),
    webapp2.Route(r'/stream_trending', handler = TstreamHandler, name = 'trendinngstream'),
    webapp2.Route(r'/error/<msg:[\s\S-]+>', handler = ErrorHandler, name = 'error'),
    webapp2.Route(r'/view/<id:[\w-]+>/<page:[\w-]+>', handler = ViewStreamHandler, name = 'viewsingle'),
    webapp2.Route(r'/refresh/<id:[\w-]+>/<page:[\w-]+>', handler = RefreshHandler, name = 'refresh'),
    webapp2.Route(r'/view/<id:[\w-]+>', handler = DefaultViewStreamHandler, name = 'viewsingle'),
    webapp2.Route(r'/geoview/<id:[\w-]+>', handler = GeoView, name = 'geoview'),
 #   webapp2.Route(r'/geoview_fetch/<id:[\w-]+>', handler = GeoViewFetch, name = 'geoviewf'),
    webapp2.Route(r'/upload_fig', handler = UploadHandler, name = 'uploadpage'),
    webapp2.Route('/upload_photo', handler = PhotoUploadHandler, name = 'uploadapi'),
    webapp2.Route('/generate_upload_url/<stream_id:[\w-]+>', handler = GenerateUploadUrlHandler),

    #YW add routing for subscribe pate
    webapp2.Route(r'/subscribe/<stream_id:[\w-]+>', handler = SubscribeStreamHandler, name = 'subscribestream'),
    webapp2.Route(r'/report_trend/<freq:[\w-]+>', handler = TrendReportHandler, name = 'uploadapi')
]
app = webapp2.WSGIApplication(routes = routes, debug = True)
