# Currently is a simple  script to pull data into a file.
# Will want to build some type of function for converting raw data streamed from the API into json/dict or csv/dataframe.
import json_stream.requests
import urllib.request
import pandas as pd

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
# Went back to json_stream since ijson error was proving to be difficult
def get_redcap_json_data(url):
    # open 
    with urllib.request.urlopen(url) as response:
        # get a persistent (use memory) json object
        json_data = json_stream.load(response, persistent=True)
        # read all data into memory
        json_data.read_all()
        # convert the response into a list of OrderedDicts
        oDict_list = [x._data for x in json_data]
    return oDict_list

# method to get the the url response as 
def get_redcap_dataframe_data(url):
    # gets the url response as a list of OrderedDict
    json_list = get_redcap_json_data(url)
    # convert to a pandas dataframe
    df = pd.DataFrame.from_records(json_list)
    # return the pandas dataframe
    return df
