#!/usr/bin/env python
import cgi, os, json

SCORE_RANGE = 10

def load_json(path):
  file = open(path, "rb")
  loaded = json.load(file)
  file.close()
  return loaded
  
class entry:
  user = 0
  points = 0
  votes = 0
  total = 0

entries = load_json("entries.json")
sessions = load_json("sessions.json")

password = "burial1"

# Password check
form_data = cgi.FieldStorage()
passwd = form_data.getfirst("passwd")
if not passwd or passwd != password:
  print "Content-Type: text/html\n\n"
  print '<html><body><form action="#" method="post"><input name="passwd" type="password" \></form></body></html>'
  exit()

# Convert dict to list
submissions = []
for user in entries["users"]:
  temp = entry()
  temp.user = user
  for ip in sessions:
    if user in sessions[ip]:
      temp.points += sessions[ip][user]
      temp.votes += 1
  submissions.append(temp)
      
# Determine total scores      
for submission in submissions:
  if submission.votes:
    submission.total = float(submission.points) / float(submission.votes)
  else: 
    submission.total = 0
  
# Sort scores, lowest to highest
submissions = sorted(submissions, key=lambda x:x.total)

# Get other stats
votes = 0
for ip in sessions:
  votes += len(sessions[ip])
stats = "STATS\n------------------------------\n"
stats = "%d unique voters cast %d votes" % (len(sessions), votes)

# Print output
print "Content-Type: text/html\n\n"
print "<html><pre>"
for submission in reversed(submissions):
  print ("%.2f" % submission.total), submission.user
print "\n\n"
print stats
print "</pre></html>"
