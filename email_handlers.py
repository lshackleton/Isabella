#!/usr/bin/env python
"""
Handlers for maintaining our email database.

We use the webapp.py WSGI framework to handle CGI requests, using the
wsgiref module to wrap the webapp.py WSGI application in a CGI-compatible
container. See webapp.py for documentation on RequestHandlers and the URL
mapping at the bottom of this module.  

"""

import logging

from google.appengine.ext import db

from django.utils import simplejson
from django.http import HttpResponse

# Data models
import models

# Simple web handlers
import webpagehandlers


class AddToEmailListActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Processes an email list addition request.

  """
  def post(self):
    logging.info('Adding new email address')
    email = self.request.get('youremail')
    logging.info('email == %s' % email)
    if self.request.get('yourname'):
      name = self.request.get('yourname')
      logging.info('name == %s' % name)
    else: 
      name = None
    if (not email or not '@' in email):
      logging.info('email blank')
      logging.info('Sending back to contact page with alert.')
      self.redirect('/') #TODO: replace with new page / alert
      return
    query = models.Email.all()
    query.filter('email =', db.Email(self.request.get('youremail')))
    entry = query.get()
    logging.info('entry = %s ' % str(entry))
    if entry:
      logging.info('email already exists in email DB.')
      self.redirect('/emailadded') #TODO: replace with new page / alert
    else:
      if '@' in email:
        new_email = models.Email()
        new_email.email = db.Email(email)
        new_email.verified = bool(False)
        new_email.name = name
        new_email.put()

        email_name = new_email.name
        if email_name == None:
          email_name = ''
        else:
          email_name = ' ' + email_name
#        mail.send_mail(sender="info@.com", #TODO: Clean up this email
#                      to=email,
#                      bcc="alerts@.com",
#                      subject="Miracle One Wines: Confirm Email Address",
#                      body="""
#Hello%s,
#
#In order to confirm your Miracle One newsletter subscription, please click the link below:
#
#http://www..com/confirmemailaddress.do?id=%s
#
#Thanks for signing up for the Miracle One Newsletter and we look forward to keeping in touch with you!
#
#Cheers,
#
#""" % (email_name, new_email.key())
#                      )
        self.redirect('/successnewsletter') #TODO: replace with new page
      else:
        logging.info('Sending back with alert.')
#        self.generate('contact.html', { #TODO: replace with new page
#          'alert': 'Please insert a valid email address.',
#          })


class ConfirmEmailAddressActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Processes an confirm Newsletter request.

  """
  def get(self):
    logging.info('-- Verifying email address')

    entry = models.Email.get(self.request.get('id'))
    logging.info('id == %s' % self.request.get('id'))
    if not entry:
      logging.info('Sending back with alert.')
#      self.generate('contact.html', { #TODO: Replace with the proper page.
#        'alert': 'Please try clicking the link in the confirmation email again. Or send us a support request at lane@miracleonewines.com',  #TODO: Replace with a proper message
#        })
    else:
      entry.verified = bool(True)
      logging.info('entry.verified updated to bool(True)')
      entry.put()
      self.redirect('/confirmnewsletter') #TODO: Replace with the proper page.


class OptOutEmailActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Processes an opt out.

  """
  def post(self):
    logging.info('Opting out an email address')
    logging.info('email = %s ' % self.request.get('youremail'))

    query = models.Email.all()
    query.filter('email =', db.Email(self.request.get('youremail')))
    entry = query.get()
    logging.info('entry = %s ' % str(entry))
    if entry:
      entry.verified = bool(False)
      logging.info('entry.verified updated to bool(False)')
      entry.put()

    self.redirect('/optout') #TODO: Replace with the proper page. And replace so that this is an alert instead.

