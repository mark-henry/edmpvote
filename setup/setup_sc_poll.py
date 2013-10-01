import re, urllib, ftplib, os, getpass

entries_file = "entries.json"

def get_title_and_artist(url):
  page = urllib.urlopen(url).read()
  reg = re.search("<title>(.*?) by (.*?) on SoundCloud", page);
  return reg.group(1), reg.group(2)

  
def upload_entries_file(username, password, server="ftp.alwaysdata.com", reset="y"):
  print "Connecting to FTP Server..."
  ftp = ftplib.FTP(server)
  ftp.login(username, password)
  print "Uploading file..."
  ftp.storbinary("STOR /cgi-bin/sc_poll/entries.json", open(entries_file, "rb"))
  if reset.lower().startswith("y"): 
    print "Reseting Results..."
    try:
      ftp.delete("/cgi-bin/sc_poll/sessions.json")
    except:
      pass
  ftp.quit()
  
  
def clean_up():
  print "Cleaning up..."
  os.unlink(entries_file)
  
  
def make_entries_file(itemsfile="items.txt"):
  items = open(itemsfile, "r").read().split("\n")
  items = map(lambda x:x.strip("\r"), items)
  items = filter(lambda x:x!="", items)
  
  outfile = open(entries_file, "w")
  outfile.write("{\"users\":{\n")
  
  for item in items:
    # Handle
    user, url = item.split(" ", 1)
    print "Getting data for " + url
    title, artist = get_title_and_artist(url)
    title = title.replace('"', '\\"')
    artist = artist.replace('"', '\\"')
    outfile.write('"' + user + '": {"title": "' + title + '", "url": "' + url + '"}\n')
    if item is not items[-1]:
      outfile.write(",")
      
  outfile.write("}}")
  outfile.close()
  
  
make_entries_file()
username = raw_input("FTP username: ")
password = getpass.getpass("FTP password: ")
reset = raw_input("Reset Results? [y/n]: ")
upload_entries_file(username, password, reset=reset)
clean_up()
print "Done"
