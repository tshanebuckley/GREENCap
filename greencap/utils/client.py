# Currently is a simple  script to pull data into a file.
# Will want to build some type of function for converting raw data streamed from the API into json/dict or csv/dataframe.
import ijson
import urllib.request
import pandas as pd
import aiohttp

# method to obtain the streamed json response from a resquest as a dictionary
def get_redcap_json_data(url):
    # make the url request
    with urllib.request.urlopen(url) as response:
        # intialize a json list
        json_data = list()
        # create a generator to recieve the streamed response
        for obj in ijson.items(response, '', multiple_values=True):
            # get all of the data from the generator
            json_data.append(obj)
    # flatten the list
    json_data = [j for i in json_data for j in i]
    # return the data
    return json_data

# method to get the redcap json data asynchronously
def async async_get_redcap_json_data(url):
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as response:
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
