# import dependencies
from typing import Optional
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from asgiref.sync import async_to_sync, sync_to_async
import redcap
import pandas as pd
import fnmatch
import json
import os
import sys
import shutil
import requests
import time
import multipart
# import greencap items
from greencap import Project as GCProject
from greencap import utils as gc_utils

# initialize a GREENCap object
grncap = GCProject()

# initialize FastAPI
app = FastAPI()

# general data dictionary query -> TODO: Make this async
@app.get("/redcap/{project}/")
async def read_data(project: str, records: Optional[str] = "", arms: Optional[str] = "", events: Optional[str] = "", forms: Optional[str] = "", fields: Optional[str] = ""):
    # NOTE: If the query string is saved somewhere, then the same pull can be saved, and automated
    # use project name to get url and token from config file
    cfg = await utils.async_get_project_config(project=project)
    # if the selected REDCap is not already loaded
    if project not in grncap.redcap.keys():
        # connect to redcap (will currently be blocking)
        await grncap.async_add_project(project)
    # run the selection (should be non-blocking)
    csv = utils.run_selection(project=rc, records=records, arms=arms, events=events, forms=forms, fields=fields)
    # pipes should be run and potentially parallelized locally on the aggregated dataframe, perhaps utilize dagster here
    #csv = utils.run_pipes(df=csv, pipes=pipes)
    # return the resultant csv
    return csv
    
## BELOW HERE: NEED REFACTORED ##
    
# pulls and formats a project's metadata, usually for building selectors and verifying choices
@app.get("/meta/{project}/{item}/")
def read_meta(project: str, item: str):
	# use project name to get url and token from config file
    cfg = utils.get_project_config(project=project)
    # connect to redcap
    rc = redcap.Project(cfg['url'], cfg['token'])
    # get the item 
    selected_item = eval("rc.{i}".format(i=item))
    #selected_item = json.loads(str(list(selected_item)))
    #os.system(selected_item)
    return selected_item

@app.get("/forms/{project}")
def forms(project: str):
    # use project name to get url and token from config file
    cfg = utils.get_project_config(project=project)
    # connect to redcap
    rc = redcap.Project(cfg['url'], cfg['token'])
    # return the forms
    return rc.forms

@app.get("/fields/{project}")
def fields(project: str):
    # use project name to get url and token from config file
    cfg = utils.get_project_config(project=project)
    # connect to redcap
    rc = redcap.Project(cfg['url'], cfg['token'])
    # return the fields
    return rc.field_names

# add parameter to request nums names, or both:
# Done
#@app.get("/arms/{project}")
@app.get("/arms/{project}/{type}")
def arms(project: str, type: str = "names"):
    # use project name to get url and token from config file
    cfg = utils.get_project_config(project=project)
    # connect to redcap
    rc = redcap.Project(cfg['url'], cfg['token'])
    # nums, names, or both
    if type == "names":
        return rc.arm_names
    elif type == "nums":
        return rc.arm_nums
    elif type == "dict":
        return dict(zip(rc.arm_names, rc.arm_nums))
    # default if someone enters something other than names and nums
    #return arm_names

# return only unique event names
# Done
@app.get("/events/{project}")
def events(project: str):
    # use project name to get url and token from config file
    cfg = utils.get_project_config(project=project)
    # connect to redcap
    rc = redcap.Project(cfg['url'], cfg['token'])
    events = rc.events
    events = [x['unique_event_name'].split('_arm_')[0] for x in events]
    return events
