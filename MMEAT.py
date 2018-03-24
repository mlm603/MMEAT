# import libraries
import datetime
import pytz
import tweepy
import json
import os.path
import time
import logging
##import csv
from string import digits
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

def get_api(cfg):
  auth = tweepy.OAuthHandler(cfg['consumer_key'], cfg['consumer_secret'])
  auth.set_access_token(cfg['access_token'], cfg['access_token_secret'])
  return tweepy.API(auth)

def send_tweet(twit):
  cfg = { 
    "consumer_key"        : consumer_key,
    "consumer_secret"     : consumer_secret,
    "access_token"        : access_token,
    "access_token_secret" : access_token_secret 
    }
  api = get_api(cfg)
  tweet = twit
  status = api.update_status(status=tweet) 

def same_games():
  for x in range(1,game_count):
    try:
      #if any game exceeds threshold *that didn't in existing data*
      if float(data[x]['excitement'])<threshold and float(details[x]['excitement'])>=threshold:
          #twit it
          twit = details[x]['competitor0']+' v '+details[x]['competitor1']+' is getting good! Score: '+details[x]['score0']+'-'+details[x]['score1']+'; Excitement Index: '+details[x]['excitement']
          send_tweet(twit)
    except:
      pass

def new_game():
  try:
    #loop through games
    for x in range(1,game_count):
        #if any game exceeds threshold:
        if float(details[x]['excitement'])>=threshold:
            #twit it
            twit = details[x]['competitor0']+' v '+details[x]['competitor1']+' is getting good! Score: '+details[x]['score0']+'-'+details[x]['score1']+'; Excitement Index: '+details[x]['excitement']
            send_tweet(twit)
  except:
    pass

#set up logging file to record all data collected and any errors
logging.basicConfig(filename='MMEAT.log',level=logging.DEBUG)

#pick threshold for alerting (could potentially increase this as the tournament progresses)
threshold=4.5

#set url
quote_page = 'https://projects.fivethirtyeight.com/2018-march-madness-predictions/'

#get API keys from file located in different folder (so keys don't get pushed to github)
with open('/Users/mlm603/localhost/Twitter_MMEATool_Keys.txt') as datafile:
    keys = json.loads(datafile.read())

consumer_key=keys["consumer_key"]
consumer_secret=keys["consumer_secret"]
access_token=keys["access_token"]
access_token_secret=keys["access_token_secret"]

starttime=time.time()
#while True creates persistent loop so data updates will occur
#at the pace specified in the sleep function at the end of the loop
while True:

  #use selenium/geckodriver to open firefox
  browser = webdriver.Firefox()
  #navigate to url
  browser.get(quote_page)
  #wait for 'livegame' css class to be present (indicates that needed data is loaded from 538's external scripts)
  WebDriverWait(browser, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.livegame")))

  #FOR TESTING ONLY - REMOVE THIS LINE FOR LIVE GAMES
  #selects a past date from dropdown to allow for testing on inactive data
  ###########################################################################################################
  #Select(browser.find_element_by_id('gamedate-selector-mens')).select_by_value('March 18')
  ###########################################################################################################

  #grab all inner HTML
  innerHTML = browser.execute_script("return document.body.innerHTML")
  #close browser
  browser.quit()

  # parse the html using beautiful soup and store in variable 'soup'
  soup = BeautifulSoup(innerHTML, 'html.parser')

  #get timestamp for log and convert to date for checking if games have changed
  ts=datetime.datetime.now(pytz.timezone('US/Eastern'))
  print(ts)
  now=ts.strftime("%m-%d-%Y")

  #don't run substantive part of script if there are no excitement numbers yet (games aren't live)
  ready = soup.find(class_='excitement-num')
  if ready:
    # get useful info out of html
    #initialize competitor number (to make sure that teams are differentiated in game object)
    comp=0
    #initialize array that will hold game objects
    details=[]
    #initialize game object
    game_dets = {}
    #create object containing date and append to details array
    game_dets["date"]=now
    details.append(game_dets)
    #reset game object
    game_dets = {}
    
    #start game count at 1 since date object occupies slot 0 in the array
    game_num=1
    #add competitors to objects pushed into an array (1 object/game)
    for x in soup.findAll('td', attrs={'class':'team'}):
        #strip html formatting and seed numbers out
        clean_team = x.text.strip().translate(str.maketrans('', '', digits))
        #create object key for competitor #
        competitor="competitor"+str(comp)
        #comp value changes so 1st competitor in a game is 0 and 2nd competitor is 1
        comp=(comp+1)%2
        #add team to game object
        game_dets[competitor] = clean_team
        #if both competitors from a game have been added to the game's object
        if comp==0:
            #add game number to the game object
            game_dets["game_number"]=game_num
            #add game object to details array
            details.append(game_dets)
            #reset game object
            game_dets={}
            #increment game number
            game_num = game_num+1
            
    #start game count at 1 since date object occupies slot 0 in the array
    game_num=1
    #add excitement indices to existing game objects
    for x in soup.findAll('span', attrs={'class':'excitement-num'}):
        #strip html formatting out
        excitement_num=x.text.strip()
        #add excitement number to corresponding game object
        details[game_num]["excitement"]=excitement_num
        #increment game number
        game_num = game_num+1
  
    #start game count at 1 since date object occupies slot 0 in the array
    game_num=1
    sc=0
    #add scores to existing game objects
    for x in soup.findAll('td',attrs={'class':'score'}):
        #strip html formatting out
        clean_score = x.text.strip()
        #create object key for score # (so score can be tied to competitor)
        score="score"+str(sc)
        #sc value changes so 1st competitor in a game is 0 and 2nd competitor is 1
        sc=(sc+1)%2
        #add score to game object
        details[game_num][score]=clean_score
        #if both scores from a game have been added to the game's object
        if sc==0:
            #increment game number
            game_num = game_num+1

    #record timestamp and details array in log file
    logging.info(ts)
    logging.info(details)

    #get number of objects in details to cap index in loops
    game_count=len(details)

    #if file already exists, need to compare to existing data. Else, need to create file.
    if os.path.exists('MMEAT_data.txt'):
        with open('MMEAT_data.txt') as datafile:
            #get previous version of details array from txt file for comparison
            data = json.loads(datafile.read())
            #if the dates of the old and new arrays are the same, compare new data to existing
            if now == data[0]['date']:
                #loop through games and execute tweets as appropriate
                same_games()
            #else check if games have changed, then dump the existing data for new data
            else:
                #game sets will be assumed to be the same unless otherwise proven in for loop
                same="true"
                #loop through games to see if all competitors are the same
                for x in range(1,game_count):
                  #if any of the competitors have changed, the set of games is not the same
                  if details[x]['competitor0']!=data[x]['competitor0'] or details[x]['competitor1']!=data[x]['competitor1']:
                    same="false"
                #if we're dealing with a new set of games
                #(need this double check to prevent a tweet at midnight that would call out completed games)
                if same=="false":
                   #loop through games and execute tweets as appropriate
                  new_game()
                else:
                  #loop through games and execute tweets as appropriate
                  same_games()
            #dump existing data for new data
            with open('MMEAT_data.txt','w') as new_datafile:
                json.dump(details,new_datafile)
    else:
        #loop through games and execute tweets as appropriate
        new_game()
        #create new file with new data
        with open('MMEAT_data.txt','w') as new_datafile:
            json.dump(details,new_datafile)
  else:
    logging.warning(ts)
    logging.warning('no live games')

  #repeat process every 60 seconds
  time.sleep(60.0 - ((time.time() - starttime) % 60.0))
