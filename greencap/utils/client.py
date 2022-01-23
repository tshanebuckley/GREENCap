# Currently is a simple  script to pull data into a file.
# Will want to build some type of function for converting raw data streamed from the API into json/dict or csv/dataframe.
import requests
import shutil
import uuid
import json_stream.requests
import urllib.request
import ijson

# simple function to use uuid to generate a text file name
def generate_filename():
    return f"{uuid.uuid4()}.txt"

# method to return the json response as a file
def get_redcap_json_file(url):
    local_filename = generate_filename()

    with requests.get(url, stream=True) as response:
        with open(local_filename, 'wb') as file:
            shutil.copyfileobj(response.raw, file)

    return local_filename

# method to obtain the streamed json response from a resquest as a dictionary
# Have been testing with multiple packages. So far, urllib and ijson seem to be
# the best option considering that ijson has async support. Need to learn more about
# returned data to finialize a method for returning large json responses. 
# Currently getting this error:
# ijson.common.IncompleteJSONError: parse error: premature EOF
#
#                     (right here) ------^
# Once this is complete, should be able to use this to return a pandas dataframe and
# return the result to RShiny app using reticulate.
def get_redcap_json_data(url, clean=True):
    json_data = list()
    with urllib.request.urlopen(url) as response:
        #json_stream.visit(response, visitor)
        #json_data = json_stream.load(response, persistent=True)
        #json_data.read_all()
        #json_data = ijson.items(response)
        json_data = ijson.basic_parse(response)
    return json_data

# method to get the the url response as 
def get_redcap_dataframe_data(url, clean=True):
    pass
    
url = "http://localhost:8000/redcap/bsocial/"
get_redcap_json(url)
