#!/usr/bin/env python
"""


We use the webapp.py WSGI framework to handle CGI requests, using the
wsgiref module to wrap the webapp.py WSGI application in a CGI-compatible
container. See webapp.py for documentation on RequestHandlers and the URL
mapping at the bottom of this module.  

"""

__author__ = 'wferrell@gmail.com'

from google.appengine.ext import db

class Email(db.Model):
  """This is the AppEngine data model for the Email Data."""
  email = db.EmailProperty()
  name = db.StringProperty()
  verified = db.BooleanProperty()
  timestamp = db.DateTimeProperty(auto_now_add=True)
