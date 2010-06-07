#!/usr/bin/env python
"""
Isabella
Version 0.0.1

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

# Set to true to see stack traces and template debugging information
_DEBUG = True

class BaseRequestHandler(webapp.RequestHandler):
  """The common class for all M1 requests"""

  def handle_exception(self, exception, debug_mode):
      exception_name = sys.exc_info()[0].__name__
      exception_details = str(sys.exc_info()[1])
      exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
      logging.error(exception_traceback)
      exception_expiration = 600 # seconds 
      mail_admin = "wferrell@gmail.com" # must be an admin
      sitename = "isabella"
      throttle_name = 'exception-'+exception_name
      throttle = memcache.get(throttle_name)
      if throttle is None:
          memcache.add(throttle_name, 1, exception_expiration)
          subject = '[%s] exception [%s: %s]' % (sitename, exception_name,
                                                 exception_details)
          mail.send_mail_to_admins(sender=mail_admin,
                                   subject=subject,
                                   body=exception_traceback)

      values = {}
      template_name = 'error.html'
      if users.is_current_user_admin():
        values['traceback'] = exception_traceback
      #values['traceback'] = exception_traceback
      directory = os.path.dirname(os.environ['PATH_TRANSLATED'])
      path = os.path.join(directory, os.path.join('templates', template_name))
      self.response.out.write(template.render(path, values, debug=_DEBUG))

  def generate(self, template_name, template_values={}):
    """Generates the given template values into the given template.

    Args:
        template_name: the name of the template file (e.g., 'index.html')
        template_values: a dictionary of values to expand into the template
    """

    # Populate the values common to all templates
    values = {
      #'user': users.GetCurrentUser(),
      'alert': 'testing alert',
      'debug': self.request.get('deb'),
      'current_header': template_name,
    }
    values.update(template_values)
    directory = os.path.dirname(os.environ['PATH_TRANSLATED'])
    path = os.path.join(directory, os.path.join('templates', template_name))
    self.response.out.write(template.render(path, values, debug=_DEBUG))


class HomePageHandler(BaseRequestHandler):
  """
  Generates the home page.

  """
  def get(self):
    logging.info('Visiting the home page')
    self.generate('home.html', {
      'header_title': 'Isabella',
      'header_keywords': 'the ladies',
      'header_description':'the ladies',
      })

class ContactPageHandler(BaseRequestHandler):
  """
  Generates the contact page.

  """
  def get(self):
    logging.info('Visiting the contact page')
    self.generate('contact.html', {
      })
      
class AboutPageHandler(BaseRequestHandler):
  """
  Generates the about page.

  """
  def get(self):
    logging.info('Visiting the about page')
    self.generate('about.html', {
      })


class ErrorPageHandler(BaseRequestHandler):
  """
  Generates the error page.

  """
  def get(self):
    logging.info('Visiting the error page')
    self.generate('error.html', {
      })

class OptOutEmailHandler(BaseRequestHandler):
  """
  Generates the Opt Out page.

  """
  def get(self):
    logging.info('Visiting the Opt Out page')
    self.generate('optout.html', {
      })



class SiteMapHandler(BaseRequestHandler):
  """
    Generates the sitemap.
  """
  def get(self):
    logging.info('Displaying the sitemap')
    self.generate('sitemap.xml', {
    })


class RobotsHandler(BaseRequestHandler):
  """
    Generates the robots.txt file.
  """
  def get(self):
    logging.info('Displaying the robots.txt file')
    self.generate('robots.txt', {
    })
