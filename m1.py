#!/usr/bin/env python
"""
Miracle One Wines
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

# Data models
import models

# Simple web handlers
import webpagehandlers

# Admin page handlers
import adminpagehandlers

# m1_util -- All the helper functions
import m1_util

## Set logging level.
logging.getLogger().setLevel(logging.INFO)


class EmailListActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Processes an email list addition request.

  """
  def post(self):
    logging.info('EmailListHandler -- adding new email address')
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
      self.generate('contact.html', {
        #'title': 'Contact',
        'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
        'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
        'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
        'alert': 'Please insert a valid email address',
        })
      return
    query = models.Email.all()
    query.filter('email =', db.Email(self.request.get('youremail')))
    entry = query.get()
    logging.info('entry = %s ' % str(entry))
    if entry:
      logging.info('email already exists in email DB.')
      self.redirect('/successnewsletter')
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
        mail.send_mail(sender="info@miracleonewines.com",
                      to=email,
                      bcc="alerts@miracleonewines.com",
                      subject="Miracle One Wines: Confirm Email Address",
                      body="""
Hello%s,

In order to confirm your Miracle One newsletter subscription, please click the link below:

http://www.miracleonewines.com/confirmnewsletter.do?id=%s

Thanks for signing up for the Miracle One Newsletter and we look forward to keeping in touch with you!

Cheers,
Ryan and Lane
""" % (email_name, new_email.key())
                      )
        self.redirect('/successnewsletter')
      else:
        logging.info('Sending back to contact page with alert.')
        self.generate('contact.html', {
          #'title': 'Contact',
          'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
          'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
          'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
          'alert': 'Please insert a valid email address.',
          })


class ConfirmNewsletterActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Processes an confirm Newsletter request.

  """
  def get(self):
    logging.info('ConfirmNewsletterHandler -- Verifying email address')

    entry = models.Email.get(self.request.get('id'))
    logging.info('id == %s' % self.request.get('id'))
    if not entry:
      logging.info('Sending back to contact page with alert.')
      self.generate('contact.html', {
        #'title': 'Contact',
        'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
        'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
        'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
        'alert': 'Please try clicking the link in the confirmation email again. Or send us a support request at lane@miracleonewines.com',
        })
    else:
      entry.verified = bool(True)
      logging.info('entry.verified updated to bool(True)')
      entry.put()
      self.redirect('/confirmnewsletter')


class OptOutEmailActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Processes an opt out.

  """
  def post(self):
    logging.info('OptOutEmailActionHandler -- Opting out an email address')
    logging.info('email = %s ' % self.request.get('youremail'))

    query = models.Email.all()
    query.filter('email =', db.Email(self.request.get('youremail')))
    entry = query.get()
    logging.info('entry = %s ' % str(entry))
    if entry:
      entry.verified = bool(False)
      logging.info('entry.verified updated to bool(False)')
      entry.put()
      
    self.redirect('/optout')


class PurchaseWineActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Actually purchasing the wine and sending an order email to Lane/Ryan.
  """
  def post(self):
    logging.info('Verifying user age before allowing wine purchase. VerifyAgeActionHandler.')
    day = int(self.request.get('day'))
    month = int(self.request.get('month'))
    year = int(self.request.get('year'))
    wine_2007_chardonnay = int(self.request.get('2007_chardonnay'))
    wine_2007_pinot = int(self.request.get('2007_pinot'))
    firstname = self.request.get('firstname')
    lastname = self.request.get('lastname')
    shipping_type = self.request.get('shipping_type')
    shippingaddress = self.request.get('shippingaddress')
    state =  self.request.get('state')
    shippingzip = self.request.get('shippingzip')
    phone = self.request.get('phone')
    email = self.request.get('email')
    cardtype = self.request.get('cardtype')
    nameoncard = self.request.get('nameoncard')
    cardnumber = self.request.get('cardnumber')
    cvccode = self.request.get('cvccode')

    required_items = [day, month, year, wine_2007_chardonnay, wine_2007_pinot, 
                      firstname, lastname, shippingaddress, state, shippingzip, 
                      phone, email, cardtype, nameoncard, cardnumber, cvccode, 
                      shipping_type
                     ]
    
    for item in required_items:
      if not item:
        self.redirect('/purchasewine')
        return


    age = m1_util.VerifyAtLeast21(month=month, day=day, year=year)
    if age:
      tax_query = models.TaxTable.all()
      tax_query.filter('state =', state)
      tax_result = tax_query.get()
      if tax_result == None:
        self.redirect('/purchasewine')
        return
      else:
        tax_rate =  tax_result.tax_rate

      total_wine = wine_2007_chardonnay + wine_2007_pinot
      cases = total_wine / 12
      singles = total_wine % 12

      shipping = 0.00
      
      if cases > 0:
        cases_shipping_query = models.ShippingTable.all()
        cases_shipping_query.filter('state =', state)
        cases_shipping_query.filter('number_bottles =', 12)
        cases_shipping_result = cases_shipping_query.get()
        if cases_shipping_result == None:
          self.redirect('/purchasewine')
          return
        else:
          if shipping_type == 'express':
            shipping_cost = cases_shipping_result.express_cost
          else:
            shipping_cost = cases_shipping_result.standard_cost
            
        shipping =+ cases * shipping_cost
        
      if singles > 0:
        singles_shipping_query = models.ShippingTable.all()
        singles_shipping_query.filter('state =', state)
        singles_shipping_query.filter('number_bottles =', singles)
        singles_shipping_result = singles_shipping_query.get()
        if singles_shipping_result == None:
          self.redirect('/purchasewine')
          return
        else:
          if shipping_type == 'express':
            shipping_cost = singles_shipping_result.express_cost
          else:
            shipping_cost = singles_shipping_result.standard_cost

        shipping =+ singles * shipping_cost

      pre_tax = total_wine * 25
      tax = pre_tax * tax_rate
      pre_tax_2007_chardonnay = wine_2007_chardonnay * 25
      pre_tax_2007_pinot = wine_2007_pinot * 25
      total_cost = pre_tax + tax + shipping
      new_web_order = models.OrderDetails()
      new_web_order.age = age
      new_web_order.month=month
      new_web_order.year=year
      new_web_order.day=day
      new_web_order.wine_2007_chardonnay=wine_2007_chardonnay
      new_web_order.wine_2007_pinot=wine_2007_pinot
      new_web_order.firstname=firstname
      new_web_order.lastname=lastname
      new_web_order.shipping_type=shipping_type
      new_web_order.shippingaddress=shippingaddress
      new_web_order.state=state
      new_web_order.shippingzip=shippingzip
      new_web_order.phone=phone
      new_web_order.email=email
      new_web_order.cardtype=cardtype
      new_web_order.nameoncard=nameoncard
      new_web_order.cardnumber=cardnumber
      new_web_order.cvccode=cvccode
      new_web_order.total_wine = total_wine
      new_web_order.pre_tax=pre_tax
      new_web_order.tax=tax
      new_web_order.pre_tax_2007_chardonnay=pre_tax_2007_chardonnay
      new_web_order.pre_tax_2007_pinot=pre_tax_2007_pinot
      new_web_order.total_cost=total_cost
      new_web_order.put()

      subject = 'New M1 Order. Get ready to ship!'
      body = """Here are the order details: 
             age: %d
             month: %d
             year: %d
             day: %d
             2007_chardonnay: %d
             2007_pinot: %d
             firstname: %s
             lastname: %s
             shippingaddress: %s
             state: %s
             shippingzip: %s
             phone: %s
             email: %s
             cardtype: %s
             nameoncard: %s
             cardnumber: %s
             cvccode: %s
             total_wine: %s
             pre_tax: %s
             tax: %s
             total_cost: %s
             shipping_type: %s
             """% (age, month, year, day, wine_2007_chardonnay, wine_2007_pinot,
                   firstname, lastname, shippingaddress, state, shippingzip,  
                   phone, email, cardtype, nameoncard, cardnumber, cvccode, 
                   str(total_wine), str(pre_tax), str(tax), str(total_cost),  
                   shipping_type
                  )               
      mail.send_mail_to_admins(sender=mail_admin,
                               subject=subject,
                               body=body)

      self.generate('successwine.html', {
        #'title': '',
        'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
        'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
        'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
        '2007_chardonnay_order': wine_2007_chardonnay,
        '2007_pinot_order': wine_2007_pinot,
        'total_cost': total_cost,       
                                        }
                   )
    else:
      self.redirect('/purchasewine')


class ConsiderPurchaseActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Considering purchasing wine -- return so they can confirm.
  """
  def post(self):
    logging.info('Verifying user age before allowing wine purchase. VerifyAgeActionHandler.')
    day = int(self.request.get('day'))
    month = int(self.request.get('month'))
    year = int(self.request.get('year'))
    wine_2007_chardonnay = int(self.request.get('2007_chardonnay'))
    wine_2007_pinot = int(self.request.get('2007_pinot'))
    firstname = self.request.get('firstname')
    lastname = self.request.get('lastname')
    shipping_type = self.request.get('shipping_type')
    shippingaddress = self.request.get('shippingaddress')
    state =  self.request.get('state')
    shippingzip = self.request.get('shippingzip')
    phone = self.request.get('phone')
    email = self.request.get('email')

    required_items = [day, month, year, wine_2007_chardonnay, wine_2007_pinot, 
                      firstname, lastname, shippingaddress, state, shippingzip, 
                      phone, email, shipping_type
                     ]

    for item in required_items:
      if not item:
        self.redirect('/purchasewine')
        return


    age = m1_util.VerifyAtLeast21(month=month, day=day, year=year)
    if age:
      tax_query = models.TaxTable.all()
      tax_query.filter('state =', state)
      tax_result = tax_query.get()
      if tax_result == None:
        self.redirect('/purchasewine')
        return
      else:
        tax_rate =  tax_result.tax_rate

      total_wine = wine_2007_chardonnay + wine_2007_pinot
      cases = total_wine / 12
      singles = total_wine % 12

      shipping = 0.00

      if cases > 0:
        cases_shipping_query = models.ShippingTable.all()
        cases_shipping_query.filter('state =', state)
        cases_shipping_query.filter('number_bottles =', 12)
        cases_shipping_result = cases_shipping_query.get()
        if cases_shipping_result == None:
          self.redirect('/purchasewine')
          return
        else:
          if shipping_type == 'express':
            shipping_cost = cases_shipping_result.express_cost
          else:
            shipping_cost = cases_shipping_result.standard_cost

        shipping =+ cases * shipping_cost

      if singles > 0:
        singles_shipping_query = models.ShippingTable.all()
        singles_shipping_query.filter('state =', state)
        singles_shipping_query.filter('number_bottles =', singles)
        singles_shipping_result = singles_shipping_query.get()
        if singles_shipping_result == None:
          self.redirect('/purchasewine')
          return
        else:
          if shipping_type == 'express':
            shipping_cost = singles_shipping_result.express_cost
          else:
            shipping_cost = singles_shipping_result.standard_cost

        shipping =+ shipping_cost

      pre_tax = total_wine * 25
      tax = pre_tax * tax_rate
      pre_tax_2007_chardonnay = wine_2007_chardonnay * 25
      pre_tax_2007_pinot = wine_2007_pinot * 25
      total_cost = pre_tax + tax + shipping

      self.generate('successwine.html', {
        #'title': '',
        'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
        'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
        'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
        '2007_chardonnay_order': wine_2007_chardonnay,
        '2007_pinot_order': wine_2007_pinot,
        'taxes': tax,
        'shipping': shipping,
        'total_cost': total_cost,       
                                        }
                   )
    else:
      self.redirect('/purchasewine')



class EmailAFriendActionHandler(webpagehandlers.BaseRequestHandler):
  """
  Processes an email a friend request.

  """
  def post(self):
    logging.info('EmailAFriendHandler -- Emailing a new friend.')

    youremail = self.request.get('youremail')
    logging.info('youremail == %s' % youremail)
    if (not youremail or not '@' in youremail):
      logging.info('youremail blank')
      logging.info('Sending back to contact page with alert.')
      self.generate('emailafriend.html', {
        #'title': 'Email A Friend',
        'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
        'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
        'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
        'alert': 'Please insert a valid email address.',
        })
      return
    yourname = self.request.get('yourname')
    logging.info('yourname == %s' % yourname)
    if not yourname:
      logging.info('yourname blank')
      logging.info('Sending back to contact page with alert.')
      self.generate('emailafriend.html', {
        #'title': 'Email A Friend',
        'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
        'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
        'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
        'alert': 'Please insert your name for sending a message to a friend.',
        })
      return
    friendemail = self.request.get('friendemail')
    logging.info('friendemail == %s' % friendemail)
    if (not friendemail or not '@' in friendemail):
      logging.info('friendemail blank')
      logging.info('Sending back to contact page with alert.')
      self.generate('emailafriend.html', {
        #'title': 'Email A Friend',
        'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
        'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
        'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
        'alert': 'Please insert a valid friend email address.',
        })
      return
    friendname = self.request.get('friendname')
    logging.info('friendname == %s' % friendname)
    if not friendname:
      logging.info('friendname blank')
      logging.info('Sending back to contact page with alert.')
      self.generate('emailafriend.html', {
        #'title': 'Email A Friend',
        'header_title': 'Contact | Miracle One Chardonnay & Pinot Noir',
        'header_keywords': 'miracle one, miracle one wines, contact miracle one, contact, email, email address, miracle one phone number',
        'header_description':'Whether it is sharing a photo, a story or simply a wine your excited about - we would love to hear from you. Also, you can get updates and hear about discounts on our wine by subscribing to our newsletter.',
        'alert': 'Please insert a valid friend name before sending.',
        })
      return
    new_friend = models.Friend()
    new_friend.youremail = db.Email(youremail)
    new_friend.yourname = yourname
    new_friend.friendname = friendname
    new_friend.friendemail = db.Email(friendemail)
    new_friend.put()

    mail.send_mail(sender="info@miracleonewines.com",
                  to=friendemail,
                  bcc="alerts@miracleonewines.com",
                  subject="Miracle One Wines",
                  body="""
Hi %s,

Check out a new wine I found called Miracle One - www.miracleonewines.com

Cheers,
 %s
 """ % (friendname, yourname)
                  )
    self.redirect('/successinvite')  


class PaypalIPNHandler(webpagehandlers.BaseRequestHandler):
  """
  Classes for accepting PayPal's Instant Payment Notification messages.
  See: https://www.paypal.com/ipn

  "data" looks something like this:

  {
      'business': 'your-business@example.com',
      'charset': 'windows-1252',
      'cmd': '_notify-validate',
      'first_name': 'S',
      'last_name': 'Willison',
      'mc_currency': 'GBP',
      'mc_fee': '0.01',
      'mc_gross': '0.01',
      'notify_version': '2.4',
      'payer_business_name': 'Example Ltd',
      'payer_email': 'payer@example.com',
      'payer_id': '5YKXXXXXX6',
      'payer_status': 'verified',
      'payment_date': '11:45:00 Aug 13, 2008 PDT',
      'payment_fee': '',
      'payment_gross': '',
      'payment_status': 'Completed',
      'payment_type': 'instant',
      'receiver_email': 'your-email@example.com',
      'receiver_id': 'CXZXXXXXQ',
      'residence_country': 'GB',
      'txn_id': '79F58253T2487374D',
      'txn_type': 'send_money',
      'verify_sign': 'AOH.JxXLRThnyE4toeuh-.oeurch23.QyBY-O1N'
  }
  """
  verify_url = "https://www.paypal.com/cgi-bin/webscr"

  def get(self):
    logging.info('Calling the PaypalIPNHandler via get. Bad.')
    self.redirect("/home")

  def post(self):
    """ Post method to accept PayPalData data."""
    logging.info('Calling the PaypalIPNHandler via post. Good.')
    logging.info('print dir(self.request.POST.items()): %s' % dir(self.request.POST.items()))
    logging.info('print self.request.POST.items(): %s' % self.request.POST.items())

    data = dict(self.request.POST.items())
    logging.info('data == %s' % str(data))
    # We need to post that BACK to PayPal to confirm it
    if self.verify(data):
        r = self.process(data)
    else:
        r = self.process_invalid(data)

  def process(self, data):
    logging.info('Verfication successful. process(data)')
    #Store the data in the db
    newpaypalentry = models.PayPalData()
    newpaypalentry.dataBlob = str(data)
    newpaypalentry.verification = str('process')
    newpaypalentry.customerOrderId = str(data.txn_id)
    newpaypalentry.customerOrderDate = str(data.payment_date)    
    newpaypalentry.SoldToFirstName = str(data.first_name)
    newpaypalentry.SoldToLastName = str(data.last_name)
    newpaypalentry.AddressLine1 = str(data.address_street)
    newpaypalentry.AddressLine2 = str('')
    newpaypalentry.SoldToCity = str(data.address_city)
    newpaypalentry.SoldToState = str(data.address_state)
    newpaypalentry.SoldToZip = str(data.address_zip)
    newpaypalentry.SoldToPhone = str(data.contact_phone)
    newpaypalentry.ConsumerShippingCharge = str(data.mc_shipping)
    newpaypalentry.SalesTaxAmount = str(data.tax)
    newpaypalentry.TotalChargeToConsumer = str(data.mc_gross)
    newpaypalentry.CustomerProductId = str(data.item_number1)
    newpaypalentry.Quantity = str(data.quantity)
    newpaypalentry.Price = str(data.mc_gross)
    newpaypalentry.Subtotal = str(data.mc_gross) 
    newpaypalentry.put()
    #format the data as a csv

    csvdata = m1_util.CreateCSVOrderFile(customerOrderId=newpaypalentry.customerOrderId, customerOrderDate=newpaypalentry.customerOrderDate, SoldToFirstName=newpaypalentry.SoldToFirstName, SoldToLastName=newpaypalentry.SoldToLastName, AddressLine1=newpaypalentry.AddressLine1, AddressLine2=newpaypalentry.AddressLine2, SoldToCity=newpaypalentry.SoldToCity, SoldToState=newpaypalentry.SoldToState, SoldToZip=newpaypalentry.SoldToZip, SoldToPhone=newpaypalentry.SoldToPhone, ConsumerShippingCharge=newpaypalentry.ConsumerShippingCharge, SalesTaxAmount=newpaypalentry.SalesTaxAmount, TotalChargeToConsumer=newpaypalentry.TotalChargeToConsumer, CustomerProductId=newpaypalentry.CustomerProductId, Quantity=newpaypalentry.Quantity, Price=newpaypalentry.Price, Subtotal=newpaypalentry.Subtotal)
    csvfilename = 'Miracleonewines_%s_%s.csv' % ( datetime.datetime.now().strftime("%m%d%Y"), newpaypalentry.customerOrderId)
    #email the data to the shipper
    mail.send_mail(sender="info@miracleonewines.com",
                    to="wferrell@gmail.com",
                    cc="alerts@miracleonewines.com",
                    subject="Miracleonewines.com Order Attachment",
                    body="""Attached is the latest Miracleonewines.com order. Thanks!""",
                    attachments=[(csvfilename, csvdata)]
                  )
    self.redirect("/home")

  def process_invalid(self, data):
    FAIL_ALERT_EMAIL = """Dear Miracle One Wines, There has been an invalid Paypal payment. I recommend visiting http://www.paypal.com and investigating. Here is the data: %s."""
    logging.info('Verfication failed. process_invalid(data)')
    #Store the data in the db
    newpaypalentry = PayPalData()
    newpaypalentry.dataBlob = str(data)
    newpaypalentry.verification = str('process_invalid')
    newpaypalentry.put()
    
    #email the data to lane/ryan
    message = mail.EmailMessage(sender="info@miracleonewines.com",
                                subject="FAIL - Paypal IPN verification           alert")
    message.to = "alerts@miracleonewines.com"
    message.body = self.FAIL_ALERT_EMAIL % data
    message.send()


  def do_post(self, url, args):
    return urlfetch.fetch(
      url = url,
        method = urlfetch.POST,
        payload = urllib.urlencode(args)
    ).content

  def verify(self, data):
    bad_item_numbers = (1001, 1002)
    args = {
        'cmd': '_notify-validate',
    }
    for k, v in data.items():
        args[k] = v.encode('utf-8')
    if not data.item_number1 in bad_item_numbers:
      logging.info('Verfication process -- NOT a vest order.')
      return self.do_post(self.verify_url, args) == 'VERIFIED'
    else:
      logging.info('Verfication process -- IS a vest order.')
      #email the data to alerts
      message = mail.EmailMessage(sender="lane@miracleonewines.com",
                                  subject="Vest(s) Ordered -- Go do something")
      message.to = "alerts@miracleonewines.com"
      message.body = 'A vest has been ordered. Go ship this order.'
      message.send()
      return self.do_post(self.verify_url, args) == 'VERIFIED'


# Map URLs to our RequestHandler classes above
_M1_URLS = [
# after each URL map we list the html template that is displayed
   ('/', webpagehandlers.HomePageHandler), #home.html
   ('/home', webpagehandlers.HomePageHandler), #home.html
   ('/wine', webpagehandlers.WinePageHandler), #wine.html
   ('/enviro', webpagehandlers.EnviroPageHandler), #enviro.html
   ('/film', webpagehandlers.FilmPageHandler), #film.html
   ('/press', webpagehandlers.PressPageHandler), #press.html
   ('/contact', webpagehandlers.ContactPageHandler), #contact.html
   ('/about', webpagehandlers.AboutPageHandler), #about.html
##   ('/purchasewine', webpagehandlers.PurchaseWinePageHandler), #purchasewine.html
##   ('/purchasewineconfirm', webpagehandlers.PurchaseWineConfirmPageHandler), #purchasewineconfirm.html
   ('/purchasegear', webpagehandlers.PurchaseGearPageHandler), #purchasegear.html
   ('/successwine', webpagehandlers.SuccessWinePageHandler), #successwine.html
   ('/successgear', webpagehandlers.SuccessGearPageHandler), #successgear.html
   ('/comingsoon', webpagehandlers.ComingSoonPageHandler), #comingsoon.html
   ('/soldout', webpagehandlers.SoldOutPageHandler), #soldout.html
   ('/gearsoldout', webpagehandlers.GearSoldOutPageHandler), #gearsoldout.html
   ('/4587621379', PaypalIPNHandler), # PayPal IPN URL
   ('/newslettersubmit.do', EmailListActionHandler),
   ('/newslettervalidemail', webpagehandlers.NewsLetterProvideValidEmailHandler),
   ('/friendinvite.do', EmailAFriendActionHandler),
   ('/friendvalidemail', webpagehandlers.FriendProvideValidInfoHandler),
   ('/optout', webpagehandlers.OptOutEmailHandler),   
   ('/successnewsletter', webpagehandlers.SuccessNewsletterHandler),   
   ('/successinvite', webpagehandlers.SuccessInviteHandler),   
   ('/confirmnewsletter.do', ConfirmNewsletterActionHandler),   
   ('/confirmnewsletter', webpagehandlers.ConfirmNewsletterHandler),
   ('/sitemap', webpagehandlers.SiteMapHandler),
   ('/sitemap.xml', webpagehandlers.SiteMapHandler),
   ('/robots.txt', webpagehandlers.RobotsHandler),
   ('/optout.do', OptOutEmailActionHandler),
##  ('/purchasewine.do', PurchaseWineActionHandler),
##  ('/considerpurchase.do', ConsiderPurchaseActionHandler),   
   ('/emailafriend', webpagehandlers.EmailAFriendHandler),
   ('/.*$', webpagehandlers.HomePageHandler), #home.html
]


def main():
  application = webapp.WSGIApplication(_M1_URLS, debug=webpagehandlers._DEBUG)
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
