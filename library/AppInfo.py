## Idea and Developed by : Jambes M
## Purpose      : This Slack BIbot is developed with an aim to facilitate self service BI on all Tableau environment
## Version1.0   :  
 

import yaml
import tableauserverclient as TSC
import re
import json
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from library.tabLogger import tabLogger
import pdfkit
import os


wb_consumer_capabilities = {TSC.Permission.Capability.Read: TSC.Permission.Mode.Allow,TSC.Permission.Capability.WebAuthoring: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ExportData: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ExportImage: TSC.Permission.Mode.Allow,TSC.Permission.Capability.Filter: TSC.Permission.Mode.Allow,TSC.Permission.Capability.AddComment: TSC.Permission.Mode.Allow,TSC.Permission.Capability.RunExplainData: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ViewUnderlyingData: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ShareView: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ViewComments: TSC.Permission.Mode.Allow}
wb_publisher_capabilities = {TSC.Permission.Capability.Read: TSC.Permission.Mode.Allow,TSC.Permission.Capability.Write: TSC.Permission.Mode.Allow,TSC.Permission.Capability.WebAuthoring: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ExportData: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ExportImage: TSC.Permission.Mode.Allow,TSC.Permission.Capability.Filter: TSC.Permission.Mode.Allow,TSC.Permission.Capability.AddComment: TSC.Permission.Mode.Allow,TSC.Permission.Capability.RunExplainData: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ViewUnderlyingData: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ShareView: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ViewComments: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ExportXml: TSC.Permission.Mode.Allow}
ds_consumer_capability = {TSC.Permission.Capability.Connect: TSC.Permission.Mode.Allow,TSC.Permission.Capability.Read: TSC.Permission.Mode.Allow} 
ds_publisher_capability = {TSC.Permission.Capability.Connect: TSC.Permission.Mode.Allow,TSC.Permission.Capability.Read: TSC.Permission.Mode.Allow,TSC.Permission.Capability.Write: TSC.Permission.Mode.Allow,TSC.Permission.Capability.ExportXml: TSC.Permission.Mode.Allow}      
project_read_capability = {TSC.Permission.Capability.Read: TSC.Permission.Mode.Allow}
project_lead_capability = {TSC.Permission.Capability.ProjectLeader: TSC.Permission.Mode.Allow}
project_publish_capability = {TSC.Permission.Capability.Write: TSC.Permission.Mode.Allow}



def get_env():  
    current_file_path = os.path.abspath(__file__)
    parent_dir_path = os.path.dirname(os.path.dirname(current_file_path))
    configfile = parent_dir_path+"/library/"+"config.yaml"
     
    with open(configfile) as envinfo:
         data = yaml.load(envinfo, Loader=yaml.FullLoader)
    return data
#Load the config File
configdata = get_env()


tableau_domain      = configdata["TABLEAU_DOMAIN"]["NAME"]
valid_user_commands = configdata["VALID_SLACK_USER_COMMAND"]["NAME"]
'''
wb_consumer_capabilities = configdata["TABLEAU_CAPABILITY"]["WB_CONSUMER"]
wb_publisher_capabilities = configdata["TABLEAU_CAPABILITY"]["WB_PUBLISHER"]
ds_publisher_capability = configdata["TABLEAU_CAPABILITY"]["DS_PUBLISHER"]
ds_consumer_capability = configdata["TABLEAU_CAPABILITY"]["DS_CONSUMER"]
project_read_capability = configdata["TABLEAU_CAPABILITY"]["PROJECT_READ"]
project_lead_capability = configdata["TABLEAU_CAPABILITY"]["PROJECT_READ"]
project_publish_capability = configdata["TABLEAU_CAPABILITY"]["PROJECT_PUBLISH"]
'''




class InitializeSlackApp:
    
    __slack_app_info = {}
    def __init__(self):        
        #data = get_env()
        self.__slack_app_info["SLACK_APP_NAME"]     = configdata["SLACK_ENV"]["SLACK_APP_NAME"]
        self.__slack_app_info["SLACK_APP_TOKEN"]    = configdata["SLACK_ENV"]["SLACK_APP_TOKEN"]
        self.__slack_app_info["SLACK_BOT_TOKEN"]    = configdata["SLACK_ENV"]["SLACK_BOT_TOKEN"]
        self.__slack_app_info["SLACK_COMMAND_NAME"] = configdata["SLACK_ENV"]["SLACK_COMMAND_NAME"]

    def get_slack_info(self):
        APP_NAME = self.__slack_app_info["SLACK_APP_NAME"]
        APP_TOKEN = self.__slack_app_info["SLACK_APP_TOKEN"]
        BOT_TOKEN = self.__slack_app_info["SLACK_BOT_TOKEN"]
        COMMAND_NAME = self.__slack_app_info["SLACK_COMMAND_NAME"]
        return APP_NAME,APP_TOKEN,BOT_TOKEN,COMMAND_NAME
        

class TableauApp:
    
    def __init__(self,userver,usite,auth_type="PASS"):
        self.userver = userver 
        self.usite  = usite
        self.isValidServerAndSite,self.serverInfo = self.validate_server_site(self.userver,self.usite)
        try:
            if auth_type == "PAT":
                self.tableau_auth = TSC.PersonalAccessTokenAuth(self.serverInfo["TOKEN_NAME"], self.serverInfo["TOKEN_SECRET"], site_id=self.serverInfo["TABLEAU_SITE"])
            else:
                self.tableau_auth = TSC.TableauAuth(self.serverInfo['SVC_USER'],self.serverInfo['SVC_PASS'],site_id=self.serverInfo["TABLEAU_SITE"])
            self.tserver = TSC.Server(self.serverInfo["TABLEAU_SERVER"], http_options={"verify": False},use_server_version=True)
            ##below one just for testing.
            self.tsc = TSC
        except:
            print("Invalid Server or Site Specified ")

    def validate_server_site(self,userver,usite="SelfService"):
        
        validServersAndSites = {}
        tableau_app_info = {}
        userver=userver.upper()
       
        #data = get_env()

        for server in list(configdata["TABLEAU_ENV"].keys()):
            validServersAndSites[server] = configdata['TABLEAU_ENV'][server]['SITES']
        #print(f"1: value of the server and sites ..{validServersAndSites} ")

        if userver  in [k.upper() for k in validServersAndSites.keys()]:
            #print(f"2: Provided Server {userver} is Valid Server..")
            if  usite.upper() == "DEFAULT":
                usite = ''
            
            else:
                usite = tableau_app_info["TABLEAU_SITE"]= usite

            #msg= f"3:No Site Provided,Setting site to default  :  {usite} "
            
            tableau_app_info["TOKEN_NAME"] = configdata['TABLEAU_ENV'][userver]["TOKEN_NAME"]
            tableau_app_info["TOKEN_SECRET"] = configdata['TABLEAU_ENV'][userver]["TOKEN_SECRET"]
            tableau_app_info["TABLEAU_SERVER"]= configdata['TABLEAU_ENV'][userver]["SERVER"]
            tableau_app_info["TABLEAU_SITE"]= usite
            tableau_app_info['SVC_USER'] = configdata['TABLEAU_ENV'][userver]["SVC_USER"]
            tableau_app_info["SVC_PASS"] = configdata['TABLEAU_ENV'][userver]["SVC_PASS"]
            #print(f"5.is_valid_server_and_sites: conn info dict before return..{tableau_app_info}")
             
            return True,tableau_app_info          

        else:
            #emsg = f"In valid_server_and_sites:Error:Invalid server: {userver}"
            #tablogger.error(emsg)
            return False,tableau_app_info


    def connect(self):
        try:
            
            conn = self.tserver.auth.sign_in(self.tableau_auth)
            print("connect: Successfully sign-in to the server")
            return conn
        except:
            print("connect: Failed To Connect to the server")
            
    
    def disconnect(self):
        try:
            self.tserver.auth.sign_out()
            print("disconnect: Logout Success")
        except:
            print("disconnect: Problem with logout")
        
    def createProject(self,project_name,permission="LOCKED",parent_id=None):
        
        if len(permission)==0 or permission.upper() == "LOCKED":
            NewPerm = TSC.ProjectItem.ContentPermissions.LockedToProject
        else:
            NewPerm = TSC.ProjectItem.ContentPermissions.ManagedByOwner

        new_project = TSC.ProjectItem(name=project_name,content_permissions=NewPerm,parent_id=parent_id,description="Created using tabforslack")
        try:
            project_item = self.tserver.projects.create(new_project)        
            return project_item
        except TSC.ServerResponseError:
            print(f"2.createProject: EXCEPTION : Project {new_project.name} already exist on the server, Please check the name" )
            
            #project_items = server.projects.filter(name=top_level_project.name)
            

    def importGroup(self,group_name,role_name="EXPLORER"):
        
        newgroup = TSC.GroupItem(name=group_name,domain_name=tableau_domain)
        if role_name.upper() == "EXPLORER" or role_name.upper() == "CONSUMER":
            newgroup.minimum_site_role = TSC.UserItem.Roles.Explorer
        elif role_name.upper() == "CREATOR":
            newgroup.minimum_site_role = TSC.UserItem.Roles.Creator
        elif role_name.upper() == "PUBLISHER":
            newgroup.minimum_site_role = TSC.UserItem.Roles.ExplorerCanPublish
        else:
        ##Default Role - Explorer if either not specified or something accidentally typo
            newgroup.minimum_site_role = TSC.UserItem.Roles.Explorer
        ## Grant License Upon login to Server - Dont grant License as import
        newgroup.license_mode = TSC.GroupItem.LicenseMode.onLogin
        #print(f"import group : {group_name}")
        #print(f"group type : {type(group_name)}")
        try:
        # call the create method to create the group
            #print(f"1.importGroup: Group : {newgroup.name} imported to server : {self.serverInfo['TABLEAU_SERVER']} , site : {self.serverInfo['TABLEAU_SITE']}")
            newgroup = self.tserver.groups.create_AD_group(newgroup)
            #print("success group import")           
            return newgroup
        except:
            print("2.importGroup: Unable to Import the Group , Please check the AD group name")
         
    
    def set_wb_role(self,project,assignee,wb_rule):
        # Workbook Permission Rule for the group
        wb_rules = [TSC.PermissionsRule(grantee=assignee, capabilities=wb_rule)]
        try:
            #print(f" Inside  Project Role Setup Function  project = {project} , assignee = {assignee} , rule = {wb_rule}")
            new_default_wb_permissions = self.tserver.projects.update_workbook_default_permissions(project, wb_rules)
            if new_default_wb_permissions:
                return True
            #print(f"Project {project} Permission Updated for Asignee - {assignee}")
        except:
            
            print(f"ERROR: Default Project Permission Updated for WB Rule :  {project} , Asignee - {assignee}")
            return False
            

    def set_project_role(self,project,assignee,pr_rule):
        rule = TSC.PermissionsRule(assignee, capabilities=pr_rule)

        try:
            #print(f" Inside  Project Role Setup Function  project = {project} , assignee = {assignee} , rule = {pr_rule}")
            res_perm = self.tserver.projects.update_permission(project, [rule])
            #print(f"......update perm result ....{res_perm}")
            if res_perm:
                return True 
            #print(f"Project Permission {pr_rule} assigned to {project} : Asignee - {assignee}")
        except:            
            print(f"ERROR: Default Project Permission for Project Rule Project:  {project} ,Project Rule: {pr_rule} , Asignee - {assignee}")
            return False
         

    def set_ds_role(self,project,assignee,ds_rule):
        # Data source Permission Rule for the group
        try:
            #print(f" Inside  Project Role Setup Function  project = {project} , assignee = {assignee} , rule = {ds_rule}")
            ds_rule = [TSC.PermissionsRule(grantee=assignee, capabilities=ds_rule)]
            new_default_ds_permissions = self.tserver.projects.update_datasource_default_permissions(project, ds_rule)
            if new_default_ds_permissions:
                return True
            #print(f"Project Default data source permission updated successfully for project {project} , Assignee : {assignee}")
        except:
            
            print(f"ERROR: Failed to Update Project Default data source permission for project {project} , Assignee : {assignee}")
            return False
         

    def set_all_users_permissions_none(self,project,default_group,default_rule):
        #Define All user default Rule - to be delete 
        all_user_role = [TSC.PermissionsRule(grantee=default_group, capabilities=default_rule)]
        try:
            #print(f"Inside Default Project None : Group = {default_group}  , default rule = {default_rule}")
            self.tserver.projects.delete_permission(project,all_user_role)
            print(f"Set the All Users group on the Project to None - Default")
        except:
            print(f"ERROR: Failed to Set the All Users group permission to None ")
         

    def grant_role(self,project_name,roletype,roleflag,usr_or_group):  

        print(f"project name passed : {project_name}")
        '''
            Arguments Definition 
            Project Name : Name of Project where the Role need to be setup.
            Role-Type [ explorer,consumer,publisher,creator,leader]
            Role-Flag [INDIVIDUAL,GROUP]
            usr_or_group : Actual group or User
            
        '''
        #print(f" Inside the function definition of grant role ... Project = {project_name} ,RoleType = {roletype} , Role Flag = {roleflag}, User/Group = {usr_or_group} ")
        #Filter the project and get the project object
        #print(f"{project_name} .. {roletype} ... {roleflag}.. {usr_or_group} ..")
        
        try:
            project = self.tserver.projects.filter(name=project_name)[0]
            
            #print("Project found")
            #print(project.name)
             
        except:
            print("Project Not Found")
            return False
             

        #try:
        if roleflag.lower() == "group":
            try:
                assignee = self.tserver.groups.filter(name=usr_or_group)[0]
                #print(f"Group assignee ...{assignee}")
            except:
                print("Group is not present on the Server/Site to Map , Please import the group first")
        else:
            try:   
                assignee = self.tserver.users.filter(name=usr_or_group)[0]
                #print("Individual Assignee : {assignee}")
            except:
                print("Users is not present on the Server/Site, Make sure user is valid user on the server/site and licensed")
            #print(f"assignee ... {assignee}")  ##this can be user or group.
                #print(f"..role flag = {roleflag}")
        #except:
        #        print("unable to find/filter the user")

        #print(f"project name = {project}")
         
   
        #get all users group permission - this will be later set to none -
        default_all_users = 'All Users'
        all_grp = self.tserver.groups.filter(name=default_all_users)[0]


        #Map user specified role to API Role
        if roletype.lower() == "consumer" or roletype.lower() == "explorer" or roletype.lower() == "business":
            #print("Setting Consumer Role ....")
            #print(f"project rule : {project_read_capability}")
            #Consumer/Explorer  - Individual/Groups Gets Read on Project/Explorer on Workbook/Read|Connect on Data Source
            
            #print(f"project rule : {project_read_capability}")
            res_prj = self.set_project_role(project,assignee,project_read_capability)         
            res_wb  = self.set_wb_role(project,assignee,wb_consumer_capabilities)
            res_ds  = self.set_ds_role(project,assignee,ds_consumer_capability)
            if res_prj and res_wb and res_ds :
                return True 
            else:
                print(f"some thing off  ..unable to call the set  dataset role functions ")
                return False
        
            
        elif (roletype.lower()).__contains__("lead")  :
            #Project Leader - Individual or Group gets Project Administrator Role for Project/all sub projects / workbooks etc
            prj_res = self.set_project_role(project,assignee,project_lead_capability )
            return prj_res
            

        elif roletype.lower() == "publish" or roletype.lower() == "publisher" or roletype.lower() == "creator" or roletype.lower() == "developer":
            #Publisher - Individual or Group gets Project Publisher, Workbook Publisher, Data Source read and connect etc
            res_prj = self.set_project_role(project,assignee,project_publish_capability)
            res_wb  = self.set_wb_role(project,assignee,wb_publisher_capabilities)
            res_ds  = self.set_ds_role(project,assignee,ds_publisher_capability)
            
            if res_prj and res_wb and res_ds : 
                return True 
            else:
                return False 
           
        else:
            print(f" Invalid Role Type Specified ...")
            
    def get_workbook_metainfo(self,workbook:str,project:str) ->dict:
        
        find_wb_ds_query = """
        {{
            workbooks(filter: {block}) {{
                name
                luid
                projectName
                owner {{
                    username
                    luid
                }} 
                embeddedDatasources {{
                    name
                      id
                }}      
            }}
        }}
        """.format(block='"'.join(['{name: ', str(workbook)," ,projectName: ",str(project), '}']))
        
        
        try: 
            qres = self.tserver.metadata.query(find_wb_ds_query) 
            print(qres["data"]["workbooks"][0])        
            return qres["data"]["workbooks"][0]
        except:
            qres =  '{}'
            
    def get_workbook_info(self,workbook:str,project:str) ->dict():
        req_option = TSC.RequestOptions()
        req_option.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name,
                                 TSC.RequestOptions.Operator.Equals,workbook))

        req_option.filter.add(TSC.Filter(TSC.RequestOptions.Field.ProjectName,
                                 TSC.RequestOptions.Operator.Equals,project))                                
        
        try:
            matching_workbooks, _ = self.tserver.workbooks.get(req_option)
            if   matching_workbooks[0]:
                 return matching_workbooks[0]
        except:
            return None
    
    def get_workbook_by_luid(self,wb_luid):
        try:
            wbitem = self.tserver.workbooks.get_by_id(wb_luid)
            return wbitem
        except:
            return None


    def get_workbook_by_tag(self,tag):
         return self.tserver.workbooks.filter(tags=tag)

    ##def tag_workbook(self,wb,tag):
    ##   wb.tags.add({tag})
    ##   wb.tags.update({tag})
    ##   self.tserver.workbooks.update(wb)

    def tag_workbooks(self,tagname,wb):
        
                  
        try:  
            wb.tags.add(tagname)
            #print(f" workbook name : {wb.name} , WB_LUID : {wb.id} project name : {wb.project_name}")
            wb.tags.update(tagname)     
            self.tserver.workbooks.update(wb)
            successfully_tag = True
        except:       
            successfully_tag = False

        return successfully_tag
       
     
     
    
    def download_workbook(self,wbitem,filepath=None,noextract=True):
        try:
            self.tserver.workbooks.download(wbitem.id, filepath=filepath, no_extract=noextract)
            return True
        except:
            print(f"Error Downloading the workbook : {wbitem.name}")
            return False

    def delete_workbook(self,wbluid):
        try:
            self.tserver.workbooks.delete(wbluid)
            return True
        except Exception as e:
            print(f"Unable to Delete Workbook: , WB Luid {wbluid} Not exist , exception {e}")
            return False

    def analyze_workbook(self,workbook:str) ->dict:
        #print(f"..inside analyze workbook {workbook}") 
        workbook_lineage = {}
        workbook_lineage_query = """
        {{
        workbooks (filter: {block}) {{
        name
        owner {{
        name
        }}
        projectName 
        updatedAt
        dashboards {{
        name
        }}
        
        upstreamDatasources {{
        name
        upstreamDatabases {{
            name
            connectionType
        }}
        }}
        embeddedDatasources {{
        name
        upstreamDatabases {{
            name
            connectionType
        }}
        }}
        
        containsUnsupportedCustomSql
        
        sheets {{
        
        name
        sheetFieldInstances {{
            name
            ... on CalculatedField {{
            formula
            
            }}
        }}
        
        
        }}
        }}
    
        }} """.format(block='"'.join(['{name: ', str(workbook), '}']))
        try:
            qres = self.tserver.metadata.query(workbook_lineage_query)
        except:
            workbook_lineage = {}
            error = f"Possible Incorrect Workbook Name - Please Provide Exact workbook name as it appear"
            tabLogger.error(error)

         
        df = pd.DataFrame(qres)
        workbook_lineage = {}
        workbook_lineage['workbook_name'] = df['data']['workbooks'][0]['name']
        workbook_lineage['workbook_owner'] = df['data']['workbooks'][0]['owner']['name']
        workbook_lineage['workbook_project'] = df['data']['workbooks'][0]['projectName']
        workbook_lineage['workbook_updated_at'] = df['data']['workbooks'][0]['updatedAt']

        dashboards = []
        for i in range(len(df['data']['workbooks'][0]['dashboards'])):
            dashboards.append(df['data']['workbooks'][0]['dashboards'][i]['name']) 
            i= i+1
        workbook_lineage['dashboards'] = dashboards
        
        datasources_l = []
        datasources_d = {}
        
        for item in df['data']['workbooks'][0]['embeddedDatasources']:
            datasources_d['dsname'] = item['name']
            for database in item['upstreamDatabases']:
                datasources_d['conn_name']=  database['name']
                datasources_d['conn_type'] = database['connectionType']
            
            datasources_l.append(datasources_d)
        
        workbook_lineage['datasources'] =  datasources_l
        sheets = []
        sheet_fields = {}
        for i in range(len(df['data']['workbooks'][0]['sheets'])):
            
            sheet_name = df['data']['workbooks'][0]['sheets'][i]['name'] 
            sheets.append(sheet_name)
            fields =[]
            for s in range(len(df['data']['workbooks'][0]['sheets'][i]['sheetFieldInstances'])):
                fields.append(df['data']['workbooks'][0]['sheets'][i]['sheetFieldInstances'][s])
            sheet_fields[sheet_name] = fields
        #sheet_fields['sheets'] = sheets   
        workbook_lineage['sheets'] = sheets
        workbook_lineage['fields'] = sheet_fields
        #print(f"length of data returned : {len(workbook_lineage['workbook_name'])}")
        return workbook_lineage

    def executeflow(self,flowname:str):
        all_flow_items, pagination_item = self.tserver.flows.get()
        #job_finish codes: -1 for pending/in progress, 0 for success, 1 for error or 2 for cancelled
        
        flowfound = False
        jobstatus = ["Success", "Failed", "Cancelled","Pending"]
        jobid = -99
        for flow in all_flow_items:
            if flow.name == flowname:
                print('Attempting to Running Flow', flow.name, 'Now')
                # run the flow and get the JobItem
                try:
                    job = self.tserver.flows.refresh(flow)
                
                    jobid = int(self.tserver.jobs.get_by_id(job.id).finish_code)
                    print(f"job run code {jobstatus[jobid]}")
                    flowfound = True
                except:
                    print("Prep Require Data Management Add on licensing to Run....")
                break
            else:
                continue
        if flowfound:
                return  jobstatus[jobid]
        else:
            return  "Flow Not Found" 
            
class ParseAndValidateUserQuery:

    def get_query_dict(self,uquery:str)->dict:
        parts = re.split(r"\s*(\w+)=", uquery)
        print(parts)
        uquery_dict = dict(zip(parts[1::2], parts[2::2]))
        if "server" not in uquery_dict.keys():
            uquery_dict['server']='DEFAULT'
            uquery_dict['site']='DEFAULT'
            #print(f"1.get_query_dict : Set server to default as no server provided ..")
        if "site" not in uquery_dict.keys():
            uquery_dict['site']='selfservice'
            #print(f"2.get_query_dict: Set site to default as no site provided ..")
        uquery_dict['cmd'] = uquery_dict['cmd'].lower()
        return uquery_dict
        #dict(zip(parts[1::2], parts[2::2]))

    def is_valid_command(self,ucommand:str)->bool:
        if ucommand in valid_user_commands:
            #print(f"1.is_valid_command : command specified valid...")
            return True 
        else:
            #print(f"2.is_valid_command: command specified Invalid...")
            return False 
    
    def get_user_dialog_data(self,body) ->dict:
        user_query_kiv_str = {}
        submission = body["submission"]
        #print(f" ....submission ....{submission}")
        #print(f" .....body ...{body}")
        #print(f" .....callback/command ...{body['callback_id']}")
        
        user_query_kiv_str['cmd'] = body['callback_id']
        user_query_kiv_str['server_name'] = submission['server_name']
        user_query_kiv_str['site_name'] = submission['site_name']

        if  user_query_kiv_str['cmd'] == "create-project":
            user_query_kiv_str['project_name'] = submission['project_name']
            user_query_kiv_str['project_mode'] = submission['project_mode']
        elif user_query_kiv_str['cmd'] == "import-group":
            user_query_kiv_str['group_name'] = submission['group_name']
            user_query_kiv_str['role_name'] = submission['role_name']
        elif user_query_kiv_str['cmd'] == "grant-role":
            user_query_kiv_str['project_name'] = submission['project_name']
            user_query_kiv_str['group_name'] = submission['group_name']
            user_query_kiv_str['role_name'] = submission['role_name']
        elif user_query_kiv_str['cmd'] == "schedule-flow":
            user_query_kiv_str['flow_name'] = submission['flow_name']
            user_query_kiv_str['schedule_name'] = submission['schedule_name']

        #print(f"1.get_user_dialog_data.......{user_query_kiv_str}")
        return user_query_kiv_str

class TableauAppExceptions(Exception):

    def __init__(self,message,error_code):
        super().__init__(message)
        self.error_code = error_code


class UtilityClass:

    def generate_workbook_lineage_file(self,workbook_lineage,file_format="html"):
    #print(f"....inside func ... {workbook_lineage['workbook_name']}")
        loader = FileSystemLoader(searchpath="templates")
        environment = Environment(loader=loader)
        template_file = environment.get_template("wb_lineage_template.jinja")
        result_file = f"data/workbookinfo-{workbook_lineage['workbook_name']}"
        result_file = result_file.replace(" ","")
        result_file_html = result_file+".html"
        result_file_pdf = result_file+".pdf"

        with open(result_file_html, mode="w", encoding="utf-8") as result:
            result.write(template_file.render(workbook_lineage=workbook_lineage))
        if file_format =="pdf":
                
                try:
                    pdfkit.from_file(result_file_html,result_file_pdf) 
                    return result_file_pdf 
                except:
                    return result_file_pdf
                      
        return result_file_html     