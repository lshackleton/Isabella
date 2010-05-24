#!/usr/bin/env python
"""

We use the webapp.py WSGI framework to handle CGI requests, using the
wsgiref module to wrap the webapp.py WSGI application in a CGI-compatible
container. See webapp.py for documentation on RequestHandlers and the URL
mapping at the bottom of this module.  

"""

__author__ = 'wferrell@gmail.com'

import cgi
import csv
import datetime
import htmlentitydefs
import math
import os
import re
import sgmllib
import sys
import time
import urllib
import logging
import wsgiref.handlers
import base64
import hmac
import sha
import traceback

from google.appengine.api import datastore
from google.appengine.api import datastore_types
from google.appengine.api import datastore_errors
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import mail
from google.appengine.api import urlfetch

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext import search
from google.appengine.ext import bulkload
from google.appengine.ext import db

from django.utils import simplejson
from django.http import HttpResponse

# Data models
import models

# Simple web handlers
import webpagehandlers

# email handlers
import email_handlers

## Set logging level.
logging.getLogger().setLevel(logging.INFO)




# Map URLs to our RequestHandler classes above
URL_MAP = [
# after each URL map we list the html template that is displayed
   ('/contact', webpagehandlers.ContactPageHandler), #contact.html
   ('/about', webpagehandlers.AboutPageHandler), #about.html
   ('/optout', webpagehandlers.OptOutEmailHandler),   
   ('/sitemap', webpagehandlers.SiteMapHandler),
   ('/sitemap.xml', webpagehandlers.SiteMapHandler),
   ('/robots.txt', webpagehandlers.RobotsHandler),
   ('/addtoemaillist.do', email_handlers.AddToEmailListActionHandler),
   ('/confirmemailaddress.do', email_handlers.ConfirmEmailAddressActionHandler),   
   ('/optoutemailaddress.do', email_handlers.OptOutEmailActionHandler),
   ('/.*$', webpagehandlers.HomePageHandler), #home.html
]


def main():
  application = webapp.WSGIApplication(URL_MAP, debug=webpagehandlers._DEBUG)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
