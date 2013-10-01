#!/usr/bin/env python
import cgi, os, json, random

SCORE_RANGE     = 10
SESSIONS_FILE   = "sessions.json"

def load_json(path):
  try:
    file = open(path, "rb")
  except:
    error("Couldn't load %s" % path)
  loaded = json.load(file)
  file.close()
  return loaded
  

def dump_json(data, path):
  temp_file = "__temp"
  file = open(temp_file, "wb")
  json.dump(data, file)
  file.close()
  os.rename(temp_file, path)
  

def load_session(ip):
  # Make sessions file if it doesn't exist
  if not os.path.exists(SESSIONS_FILE):
    file = open(SESSIONS_FILE, "wb")
    file.write("{ }")
    file.close()
  # Load sessions file
  sessions = load_json(SESSIONS_FILE)
  if ip in sessions:
    return sessions[ip]
  else:
    return {}
    

def write_sessions(ip, session):
  sessions = load_json(SESSIONS_FILE)
  sessions[ip] = session
  dump_json(sessions, SESSIONS_FILE)
  

def read_text(path):
  if os.path.exists(path):
    file = open(path, "r")
    text = file.read()
    file.close()
    return text
  else:
    return None


def soundcloud_embedded(url, width="100%", height=18, color="0066cc"):
  player_url = "http://player.soundcloud.com/player.swf?url=%s&amp;auto_play=false&amp;player_type=tiny&amp;font=Arial&amp;color=%s"
    % (url, color)
  return '''\
    <object height="%s" width="%s">
      <param name="movie" value="%s" />
      <param name="allowscriptaccess" value="always" />
      <embed allowscriptaccess="always" height="%s" src="%s" type="application/x-shockwave-flash" width="%s" />
    </object>''' % (height, width, player_url, player_url)
   
    
def error(text):
  print "Content-Type: text/html\n\n"
  print "<html><pre>ERROR: " + text + "</pre></html>"
  exit()


# Get client IP
client_ip = os.getenv("REMOTE_ADDR")

# Handle form data
form_data = cgi.FieldStorage()
user = form_data.getfirst("user")
score = form_data.getfirst("score")
oldpoll = form_data.getfirst("oldpoll")

if oldpoll:
  path = "./oldpolls/" + oldpoll
  
  # Error check
  if "." in oldpoll or "/" in oldpoll:
    error("Invalid poll name")
  if not os.path.exists(path):
    error("Poll does not exist")
    
  # Load old poll
  entries = load_json(path + "/entries.json")
  session = {}
  
else:
  entries = load_json("entries.json")
  session = load_session(client_ip)

  if user and score:
    # Error check
    if user not in entries["users"]:
      error("Invalid username value")
    elif not score.isdigit():
      error("Invalid score value")
    elif int(score) not in range(SCORE_RANGE):
      error("Invalid score range")
    # Everything is ok, update!
    session[user] = int(score)
    write_sessions(client_ip, session)
    
    
# Shuffle list according to IP address
random.seed(client_ip)
users = list(entries["users"])
random.shuffle(users)

# Render page
print "Content-Type: text/html\n\n"
print "<html>"
# Load stylesheet
print "<head><style>"
print read_text("style.css")
print "</style></head><body>"
# Header
print '<div id="header"><a href="http://www.reddit.com/r/edmproduction/"><img src="http://thumbs.reddit.com/t5_2sa4x.png?v=f99241bb2fbdb8d75030ba7dfe701d73"/></a></div>'
# Start entry list
print '<div id="content">'
for user in users:
  title = entries["users"][user]["title"]
  url = entries["users"][user]["url"]
  # Title and link
  print '<div class="entry">'
  print '<span class="title">' + '<a href="' + url + '">' + title + '</a></span>' 
  print '<span class="user">' + user + '</span>'
  # Embedded player
  if "soundcloud.com" in url:
    print '<div class="sc_player">'
    print soundcloud_embedded(url)
    print '</div>'
  # Scoring links
  if not oldpoll:
    print '<div class="score_links">'
    for i in range(SCORE_RANGE):
        print '<a class="score_link',
        if user in session and i == session[user]: 
          print 'score_link_active',
        print '" href="?user=' + user + '&score=' + str(i) + '">' + str(i) + '</a>'
    print '</div>'
  # Close entry div
  print '</div>'
# End entry list
print "</div></body></html>"



