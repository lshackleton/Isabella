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
      mail_admin = "info@miracleonewines.com" # must be an admin
      sitename = "miracleonewines"
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
      #'title': 'Home',
      'header_title': 'Isabella',
      'header_keywords': 'the ladies',
      'header_description':'the ladies',
      })

class EmailAFriendHandler(BaseRequestHandler):
  """
  Generates the email a friend  page.

  """
  def get(self):
    logging.info('Visiting the email a friend page')
    self.generate('emailafriend.html', {
      #'title': 'Email A Friend',
      'header_title': 'Email A Friend | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'miracle one, miracle one wines, email a friend',
      'header_description':'After several years in the making, we are incredibly excited to release our Carneros Chardonnay and Napa Valley-Carneros Pinot Noir in May 2009.',
      })


class ContactPageHandler(BaseRequestHandler):
  """
  Generates the contact page.

  """
  def get(self):
    logging.info('Visiting the contact page')
    self.generate('contact.html', {
      #'title': 'Contact',
      'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
      'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
      })
      
class AboutPageHandler(BaseRequestHandler):
  """
  Generates the about page.

  """
  def get(self):
    logging.info('Visiting the about page')
    self.generate('about.html', {
      #'title': 'About',
      'header_title': 'About | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'wine, wines, miracle one, miracle one wine, pinot noir, buy wine, purchase wine, red wine, ryan donnelly, lane shackleton, napa valley, carneros',
      'header_description':'Miracle One Wines is the producer of Miracle One Chardonnay and Pinot Noir. Visit miracleonewines.com/about to find out more about Miracle One the company and the people behind the wine.',
      })

class ConfirmNewsletterHandler(BaseRequestHandler):
  """
  Generates the Confirm Newsletter page.

  """
  def get(self):
    logging.info('Visiting the Confirm Newsletter page')
    self.generate('confirmnewsletter.html', {
      #'title': 'Confirm Newsletter',
      'header_title': 'Confirm Newsletter | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'wine, wines, miracle one, miracle one wine, pinot noir, buy wine, purchase wine, red wine, chardonnay, carneros, napa valley, home, homepage',
      'header_description':'Welcome to Miracle One Wines.  We are the producers of Miracle One Carneros Chardonnay and Miracle One Carneros-Napa Valley Pinot Noir.',
      })


class SuccessNewsletterHandler(BaseRequestHandler):
  """
  Generates the Success Newsletter page. This is after you sign up for the page.

  """
  def get(self):
    logging.info('Visiting the Success Newsletter page')
    self.generate('successnewsletter.html', {
      #'title': 'Success Newsletter',
      'header_title': 'Success Newsletter | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'wine, wines, miracle one, miracle one wine, pinot noir, buy wine, purchase wine, red wine, chardonnay, carneros, napa valley, home, homepage',
      'header_description':'Welcome to Miracle One Wines.  We are the producers of Miracle One Carneros Chardonnay and Miracle One Carneros-Napa Valley Pinot Noir.',
      })


class SuccessInviteHandler(BaseRequestHandler):
  """
  Generates the Success Invite page.

  """
  def get(self):
    logging.info('Visiting the Success invite page')
    self.generate('successinvite.html', {
      #'title': 'Success Invite',
      'header_title': 'Invite Success | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'wine, wines, miracle one, miracle one wine, pinot noir, buy wine, purchase wine, red wine, chardonnay, carneros, napa valley, home, homepage',
      'header_description':'Welcome to Miracle One Wines.  We are the producers of Miracle One Carneros Chardonnay and Miracle One Carneros-Napa Valley Pinot Noir.',
      })


class OptOutEmailHandler(BaseRequestHandler):
  """
  Generates the Opt Out page.

  """
  def get(self):
    logging.info('Visiting the Opt Out page')
    self.generate('optout.html', {
      #'title': 'Opt Out',
      'header_title': 'Home | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'wine, wines, miracle one, miracle one wine, pinot noir, buy wine, purchase wine, red wine, chardonnay, carneros, napa valley, home, homepage',
      'header_description':'Welcome to Miracle One Wines.  We are the producers of Miracle One Carneros Chardonnay and Miracle One Carneros-Napa Valley Pinot Noir.',
      })


class SoldOutPageHandler(BaseRequestHandler):
  """
  Generates the sold out page.

  """
  def get(self):
    logging.info('Visiting the sold out page')
    self.generate('soldout.html', {
      #'title': 'Sold Out',
      'header_title': 'Home | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'wine, wines, miracle one, miracle one wine, pinot noir, buy wine, purchase wine, red wine, chardonnay, carneros, napa valley, home, homepage',
      'header_description':'Welcome to Miracle One Wines.  We are the producers of Miracle One Carneros Chardonnay and Miracle One Carneros-Napa Valley Pinot Noir.',
      })

class NewsLetterProvideValidEmailHandler(BaseRequestHandler):
  """
    Generates the page instructing users to provide valid email addresses
    for newsletter page.
  """
  def get(self):
    logging.info('Visiting the provide valid email address for the newsletter.')
    self.generate('newslettervalidemail.html', {
      #'title': 'Provide Valid Email for Newsletter',
      'header_title': 'Home | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'wine, wines, miracle one, miracle one wine, pinot noir, buy wine, purchase wine, red wine, chardonnay, carneros, napa valley, home, homepage',
      'header_description':'Welcome to Miracle One Wines.  We are the producers of Miracle One Carneros Chardonnay and Miracle One Carneros-Napa Valley Pinot Noir.',
      })


class FriendProvideValidInfoHandler(BaseRequestHandler):
  """
    Generates the page instructing users to provide valid information if they     would like to email a friend.
  """
  def get(self):
    logging.info('Visiting the provide valid info to email a friend page.')
    self.generate('friendvalidemail.html', {
      #'title': 'Provide Valid Info To email a friend',
      'header_title': 'Home | Miracle One Chardonnay & Pinot Noir',
      'header_keywords': 'wine, wines, miracle one, miracle one wine, pinot noir, buy wine, purchase wine, red wine, chardonnay, carneros, napa valley, home, homepage',
      'header_description':'Welcome to Miracle One Wines.  We are the producers of Miracle One Carneros Chardonnay and Miracle One Carneros-Napa Valley Pinot Noir.',
      })


class SiteMapHandler(BaseRequestHandler):
  """
    Generates the sitemap.
  """
  def get(self):
    logging.info('Displaying the sitemap')
    self.generate('miracleonewinessitemap.xml', {
    })


class RobotsHandler(BaseRequestHandler):
  """
    Generates the robots.txt file.
  """
  def get(self):
    logging.info('Displaying the robots.txt file')
    self.generate('robots.txt', {
    })
