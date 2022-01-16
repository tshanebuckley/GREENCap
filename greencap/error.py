# redcap connection error
class REDCapConnectError(Exception):
    def __init__(self, name:str, message:str="Unable to connect to REDCap project {name}") -> None:
        self.name = name
        self. message = message
        super().__init__(message)

    def __str__(self):
        return self.message.format(name=self.name)

# redcap object error
class REDCapObjectError(Exception):
    def __init__(self, name:str, message:str="REDCap object model incorrect for project {name}") -> None:
        self.name = name
        self. message = message
        super().__init__(message)

    def __str__(self):
        return self.message.format(name=self.name)
