#!/usr/bin/python

print '=========================================='
print '== TimezoneSimplifier Reddit bot V. 2.0 =='
print '=========================================='
print
print 'Importing...'
import requests # for error handling
from ConfigParser import SafeConfigParser # to parse username and password from file
import praw # for reddit API
import urllib2 # for website access
import re # for regular Expressions
import pytz, datetime # for caluclations between timezones
import time # to sleep the program
import collections # for ordered dict (used in generating the output)
import sys # for reading command line arguments
import logging 
print '  Importing done.'

#Set logging
logging.basicConfig(filename='timezonesimplifier_log.txt', level=logging.WARNING, format='%(asctime)s %(message)s')

#login
parser = SafeConfigParser()
parser.read('/config/config_secret.config')
r = praw.Reddit("timezonesimplifier/2.0 by nijin22")
r.set_oauth_app_info(client_id=parser.get('login', 'client_id'), client_secret=parser.get('login', 'client_secret'), redirect_uri=parser.get('login', 'redirect_uri') 'authorize_callback')

url = r.get_authorize_url('timezonesimplifier/2.0 by nijin22 login', 'creddits edit flair history identity modconfig modcontributors modflair modlog modothers modposts modself modwiki mysubreddits privatemessages read report save submit subscribe vote wikiedit wikiread', True)
import webbrowser
webbrowser.open(url)