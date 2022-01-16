# Currently is a simple  script to pull data into a file.
# Will want to build some type of function for converting raw data streamed from the API into json/dict or csv/dataframe.
import requests
import shutil
import uuid

def generate_filename():
    return f"{uuid.uuid4()}.txt"

def get_redcap_json(url):
    local_filename = generate_filename()

    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    return local_filename


url = "http://localhost:8000/redcap/bsocial/"
get_redcap_json(url)
