import pydantic
from typing import Optional
import json

class REDCapCred(pydantic.BaseModel):
    '''
    This object is for validating the REDCap credentials for an
    individual PyCap Project object.
    '''
    pass

# todo add validations and error messages
class GREENCapCred(pydantic.BaseModel):
    '''
    This object is for validating the credentials given to a GREENCap
    class object when adding a new REDCap object to it's list of
    modified PyCap Project objects. 
    '''
    name: str
    url: str
    token: str
    local: bool
    cli: bool
    cred: Optional[REDCapCred]

    if cred:
        name = cred.name
        url = cred.url
        local = cred.local
        cli = cred.cli


    @pydantic.root_validator(pre=True)
    @classmethod
    def check_connection(cls, value):
        try:
            redcap.Project(value["url"], value["token"])
        except:
            raise REDCapConnectError(name=values["name"],
            message="Unable to connect to REDCap project {name}.".format(name=values["name"]))
        return value

    @pydantic.root_validator(pre=True)
    @classmethod
    def check_name(cls, value):
        if value["name"] == None and value["cli"] == False:
            raise InvalidNameError(message="Name must be provided.")
            
# convenience function for getting the greencap config file data, TODO: configure this to integrate with a system
def get_greencap_config():
    file_path = str(pathlib.Path.home()) + '/.greencap/greencap_config.yaml'
    # open the file
    try:
        f = open(file_path,)
    except:
        f = open(file_path.replace('.yaml', '.yml'))
    # load the yaml as a dict
    d = yaml.load(f, Loader=yaml.FullLoader)
    # return the dict
    return(d)

# convenience function for getting the config file data, TODO: configure this to integrate with a system
def get_project_config(project = None):
    file_path = str(pathlib.Path.home()) + '/.greencap/projects/{proj}.json'.format(proj=project)
    # open the file
    f = open(file_path,)
    # load the json as a dict
    d = json.load(f)
    # return the dict
    return(d)
