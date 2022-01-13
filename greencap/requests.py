import asyncio
import redcap
import aiohttp
import aiofiles
import aiopath
from datetime import datetime
import tqdm

# TODO: come back and make this verify with pydantic
# redcap payload class
class REDCapRequest(): # pydantic.BaseModel
    #_id: str
    #payloads: list
    #response: list
    #creation_time: datetime
    #request_time: datetime
    #response_time: datetime
    #call_time: datetime
    #status: str = 'created' # can be created, running, completed

    # NOTE: all logic should be called when this class is initialized
    # NOTE: look into why forms for all records are failing
    # Will get payloads as tasks, execute the request, and return the response
    def __init__(self, _id, payloads, sleep_time, **data):
        '''
        The argument of **data must include values for 'url' and 'method'. It can also included
        other arguments used by aiohttp.ClientSession().request().
        '''
        #super().__init__(_id, payloads, **data)
        # set the id
        self._id = _id
        # create a session for this request
        self.session = aiohttp.ClientSession()
        # set the payload list
        self.payloads = payloads
        # set the creation time
        self.creation_time = datetime.now()
        # save the sleep time used per execution of each task
        self.sleep_time = sleep_time

    async def run(self):
        # sub function to apply a sleep
        # TODO: use same logic as below to read streams in the same thread as the request
        async def run_fetch(sleep_time, my_coroutine):
            # sleep
            await(asyncio.sleep(sleep_time))
            # perform the fetch
            fetch_resp = await my_coroutine
            # extract the content from the StreamReader
            streamed_content = await fetch_resp.content.read()
            # replace the StreamReader with its content
            fetch_resp.content = streamed_content
            #print(fetch_resp)
            return fetch_resp
        # set the task list
        request_tasks = list()
        # for each payload given
        for pload in self.payloads:
            # create a task
            # NOTE: need a method to convert payloads to resuests so that they can be added to the list of tasks
            request_task = asyncio.ensure_future(run_fetch(self.sleep_time, self.session.request(**pload)))
            # append that task to the list of tasks
            request_tasks.append(request_task)
        # add a progress bar
        #prog = [await f for f in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks))]
        # set the request_time
        self.request_time = datetime.now()
        # set the status to 'running'
        self.status = 'running'
        # execute the request with progress bar
        [await f for f in tqdm.tqdm(asyncio.as_completed(request_tasks), total=len(request_tasks))]
        self.response = await asyncio.gather(*request_tasks)
        # set the response time
        self.response_time = datetime.now()
        # set the status to 'completed'
        self.status = 'completed'
        # close the session
        await self.session.close()
        # set the call_time as response_time - request_time
        self.call_time = self.response_time - self.request_time
        # convert times into strings and call time into seconds
        self.creation_time = str(self.creation_time)
        self.request_time = str(self.request_time)
        self.response_time = str(self.response_time)
        self.call_time = self.call_time.total_seconds()
        self.content = [resp.content for resp in self.response]
