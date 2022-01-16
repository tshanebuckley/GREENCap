# import dependencies
import atexit
import sys
import os
import yaml
import json
import redcap
import asyncio
import aiohttp
import aiofiles
import aiopath
import pydantic
import tqdm
from uuid import uuid4
from datetime import date, datetime, time, timedelta
from requests import RequestException, Session
from typing import Optional, List
from asgiref.sync import sync_to_async, async_to_sync
from greencap.utils import utils as gc_utils
from greencap.utils import creds as gc_creds
from greencap.requests import REDCapRequest
from greencap.error import REDCapConnectError
import getpass

# method to create a redcap project
def create_redcap_project(name=None):
    creds = gc_creds.get_project_config(project = name)
    creds["name"] = name
    return REDCapProject(**creds)


def user_project(name=None, url=None, token=None, cli=False, local=True):
    # NOTE: could make this a sub-function for parsing inputs
    # if the name is None and cli is true, use getuser
    if name == None:
        if cli == True:
            name = getpass.getuser("Name: ")
        else:
            raise Exception("Error: Name is None and cli is false")
    # url uses same logic as name
    if url == None:
        if cli == True:
            url = getpass.getuser("URL: ")
        else:
            raise Exception("Error: URL is None and cli is false")
    if token == None:
        if cli == True:
            token = getpass.getpass("Token: ")

    # logic for create, remove, and update functions based on if local or not

# redcap connection error
class REDCapConnectError(Exception):
    def __init__(self, name:str, message:str) -> None:
        self.name = name
        self. message = message
        super().__init__(message)

# pydantic BaseClass object for a REDCap project
class REDCapProject(pydantic.BaseModel):
    url: str
    token: str
    name: str

    @pydantic.root_validator(pre=True)
    @classmethod
    def check_connection(cls, values):
        try:
            redcap.Project(values["url"], values["token"], lazy=True)
        except:
            raise REDCapObjectError(name=values["name"])
        return values


# based off of PyCap's Project Class
# TODO: apply Plugin Design Pattern
# Would like plugins for MongoDB, NIDM, RDF, XNAT, etc
# REDCap instance would have a Project w/ access to the above resources
class Project:
    # use the original __init__ with sycn _call_api
    def __init__(self, projects=[], verify_ssl=True, lazy=False,
                num_chunks=10, extended_by=['records'],
                use_cfg=True, **kwargs):
        # initialize a url variable
        self.curr_url = ''
        # if set default to the yaml config settings
        if use_cfg:
            # try to load the yaml cfg
            try:
                self.cfg = gc_creds.get_greencap_config()
            except:
                print("No config file found.")
            # initialize the base number of chunks for api calls
            try:
                self.num_chunks = self.cfg['num_chunks']
            except:
                self.num_chunks = num_chunks
                print("Using default number of chunks since no configuration was found.")
            # initialize the criteria to extend api calls by
            try:
                self.extended_by = self.cfg['extended_by']
            except:
                self.extended_by = extended_by
                print("Using default method to extend api calls by since no configuration was found.")
        # otherwise, just use the arguments given/set by default in code
        else:
            self.num_chunks = num_chunks
            self.extended_by = extended_by
        # initialize kwargs
        self._kwargs = kwargs
        # initialize the aiohttp client
        #self._session = aiohttp.ClientSession()
        # initialize a dictionary of redcap projects
        # NOTE: will probably change this to self.remotes
        self.redcap = dict()
        # get the greencap Project a redcap Project to base itself around
        for project in projects:
            self.add_project(project)
        # add a variable for the current list of payloads
        self._payloads = dict() # payload is the data for the post request

    # function to close the aiohttp client session on exit
    #@atexit.register
    #def _end_session(self):
    #    self._session.close()

    # overwrite the sync _call_api method
    def _call_api(self, payload, typpe, **kwargs): # async
        request_kwargs = self._kwargs
        request_kwargs.update(kwargs)
        rcr = redcap.RCRequest(self.curr_url, payload, typpe) # self.url,
        return rcr, request_kwargs

    # method to get the list of id records of the defining field of a project
    def get_records(self, rc_name):
        # run a selection to grab the list of records
        record_list = gc_utils.run_selection(project=rc_name, fields=rc_name.def_field, syncronous=True)
        # return the records
        return record_list
    
    # method to get the list of id records of the defining field of a project
    async def async_get_records(self, rc_name):
        # have the base return value be an empty list
        record_list = []
        # if this project has been initialized in the object
        if rc_name in self.redcap.keys():
            # get the records
            record_list = await gc_utils.async_get_records(rc_name)
        # return the records
        return record_list

    # method to add a project
    # NOTE: plugins could be applied here by appending more data via add_project to the objects in
    # self.redcap or by extending the self.redcap dictionary itself (would want to rename this self.remotes
    # along with this function to add_remote and add a 'type' argument)
    def add_project(self, name):
        # try to add the project
        try:
            # use pydantic to create a verified redcap connection
            rc_data = create_redcap_project(name)
            # add the project to the dict
            self.redcap[rc_data.name] = redcap.Project(rc_data.url, rc_data.token, name=rc_data.name)
            # add a .records field that contains all of the values for the def_field
            self.redcap[rc_data.name].records = self.get_records(rc_name=self.redcap[rc_data.name])
            # run the alterations for _call_api
            setattr(self.redcap[rc_data.name], "_call_api", self._call_api)
        # log the failure
        except pydantic.ValidationError as e:
            print(e)

    '''
    # add a request
    async def exec_request(self, data, method='POST', url=self.curr_url):
        try:
            response = await self._session.request(method=method, url=url, data=data)
            response.raise_for_status()
            print(f"Response status ({url}): {response.status}")
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An error ocurred: {err}")
            response_json = await response.json()
            return response_json
    '''

    # gets a payload
    @sync_to_async
    def get_payload(self, rc_name, func_name, method, **func_kwargs):
        # set the current url
        self.curr_url = self.redcap[rc_name].url
        # run the function
        rcr = eval("self.redcap['{name}'].".format(name=rc_name) + func_name + "(**func_kwargs)")
        # create a dictionary of the kwargs
        request_args = {'url':self.redcap[rc_name].url, 'data':rcr.payload, 'method':method}
        # extract only the payload, a tuple of the url to make the request to and the payload
        return request_args

    # gets the payloads by extending to all possible calls and then chunking them
    async def exec_request(self, method, selection_criteria=dict(), extended_by=None, num_chunks=None, rc_name=None, func_name=None, sleep_time=0):
        # set some variables defined by the object if not set by the function
        if num_chunks == None:
            num_chunks = self.num_chunks
        if extended_by == None:
            extended_by = self.extended_by
        # get the required selection_criteria for the func_name given
        gc_cfg = await gc_creds.async_get_greencap_config()
        # select the redcap function defaults arguments
        func_defaults = gc_cfg['redcap'][func_name]['defaults']
        # add any keys from the config if not in selection criteria
        for key in func_defaults:
            if key not in selection_criteria.keys():
                selection_criteria[key] = func_defaults[key]
        # if no record names are given, get the record names
        if selection_criteria['records'] == None:
            selection_criteria['records'] = await self.get_records(rc_name)
        # log that the payloads are being generated
        print("Generating payload(s).")
        # get the api calls
        api_calls = gc_utils.extend_api_calls(self.redcap[rc_name], selection_criteria=selection_criteria, extended_by=extended_by, num_chunks=num_chunks)
        # initialize a Payload object to save the payloads to
        ploads = list()
        # for each api call
        for call in api_calls:
            # create a payload
            pload = asyncio.ensure_future(self.get_payload(rc_name=rc_name, func_name=func_name, method=method, **call))
            # generate and save the payloads as a Payload object
            ploads.append(pload)
        # log number of calls
        print("Executing {n} request(s)...".format(n=str(len(api_calls))))
        # run the payload generation
        ploads = await asyncio.gather(*ploads)
        # get an id for the payload/request
        _id = str(uuid4())
        # save this new Payload object within the class
        self._payloads[_id] = ploads
        # determine if the project is longitudinal
        long = gc_utils.is_longitudinal(self.redcap['bsocial'])
        # create the request
        req = REDCapRequest(_id=_id, payloads=ploads, longitudinal=long, arms=None, events=None, sleep_time=sleep_time)
        # submit the request
        await req.run() # response =
        # log that the calls have finished
        print("{n} request(s) have finished.".format(n=str(len(req.content))))
        # drop the payload from the _payloads dict
        self._payloads.pop(_id)
        # clean the response (we get back a lis of json strings)
        
        # return the response
        return req
