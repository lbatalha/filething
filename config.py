import os;

app_url = "http://localhost:5000" #used for redirects et al, set to your domain

debug = True #flask debug mode

max_content_length = 100 * 1024 * 1024 #Max content size in Bytes

secret_key = "os.urandom(16)"

base_dir = "/home/lbatalha/tmp" # base directory where all files will be stored

path_length = 12 # length of file path/name for new files

ttl = 24 * 3600  #TTL in seconds to keep files

tokens = []