#!/usr/bin/python

print '==================================='
print '== TimezoneSimplifier Reddit bot =='
print '==================================='
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
print '  Finished.'

logging.basicConfig(filename='timezonesimplifier_log.txt', level=logging.WARNING, format='%(asctime)s %(message)s')

preComment = '#####&#009;\n\n####&#009;\n\n######&#009;\n'; #required for subreddit specific CSS to enable "hover to view"
signature = '\n\n---\n\nInfo: This message was submitted by a bot.\n\nFeedback, Problems and Questions: /r/TimezoneSimplifier\n\nComment unhelpful? Downvote it! Comments with less than 0 points will be deleted and won\'t block space in this thread.'
subreddit_names = ['TimezoneSimplifier', 'test', 'twitch', 'leagueoflegends', 'GlobalOffensive', 'tf2', 'worldnews', 'battlefield_4', 'dota2', 'starcraft', 'warthunder', 'heroesofthestorm', 'codcompetitive', 'titanfall', 'mcpublic', 'bravenewbies', 'ogn', 'littlewargame', 'anarchyonline', 'RunnerHub', 'watchamovienow'] #The Subreddits, the bot visits
# List of bots: http://www.reddit.com/r/botwatch/comments/1wg6f6/bot_list_i_built_a_bot_to_find_other_bots_so_far/cf1nu8p
ignored_users = ['TweetPoster', 'TimezoneSimplifier', 'Website_Mirror_Bot', 'Fedora-Tip-Bot', 'annoying_yes_bot', 'Wiki_Bot', 'Relevant_News_Bot', 'fastnewsbot', 'RemindMeBot', 'UltimatesTruth']
ignore_words = ['PCPartPicker', 'GMT+', 'GMT-', 'UTC+', 'UTC-', 'GMT +', 'GMT -', 'UTC +', 'UTC -', 'no tzs', 'no bot answer']
ignore_comments_in = ['games'] # Watch for correct cases (upper+lower)
timezones = {"gmt" : "UTC", "utc" : "UTC", "mez" : "Europe/Berlin", "cet" : "Europe/Berlin", "cest" : "Europe/Berlin", "met" : "Europe/Berlin", "eet" : "Europe/Kiev", "msk" : "Europe/Moscow", "ist" : "Asia/Kolkata", "wet" : "Europe/London", "eastern" : "America/New_York", "edt" : "America/New_York", "est" : "America/New_York", "pdt" : "America/Los_Angeles", "pacific":"America/Los_Angeles", "pst" : "America/Los_Angeles", "mdt" : "America/Denver", "cdt" : "America/Chicago", "central" : "America/Chicago", "aest" : "Australia/Sydney", "brt" : "America/Sao_Paulo", "brst" : "America/Sao_Paulo", "kst" : "Asia/Seoul", "wib" : "Asia/Jakarta", "cst" : "America/Chicago", "sgt" : "Asia/Shanghai", "ulat" : "Asia/Shanghai", "krat" : "Asia/Shanghai", "nzst" : "Pacific/Auckland", "nzdt" : "Pacific/Auckland", "eat" : "Africa/Dar_es_Salaam", "wat":"Africa/Kinshasa", "nst" : "America/St_Johns", "ndt" : "America/St_Johns", "akst" : "America/Anchorage", "akdt" : "America/Anchorage", "mst" : "America/Phoenix", "hast" : "Pacific/Honolulu", "hst" : "Pacific/Honolulu"}

#Construct a regEx for all supported Timezones:
timezones_regex = "("
addPipe = False
for key in timezones:
    if addPipe:
        timezones_regex += "|"
    timezones_regex += key
    addPipe = True
timezones_regex += ")"
regEx = re.compile(r'([0-9]?[0-9]):([0-5][0-9])(:[0-5][0-9])?( PM| AM)? ' + timezones_regex, re.I|re.S)

fetch_limit_comment = 150
fetch_limit_posts = 25

logging.info('Connecting and logging in')
r = praw.Reddit("timezonesimplifier/1.2 by nijin22")
parser = SafeConfigParser()
parser.read('login.config')
#logging.info('  as ' + parser.get('login', 'username') + ' with the password ' + parser.get('login', 'password'))
logging.info('  as ' + parser.get('login', 'username') + ' with the password ' + "XXXXXXXXXXXXX")
r.login(parser.get('login', 'username'),parser.get('login', 'password'))
logging.info('  Finished.')


logging.info('Loading posts-ids, we do not need to respond to...')
file = open("done_Posts.txt") #Loading post we don't need to reply into list
done_Posts = file.readlines()
done_Posts = [item.strip() for item in done_Posts]
map(str.strip, done_Posts)
file.close()
logging.info('  Finished.')

file = open("done_Posts.txt", "a")

def checkSelfOcomment(selfOcomment):
    #the content of a selfpost / submission is called "body" or "selftext"
    if hasattr(selfOcomment, 'body'):
        content = selfOcomment.body
    elif hasattr(selfOcomment, 'selftext'):
        content = selfOcomment.selftext
    else:
        logging.warning('ERROR: selfOcomment does not have body or selftext')
        raise SystemError
    
    if not selfOcomment.author: #Fix for reddit problem with deleted user posts: http://www.reddit.com/r/redditdev/comments/1630jj/praw_is_returning_postauthorname_errors/c7s8zx9
        username = '[deleted]'
    else:
        username = selfOcomment.author.name
    if (selfOcomment.id not in done_Posts) and (username not in ignored_users) and ('_bot' not in username.lower()):
        hour = 0 #Default values
        minute = 0
        second = 0
        timezone_string = "UTC"
        
        
        matchObj = regEx.search(content)
        if (matchObj) and not any(word.lower() in content.lower() for word in ignore_words): # Found a regEx? AND does the content includes one of the "ignore post if this is posted" words?
            logging.info('  Found useable selfOcomment by ' + selfOcomment.author.name + ' with the ID: ' + selfOcomment.id)
            hour = int(matchObj.group(1))
            if str(matchObj.group(4)).lower() == " pm":
                hour = hour + 12
            minute = int(matchObj.group(2))
            if matchObj.group(3): #Seconds are optional
                second = int(matchObj.group(3)[1:])# [1:] means that we strip the first character (a ":")
            timezone_abbrev = matchObj.group(5).lower()
            timezone_string = timezones[timezone_abbrev]
            replyto(hour, minute, second, timezone_string, replyable = selfOcomment)
def replyto(hour, minute, second, timezone_string, replyable):
    #Handling differences between self posts and comments
    if replyable.permalink:
        link = replyable.permalink
    elif replyable.short_link:
        link = replyable.short_link
    else:
        link = 'http://example.org' # This is just for error handling. it should not be used actuall.y
    
    
    invaliddata = False
    #Validation:
    if hour > 23 or hour < 0:
        invaliddata = True
        hour = 12
    if minute > 60 or minute < 0:
        invaliddata = True
        minute = 30
    if second > 60 or second < 0:
        invaliddata = True
        second = 30

    done_Posts.append(replyable.id)
    file.write(replyable.id + "\n")

    local = pytz.timezone(timezone_string)
    naive = datetime.datetime.today() #Start with today (because most users will talk about today), but....
    naive = naive.replace(hour = hour, minute = minute, second = second) #... change hour, minute and second
    local_dt = local.localize(naive)

    utc_dt = local_dt.astimezone(pytz.utc)

    logging.info('    Generating ST-Link')
    url = "http://www.simplify-time.info/api-create.php?"
    url += "identifier=reddittimezonesimplifier"
    url += "&name=Reddit%20Comment%20"+replyable.id
    url += "&timezone=UTC"
    url += "&datetime=" + utc_dt.strftime("%Y-%m-%d-%H-%M")
    url += "&url=" + link
    url += "&desc=automatically%20generated%20event%20by%20the%20reddit%20bot"
    url += "&bannerurl=http://www.simplify-time.info/img/st-logo-v3.svg"
    stlink = urllib2.urlopen(url).read().strip()
    #Preparing answer
    answer = preComment;
    answer += local_dt.strftime("%H:%M:%S") + " (" + timezone_string + ") converted to other timezones:\n\n";
    logging.info('      Finished.')

    if "ERROR" in stlink:
        answer += "Creating the event on Simplify-Time failed. Please refer to the table below.\n\n"
    else:
        answer += "[In your timezone / auto detect](" + stlink + ")\n\n"
    
    output_timezones = (("UTC", "UTC / GMT"),("Europe/London", "GMT / BST / WET / WEST"), ("Europe/Berlin","CET / CEST"), ("Africa/Dar_es_Salaam", "EAT"), ( "Europe/Moscow", "MSK"), ("Asia/Kolkata","IST"),("Asia/Jakarta","WIB"),("Asia/Shanghai","ULAT / KRAT / SGT"),("Asia/Seoul","KST / JST"), ( "Australia/Sydney","AEDT / AEST"), ("Pacific/Auckland","NZST / NZDT"), ("Pacific/Honolulu", "HST / HAST"), ("America/Anchorage","AKST / AKDT"), ("America/Los_Angeles","PST / PDT"), ("America/Phoenix", "MST"),("America/Denver","MDT"), ("America/Chicago","CDT"), ("America/New_York","EST / EDT"), ("America/Sao_Paulo","BRT / BRST"), ("America/St_Johns", "NST / NDT"))
    output_timezones = collections.OrderedDict(output_timezones)
    
    answer += "Timezone | Common Abbrev. | Time | DST active\n"
    answer += ":---------:|:---------:|:---------:|:---------:|:---------:\n"
        
    for key, value in output_timezones.items():
        pytz_timezone = pytz.timezone(key)
        key_dt = local_dt.astimezone(pytz_timezone)
        answer += key + "|"+value+"|"+key_dt.strftime("%H:%M:%S")+"|"
        if key_dt.dst() == datetime.timedelta(0):
            answer += "NO"
        else:
            answer += "YES"
        answer += "\n"
    
    if not invaliddata:
        #The answer to a selftext / comment is called "add_comment" / "reply"
        if hasattr(replyable, 'add_comment'):
            replyable.add_comment(answer + signature)
        elif hasattr(replyable, 'reply'):
            replyable.reply(answer + signature)
        else:
            logging.warning('ERROR: replyable does not have add_comment or reply function.')
            raise SystemError
        logging.info('    Replied.')
    else:
        logging.info('  Post contains invalid data. (e.g. hours > 24). SKIPPING')

loopcounter = 0
infiniteLoop = True #Set to false if debugging
logging.info('Begining infinite loop')
while infiniteLoop:
    logging.debug('Starting iteration #' + str(loopcounter))
    try:
        for subreddit_name in subreddit_names:
            commentcount = 0
            submissioncount = 0
            subreddit = r.get_subreddit(subreddit_name)
            logging.debug('Looking into ' + subreddit_name)
            for submission in subreddit.get_new(limit=fetch_limit_posts):
                if submission.is_self:
                    submissioncount = submissioncount + 1
                    checkSelfOcomment(submission)
            logging.debug('  Submissions checked. (' + str(submissioncount) + ')')
            
            if subreddit_name in ignore_comments_in:
                logging.debug('  Skipping comments in this subreddit')
            else:
                for comment in subreddit.get_comments(limit=fetch_limit_comment):
                        commentcount = commentcount + 1
                        checkSelfOcomment(comment)
                logging.debug('  Comments checked (' + str(commentcount) + ')')
        logging.debug("Checking my comments for ones with < 0 points")
        commentcount = 0
        my_user = r.get_redditor(parser.get('login', 'username'))
        for comment in my_user.get_comments(limit=25):
            if comment.score < 0:
                logging.info('  Found bad comment: ' + comment.id)
                comment.delete()
                logging.info('    deleted.')
            commentcount = commentcount + 1
        logging.debug('  ' + str(commentcount) + ' comments checked.')

        #wait 15 seconds before trying again
        logging.debug('Waiting 15 seconds before continuing...')
        time.sleep(15)
        logging.debug('  Finished.')
        logging.debug('Reporting to Simplify-Time lastonline...')
        try:
            urllib2.urlopen('http://www.simplify-time.info/reddit-crawler/lastonline.php?logthis=true').read().strip()
            logging.debug('  Finished.')
        except Exception:
            logging.debug('  FAILED! Continuing....')
        loopcounter = loopcounter+1
    except (urllib2.HTTPError, requests.exceptions.HTTPError) as e:
        logging.error("HTTP ERROR: " + str(e))
        logging.error("Sleeping 60 seconds.")
        time.sleep(60)
        logging.error("  Continuing")
        pass
    except KeyboardInterrupt:
        logging.warning('Recieved KeyboardInterrupt. Breaking infinite loop')
        break
    except Exception as e:
        #logging.CRITICAL("UNHANDLED ERROR: " + str(e))
        #logging.CRITICAL("UNHANDLED ERROR: " + sys.exc_info()[0])
        logging.CRITICAL("UNHANDLED ERROR and I don't know why I'm not able to fucking print it. Goddammit.")
        logging.CRITICAL("Waiting 2 Minutes before trying again.")
        time.sleep(60*2)
        pass
file.close()
logging.warning('  File Closed. Ending now.')
