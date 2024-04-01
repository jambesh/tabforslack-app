### this is the custom loggin module to log the message 
### @Jambesh

import logging
import tableauserverclient

#Define Custom Logging Name
logger = logging.getLogger("tabforslack")

#Set the Tableau Default logging to WARNING to avoid logging every events
logging.getLogger('tableauserverclient').setLevel(logging.WARNING)

# Disabled all other external module logging -
for log_name,log_obj in logging.Logger.manager.loggerDict.items():
    if log_name != 'tabforslack':
        log_obj.disabled = True


##Custom Logger.

class tabLogger:

    #__FileLogging = False
     
    def __init__(self,filename,filemode="a",FileLogging=True):
        self.__FileLogging = FileLogging
        self.__logger = logger
        logging.basicConfig(
            filename=filename,
            level=logging.DEBUG,
            filemode=filemode,
            format='%(levelname)s : %(asctime)s : %(message)s',
            datefmt='%m-%d-%y %H:%M:%S'
            ) 
        
    @property
    def FileLogging(self):
        return self.__FileLogging

    @FileLogging.setter
    def FileLogging(self,flag):
        self.__FileLogging = flag

    def debug(self,message:str,flag=False):
        if flag or self.__FileLogging:
            self.__logger.debug(message)
        else:
            print(message)

    def info(self,message:str,flag=False):
        if flag or self.__FileLogging:
            self.__logger.info(message)
        else:
            print(message)
          

    def warn(self,message:str,flag=False):
        if flag or self.__FileLogging:
            self.__logger.warning(message)
        else:
            print(message)
     

    def error(self,message:str,flag=False):
        if flag or self.__FileLogging:
            self.__logger.error(message)
        else:
            print(message)
        

    def critical(self,message:str,flag=False):
        if flag or self.__FileLogging:
            self.__logger.critical(message)
        else:
            print(message)
      
