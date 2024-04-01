###########################################################################################################
#@@@ Application: Tabforslack 
#@@@ Author     : JAMBESH 
#@@@ Info       : Provide Self Service functionality to most of the common Tableau admin task to developer
#@@@              without leaving the slack platform and with a very friendly natural language style.
###########################################################################################################

import re
from datetime import datetime
import json
from slack_bolt import App, Ack
from slack_bolt.adapter.socket_mode import SocketModeHandler
from library.AppInfo import InitializeSlackApp,ParseAndValidateUserQuery,TableauApp,UtilityClass
import library.AppInfo as ap
from library.tabLogger import tabLogger
import time
import os,sys
from  library.AppInfo import validate_query


# Get all direct message from the Slack App and parse the user-command to serve the request
# Slack Message Syntax :  
# 
# Explanation of syntax : 
# create-project :        create project name=selfservice - Prof of Concept server=[dev|stg|prd] site=[selfservice|default|rnd] mode=[locked | managed]
#
#                         To create a project Server and Site is optional , if both are not specified it will create on
#                         Tableau dev - selfservice site and this default is specified in config file
#                         if you specify server=[dev | stg|prd] but left site then it will create on on specified server but
#                         the default site would be selfservice
#                         if mode is unspecified then the default is Locked to Project
#
# import-group :          import group name = Tableau-SelfServe-Automation-Consumers server=[dev|stg|prd] site=[selfservice|default|rnd] role=[Explorer | Publisher]
#
#                         To import a AD group into Tableau server you can use the above syntax 
#                         Same as Project setup  server , site and role are optional if role is not specified then default site role is explorer for the AD group, if site is
#                         not specified then the default site is selfservice site, if server is also not specified then default server is dev.
#                         "group is mandatory" and can't be empty or invalid .
# grant-role        
#                         Provide Group Permission to Project:
#                         grant role name=[consumer | creator | leader | publisher] server=[dev|stg|prd] site = [selfservice|default|mapbu] group=g.Tableau-selfservice-automation-consumer project=Project Name
#                         group and project are mandatory and must be specified and valid. Server and site are optional and if omited it will be on default server and site.
#                         Consumer -- This will provide view permission on project , Explorer permission on Workbook and Data Source
#                         Creator/Publisher  -- This will provide publish permission on project , Publisher Permission on Workbook and Explorer on Data Source
#                         Leader   -- This will provide project Administrator Role on all contents belong to a project.
#
#                         Provide User Permission to Project: Except Project Lead -Dont use for individual Permission
#                         grant role name=[consumer | creator | leader | publisher] server=[dev|stg|prd] site = [selfservice|default|mapbu] user=username  project=Project Name
#
# @@@@@@@@@@@ Below Functionality will be added in V2
#                     
# describe-xx             The describe command will perform a wide variety of functionality on different object of tableau like describe project, describe workbook , describe user 
#                         describe group  -  this command should provide metadata around that object like owner,created date, members info , permissions etc ..
#                         this would be quite handy to check on any environment what access a user have, who own a workbook or project real quick.
#                        
#                         Syntax :  
#                         create project  name=projectname     server="server" site="site"                         # Display information about the project
#                         analyze  workbook name=workbookname    project=projectname server="server" site="site"     # Display information about the workbook
#                         import group name=ad-group-name-to-be-import server="server" site="site"

# for command line  use  : /tabforslack create project
#                          /tabforslack import group 
#                          /tabforslack grant role
#      


#Initialize Slack Bot information 
slackobj = InitializeSlackApp()
SLACK_APP,SLACK_APP_TOKEN,SLACK_BOT_TOKEN,SLACK_COMMAND_NAME = slackobj.get_slack_info()


app = App(token=SLACK_BOT_TOKEN, name=SLACK_APP)       
tablogger = tabLogger("./logs/tabslack.log")

#Get Slack User Profile, who requested service to response to that user
def get_slack_user_profile(client,user_id):

    try:
    # Call the users.info method using the WebClient to get the user name
        result = client.users_info(
        user=user_id
        )
        #print(f"..user info ... {result}")
        #print(f"Requesting user name : {result['user']['name']}")
        return result['user']['name']
    except :
        print("Error fetching conversations: ")

#Capture the user message typed in the slackbot messsage input , parse the user input 
#validate user input, process request and confirm back to user.
@app.message(re.compile('.*'))   
def serve_user_requests(message, say,client):

    """  
    Parse user entered message from slack IM and if all information are correct serve the request = This is the DRIVER Function.
    """
    start_time = datetime.now()
    channel_type = message["channel_type"]
    if channel_type != "im":
        return

    dm_channel = message["channel"]
    user_id = message["user"]
    chat_mesg_text = message["text"]
    
    ## important : Convert the user query to a key value string
    user_query_kiv_str = "cmd="+re.sub("(\s+)", "-", chat_mesg_text,1)
    #print(f".......got the message .... {user_query_kiv_str}")
    
    suser =  get_slack_user_profile(client,user_id)
     
    ## get the user query in a dictionary form for easy data access
    pquery = ParseAndValidateUserQuery()

    isValidQuery, query_dict = pquery.get_query_dict(user_query_kiv_str)
    isValidCommand = pquery.is_valid_command(query_dict['cmd'])
    
    #print(f"this is the initial call to the parse and validate query ...  is validquery  {isValidQuery} and query dict {query_dict} \n")
    #print(f"return to main with validcommand flag ? {isValidCommand}")

    #Keep it for debugging
    #print(f"query dictionary   =   {query_dict}")
    
    
    if isValidQuery and isValidCommand:
        
        ## Call TableauApp 
        ## validate server and site and initialize the server information 
        tabapp = TableauApp(query_dict['server'],query_dict['site'],"PAT")
        #is_valid_server_site,connection_info_dict = tabapp.validate_server_site(query_dict['server'],query_dict['site'])
        tserver_url = tabapp.serverInfo['TABLEAU_SERVER']
        tsite_url = tabapp.serverInfo['TABLEAU_SITE']

        print(f"server = {tserver_url} and site = {tsite_url}")
                
        #if server , site, command all valid then acknowledge and connect to tableau server
        say(text=f"Thank You <@{user_id}> for using Tableau Self Service Slack bot\nYour Request:  {query_dict} has been submitted", channel=user_id)
                        

        #Call appropiate tableau service based on command issued by user
        if query_dict['cmd'] == "create-project":
                    
                    
            tabapp.connect()
            res = tabapp.createProject(query_dict['name'])
            if res:
                url = tserver_url+'/#/site/'+tsite_url+'/explore?order=createdAt:desc,name:asc'
                end_time = datetime.now()
                duration = end_time - start_time  
                tabapp.disconnect()
                try:
                    tabapp.connect()
                    time.sleep(2)
                except:
                    print("can't connect to server ")
                try:
                    print(f"user ...{suser}")
                    tabapp.grant_role(query_dict['name'],"lead","individual",suser)
                    prj_message = "STATUS:SUCCESS: User:{}, Command:{}, Project:{}, Server:{}, Site:{}, Duration:{}".format(suser,query_dict['cmd'],query_dict['name'],tserver_url,tsite_url,duration.total_seconds())
                    say(text=f"Awesome <@{user_id}> !!!,\nYour Project : {query_dict['name']} is now created and You are assigned Project Admin Role !! Navigate to the link {url} to check every thing alright !!\nTime taken to create your project {duration.total_seconds()} Seconds", channel=user_id)  
                    tablogger.info(prj_message,True)
                    tabapp.disconnect()
                except:
                    prj_message = "STATUS:WARN: User:{}, Command:{}, Project:{}, Server:{}, Site:{}, Duration:{}".format(suser,query_dict['cmd'],query_dict['name'],tserver_url,tsite_url,duration.total_seconds())
                    say(text=f"Awesome <@{user_id}> !!!,\nYour Project : {query_dict['name']} is created , But you were not assigned owner role, as your name yet to setup on server, Navigate to the link {url} to check  !!\nTime taken to create your project {duration.total_seconds()} Seconds", channel=user_id)  
                    tablogger.info(prj_message,True)
                    tabapp.disconnect()
                    print("Grant Role exception...2")
                #tabapp.disconnect()
               
                
            else:
                error = "STATUS:FAILED: Requested Project Already Exist ! Can't overwrite project"
                say(text=f"Hello <@{user_id}> , {error}",channel=dm_channel)
                tablogger.error(error,True)
                tabapp.disconnect()
                    
                    #Make the requestor Project Lead.   
                    


        elif query_dict['cmd'] == "import-group":
            #implement import group here
            role = "EXPLORER" if "role" not in query_dict.keys() else query_dict['role'] 
            group_type = "local" if type not in query_dict.keys() or  query_dict['type'].lower() == "local" else query_dict['type'].lower()
            #print(f" ..group name .. : {query_dict['name']} , role name : {role} ")
            try:
                tabapp.connect()
                newgrp = tabapp.importGroup(query_dict['name'],role,group_type)
                #keep it for debugging
                end_time = datetime.now()
                duration = end_time - start_time
                grp_message = "STATUS:SUCCESS: User:{}, Command:{}, Group:{} ,Server:{}, Site:{}, Duration:{}".format(suser,query_dict['cmd'],query_dict['name'],tserver_url,tsite_url,duration.total_seconds())
                say(text=f"Thank You <@{user_id}> ,Requested AD group {query_dict['name']} imported to server {tserver_url}", channel=user_id)
                tablogger.info(grp_message,True)
                tabapp.disconnect()  
            except:
                error = "STATUS:FAILED: Possibly incorrect group name or the group already present"
                print(f"{error}")
                say(text=f"Hi <@{user_id}> , there is a {error } ", channel=user_id)
                tablogger.error(error,True)
                tabapp.disconnect()  
              

        elif query_dict['cmd'] == "grant-role":

            if    "name" not in query_dict.keys() and ("group" not in query_dict.keys() or "user" not in query_dict.keys()) and "project" not in query_dict.keys() and query_dict['name'] not in ["viewer","publisher","leader","creator"]:
                error = "STATUS:FAILED - Group Import Error ,Possible missing keywords(group or user or project or name) or Incorrect Role Specified in name"
                print(f"{error}")
                tablogger.error(error,True)
                say(text=f"Hi <@{user_id}> , there is a {error } ", channel=user_id)
            else:
                roletype =  query_dict['name'].lower()
                roleflag =  "INDIVIDUAL" if "group" not in query_dict.keys() else "GROUP"
                role_assignee  =  query_dict['user'] if roleflag == "INDIVIDUAL" else query_dict['group']
                project_name = query_dict['project']
                    
                
                
            # Connect , Grant , Notify , Disconnect 
            
                tabapp.connect()
                #Keep it for debugging
                #print(f"Inside - Grant Role : Project : {project_name},role_assignee = {role_assignee} , Role Flag = {roleflag} , Role Type = {roletype} ")
            
                res = tabapp.grant_role(project_name,roletype,roleflag,role_assignee)
                print("...return result value in main...{res}")
                if res:       
                        mesg = f"{role_assignee} is now mapped to project {project_name} with {roletype} successfully. Please check your access on server {tabapp.serverInfo['TABLEAU_SERVER']} for this project"
                        grant_mesg = "STATUS:SUCCESS: User:{}, Command:{}, Group:{}, Project:{}, Role:{}, Server:{}, Site:{} ".format(suser,query_dict['cmd'],query_dict['name'],project_name,roletype,tserver_url,tsite_url)
                        say(text=f"Thank You <@{user_id}> ,AD group  {mesg}", channel=user_id)
                        tablogger.info(grant_mesg,True)
                        tabapp.disconnect() 
                else:
                        error = "STATUS:FAILED : User/Group Mapping Error, Possible incorrect group or user or it is already mapped with higher role"
                        print(f"{error}")
                        say(text=f"Hi <@{user_id}> , there is a {error } ", channel=user_id)
                        tablogger.error(error,True)
                        tabapp.disconnect()
        elif query_dict['cmd'].strip() == "analyze-workbook":
            if  "name" not in query_dict.keys():
                error = "STATUS:FAILED - Analyze Workbook Syntax Error , missing keywords name"
                tablogger.error(error,True)
                say(text=f"Hi <@{user_id}> , Request {error } ", channel=user_id)
            else:
                workbook_name = query_dict['name']
                tabapp.connect()
                workbook_lineage = tabapp.analyze_workbook(workbook_name)
                if workbook_lineage :
                    uc = UtilityClass()
                    file_name = uc.generate_workbook_lineage_file(workbook_lineage,"pdf")
                    
                    
                    path=os.getcwd()
                    file_name = path+"/"+file_name
                    #print(f" ..file name = {file_name}")
                    tabapp.disconnect()
                    say(text=f"Hi <@{user_id}> , Successfully Generated Lineage file", channel=user_id)
                    result = client.files_upload(
                    channels=user_id,
                    title = "Here's the lineage file in pdf",
                    initial_comment="Here's the lineage file in pdf",
                    file=file_name,
                    )
                    tabLogger.info(result)
                else:
                    print("Unable to get the workbook Information")
                    tabapp.disconnect()
                    
        elif query_dict['cmd'].strip() == "query-workbook":
            if  "name" not in query_dict.keys():
                error = "STATUS:FAILED - Query Workbook Syntax Error , missing keywords  name , you should use query workbook name=your_workbook_name"
                tablogger.error(error,True)
                say(text=f"Hi <@{user_id}> , Request {error } ", channel=user_id)
            else:
                workbook_name = query_dict['name']
                tabapp.connect()
                return_flag,file_name = tabapp.query_workbook(workbook_name)
                if return_flag :
                   
                    tabapp.disconnect()
                    say(text=f"Hi <@{user_id}> , Successfully details about the workbook ", channel=user_id)
                    result = client.files_upload(
                    channels=user_id,
                    title = "Here's the lineage file ",
                    initial_comment="Here's the lineage file in pdf",
                    file=file_name,
                    )
                    tabLogger.info(result)
                else:
                    print("Unable to get the workbook Information")
                    tabapp.disconnect()

            pass
        
        
        #logger.info(f"Sent joke < {joke} > to user {user_id}")
    else:
            say(text=f"Thanks <@{user_id}> for using Tableau Self Service Slack bot, You entered an incorrect command , Server or Site !! For usage, please check the App Home Page Section Tab or check the video https://www.youtube.com/watch?v=RNjrGskMw-4", channel=dm_channel)
    ### This functionality will be for the app to respond in a channel thread - Future version .
    ### many of the functionality will be implement at later stage

##this is for advance functionality, if you want to implement tagging bot in any channel like @tabforslack
@app.event("app_mention")
def invoke_when_botname_mention(body,client,say):
    
    """ 
    Invoke This function when a user mentioned the bot name with 
    any of the SQL like Commands and pass the string to a parsing engine 
    to validate the syntax 
    """    
    #print(body)
    
    text_info       = body["event"]["text"]
    channel_name    = body["event"]["channel"]
    thread_ts       = body["event"]["ts"]
    user            = body["event"]["user"]
    #print(f"user = {user}")
    
    uid,ntxt = text_info.split(" ",1)
    ntxt = ntxt.upper() #Convert the Natural Text input to Upper Case for Consistency
    
    #say(f"Hi there! you entered .. {text}")
    #print(type(body["event"]))
    #print(body["event"])
    client.chat_postMessage(
        channel   = channel_name,
        thread_ts = thread_ts,
        text      = f"Working on your request <@{user}>\n{ntxt}"
    )

## Invoke the slack UI dialog using /slash command 
## other functionality will be added later for the slash command

@app.command(SLACK_COMMAND_NAME)
def slack_user_command_dialog(body, client, ack, logger):
    
    '''
        Functionality : Invoke GUI throgh /tabsforslack 
        and process the information from GUI.
    
    '''

    ack()
    #print(f"body text ...{body}")
    #print(f" slack command : {SLACK_COMMAND_NAME}")
    text_argument = body["text"]
    cmd_text = "-".join(text_argument.split())
    cmd_text = cmd_text.lower() 
    #text_info       = body["event"]["text"]
    channel_name    = body["channel_name"]
    user            = body["user_id"]
    
    #print(f"...user {user}")
    
   
    ##Get the dialog dynamically based on what user entered in prompt
    current_file_path = os.path.abspath(__file__) 
    parent_dir_path = os.path.dirname(current_file_path)
    configfile = "./library/"+"slackuserdialog.json"
    #print(configfile)
    try:
        with open(configfile) as j:
            dialog_selection = json.load(j)
    except:
        print("unable to open the file")

    #print(f"....{cmd_text}")
    
    #if user entered commands are valid - show the dialog else show the Help message
    #print(f" this is what entered {cmd_text}")
    print(f"entered command from dialog : {cmd_text.lower()}")
    print(f" valid commands list : {ap.valid_user_commands}")
    if cmd_text.lower() in ap.valid_user_commands:
        print("command entered is correct")
        try:
            res = client.dialog_open(
                trigger_id=body["trigger_id"],
                dialog= dialog_selection[cmd_text]
                
            )
        except Exception as e:
            
            print(f" the command is not yet implemented in the json {e}")
        #logger.debug(res)
        #mesg = "STATUS:SUCCESS User:{} , Dialog Type :{} , From:Dialog,  Date:{}".format(user,cmd_text,datetime.now())
        #tablogger.info(mesg)
    else:
        client.chat_postMessage(
        channel   = user,
        text      = f"\nHi <@{user}> ,\n Currently Supported Valid commands are\n1) /tabforslack create project\n2)/tabforslack import group\n3)/tabforslack grant role\n 4)/tabforslack schedule flow \nFor more info check the tabforslack reference : https://www.youtube.com/watch?v=RNjrGskMw-4" 
        )
        
        tablogger.critical("Invalid Command Specified")
        #logger.debug(res)

## This will get called when the user request will submit throgh GUI 
@app.action(re.compile("|".join(ap.valid_user_commands)))
def dialog_submission_or_cancellation(ack: Ack, body: dict,say,client):
    if body["type"] == "dialog_cancellation":
        # This can be sent only when notify_on_cancel is True
        ack()
        return

    user_id = body['user']['id']
    suser = get_slack_user_profile(client,user_id)
    
    #channel_name = body['channel']['id']  
    #print(f"........body info .....{body}")
    
    def slackdm(message):

        client.chat_postMessage(
        channel   = user_id,
        text      = f"Hi <@{user_id}> , {message}"
    )
    
    
    ## Initialize the Class for query validation
    pquery = ParseAndValidateUserQuery()

    #get the user input submitted from the form in a dictionary for easy data access
    
    bool_ret,user_query_kiv_str = pquery.get_user_dialog_data(body)
    if bool_ret:
        #Collect Info-
        tserver = user_query_kiv_str['server_name']
        tsite = user_query_kiv_str['site_name']
        cmd = user_query_kiv_str['cmd']
        print(f" command from dialog : {cmd.lower()}")
        ## Call and Initialize TableauApp 
        ## validate server and site and initialize the server information with authentication Info
        tabapp = TableauApp(tserver,tsite,"PAT")
        tserver_url = tabapp.serverInfo['TABLEAU_SERVER']
        tsite_name = tabapp.serverInfo['TABLEAU_SITE']
        #_,connection_info_dict = tabapp.validate_server_site(user_query_kiv_str['server_name'],user_query_kiv_str['site_name'])

        ack()
        #tssr = TableauSelfServiceRequest(connection_info_dict)
        
        if user_query_kiv_str['cmd'].lower() == "create-project":
            projectname = user_query_kiv_str["project_name"]
            #print(f"{user_query_kiv_str['server_name']},'--',{user_query_kiv_str['site_name']},'...',{user_query_kiv_str['project_name']} , ....{user_query_kiv_str['project_mode']} ")
            say(text=f"Thank You <@{user_id}> for using Tableau Self Service Slack bot\nYour Request:  {user_query_kiv_str} has been submitted", channel=user_id)
            start_time = datetime.now()
            
            tabapp.connect()
            res = tabapp.createProject(user_query_kiv_str['project_name'])
            if res:
                        tabapp.disconnect()
                        try :
                            url = tserver_url+'/#/site/'+tsite+'/explore?order=createdAt:desc,name:asc'
                            time.sleep(2)
                            tabapp.connect()
                            tabapp.grant_role(user_query_kiv_str['project_name'],"lead","individual",suser)
                            end_time = datetime.now()
                            duration = end_time - start_time
                            mesg = f"Your Project : {user_query_kiv_str['project_name']} is now created and You are set as Project Admin.\nNavigate to the link {url} to make sure every thing alright !\nTime taken to create your project {duration.total_seconds()} Seconds"
                            log_mesg = "STATUS:SUCCESS : user:{}, Command:{}, Project: {}, Server: {}, Site: {}, Channel:Dialog".format(suser,cmd,projectname,tserver_url,tsite_name)
                            say(text=f"Awesome <@{user_id}> {mesg}", channel=user_id)                  
                            #slackdm(mesg)
                            tablogger.info(log_mesg)
                            tabapp.disconnect()
                        except:
                            url = tserver_url+'/#/site/'+tsite+'/explore?order=createdAt:desc,name:asc'
                            error = f"STATUS:PARTIAL SUCCESS  {user_query_kiv_str['project_name']} is now created but could not make as owner.\nNavigate to the link {url} to check the project !"
                            say(text=f"Hello  <@{user_id}>, {error}", channel=user_id)
                        
            else:
                        mesg_err= "STATUS:FAILED Requested Project Already Exist, Can't Overwrite project !"
                        say(text=f"Hi <@{user_id}> , {mesg_err}",channel=user_id)
                        #slackdm(mesg_err)
                        tablogger.error(mesg_err)
                        tabapp.disconnect()
            
            

        elif user_query_kiv_str['cmd'].lower() == "import-group":
            print(f"user query kiv string : {user_query_kiv_str}")
            groupname = user_query_kiv_str['group_name']
            rolename = user_query_kiv_str['role_name']
            group_type = user_query_kiv_str['group_type']
            print(f" group name, group role, group type = {groupname},{rolename},{group_type}")
            #print(f"{user_query_kiv_str['type']}")
            #print(f"{tserver},'--',{tsite},'...',{greoupname},....{rolename}")
            try:
                tabapp.connect()
                newgrp = tabapp.importGroup(groupname,rolename,group_type)
                mesg = f"Requested AD group {groupname} imported to Server : {tserver_url} , Site: {tsite_name}"
                log_mesg = "STATUS:SUCCESS: User:{} , Command: {} , Group: {}, Role: {} ,Server: {},Site: {}, Channel:Dialog".format(suser,cmd,groupname,rolename,tserver_url,tsite_name)
                say(text=f"Thank You <@{user_id}> , {mesg}", channel=user_id)
                tabapp.disconnect()
                #slackdm(mesg)
                tablogger.info(log_mesg)
            
            except:
                error = "STATUS:FAILED: Unable to Import specified AD group , Possibly incorrect AD group or the group already exist"
                print(f"{error}")
                say(text=f" <@{user_id}> , {error} ", channel=user_id)
                tabapp.disconnect()
                #slackdm(error)
                tablogger.error(error)
            
        elif  user_query_kiv_str['cmd'].lower() == "grant-role":
            #print(f" user query string in grant role ... {user_query_kiv_str['cmd'].lower()}")
            try:
                
                roletype = user_query_kiv_str['role_name']
                roleflag = "GROUP"
                role_assignee = user_query_kiv_str['group_name']
                project_name = user_query_kiv_str['project_name']
                
                #print(f"Grant Role :  {role_assignee} .... {project_name} .. {roletype} ... {tabapp.serverInfo['TABLEAU_SERVER']} ..")
                
                tabapp.connect()
                res = tabapp.grant_role(project_name,roletype,roleflag,role_assignee)
                if res:
                    mesg = f"{role_assignee} is now mapped to Project {project_name} with {roletype} Role successfully. Please check your access on server {tserver_url} for this project"
                    log_mesg = "GRANT ROLE SUCCESS: User: {} , Command: {} , Group/User: {}, Role Type: {}, Project: {}, Server: {}, Site: {}, Channel:Dialog".format(suser,cmd,role_assignee,roletype,project_name,tserver_url,tsite)
                    say(text=f"Thank You <@{user_id}> , Group {mesg}", channel=user_id)
                    tabapp.disconnect()
                    #slackdm(mesg)
                    tablogger.info(log_mesg)
                else:
                    error = "STATUS:FAILED: Trouble Processing Grant Role Command , Something unusual Happend"
                    say(text=error, channel=user_id)
                    tabapp.disconnect()
                    #slackdm(error)
                    tablogger.error(error)
            
            except:
                error = "STATUS:FAILED: Unable to Map AD group To Project with specified Role, Please make sure you enter the AD group & Project Correctly"
                tablogger.error(error)
                tabapp.disconnect()  

        elif  user_query_kiv_str['cmd'].lower() == "schedule-flow":
            tablogger.info("Invoked Schedule Flow Command , Connecting To Tableau Server")
            tabapp.connect()  
            time.sleep(1)
            flowname = user_query_kiv_str['flow_name']
            schedule = user_query_kiv_str['schedule_name']  
            
            #print(f"Flow Name enter {flowname}") 
            #print(f"schedule name selected {schedule}")
            try:
                
                if schedule == "Run Now":
                    tablogger.info("calling Flow Run - Once")
                    status = tabapp.executeflow(flowname)
                    status = f"Flow satus = {status}"
                    tablogger.info(status)
                    tabapp.disconnect()
                else: 
                    import numpy as np
                    now = datetime.now()
                    formatted_date = np.datetime64(now).astype(object)
                    formatted_date_string = formatted_date.strftime('%m:%d:%y %H:%M:%S') 
                    mesg = f"Alert Flow Schedule Requested , Requested Time:{formatted_date_string} , User:{suser} ,  Flow:{flowname} ,  Schedule:{schedule} "
                    print(mesg)
                    #say(text=mesg, channel=user_id)
                
            except:
                error= f"some thing went wrong , Either not able to connect to Server or has problem executing flow run"
                tablogger.error(error)
    else:
        print("Invalid Server or site mentioned")
        mesg_err= "STATUS:FAILED Invalid Server or Site Provided !"
        say(text=f" <@{user_id}> , It Seems you provided either a wrong server or site value , Pls correct and resubmit {mesg_err}",channel=user_id)

#This is the App Home screen, when the home tab in slack bot clicked, this will display the information
@app.event("app_home_opened")
def app_home_opened(event, client):
    user_id = event["user"]
    current_file_path = os.path.abspath(__file__)
    #parent_dir_path = os.path.dirname(os.path.dirname(current_file_path))
    #print(f"current file path {current_file_path}")
    configfile = "./library/"+"slackuserdialog.json"
    with open(configfile) as j:
        dialog_selection = json.load(j)

    try:
        # Call the views.publish method using the WebClient passed to listeners
        result = client.views_publish(
            user_id=user_id,
            view=dialog_selection["home-tab-view"],
        )
        #logger.info(result)

    except :
        #logger.error("Error fetching conversations: {}")
        tablogger.error("STATUS:FAILED: Error fetching home page conversations:")


# Main Thread Start Here 
def main():
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()

if __name__ == "__main__":
    main()
