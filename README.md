![image](https://github.com/jambesh/tabforslack-app/assets/12127470/80300250-e805-4d96-bb48-39cdf7d09e76)



# tabforslack
Tableau For Slack,allow you to Perform Tableau Operations from Slack on multiple servers and sites without switching between servers and sites.   

### What you can do with the inial version ?
1.	Ability to create project on any server and any site without switching between server and site.
2.	Ability to import ad group to different servers and site without swithching server and site.
3.	Ability to grant role to a project (like Explorer/Publisher/Admin etc) without switching server and site and also without multiple permission selection like switching to project tab/workbook tab/data source tab - Explorer will automaticall grant all require permission at project/workbook/data source level etc.
4.	Analyze workbook any server and site and generate PDF right within the slack to download it for reference, this include the number of dashboards, sheets, fields,calculations etc.
Quick Demo : https://www.youtube.com/watch?v=RNjrGskMw-4
# App Configurations Steps :
1.	Create a Slack App
2.	Download the python app files/env file from github
3.	Configure the Tableau and Slack Environment info in the downloaded config file.
4.	Run and test the App locally or on a dedicated virutal Machine
# Create Slack App :
1.	Navigate to https://api.slack.com/apps
2.	Create a new Slack App and select create from scratch , give it a name like tabforslack or name you like it, select the workspace where you will create the app if you multiple workspace like sandbox/production. then create.
3.	Since our goal is to create the slack app which will run within the company firewall , we don't need a dedicate webserver to run the slack bot we can use SOCKET Mode to run it , to enable socket mode, click on socket mode on the left hand side and then enable socket mode, this will ask the token name to be provided give it a name like socket-app-token and generate . (you can copy the token for later reference, you can always show /copy this info later).
4.	there are 4 sections we need to fill after this with the require info to create our Slack App for Tableau #Slash Command : Click on the Basic information from the left side, then click on the Feature & Functionality and then click Slash Command (Baic Info ->Feature and Functionlity ->Slash Command) Provide a slash command name which you will use it to invoke it from the slack like (/tabforslack or /taboperations or /tabops etc ..) Give a short Description .
   
#Events Subscriptions Basic Informations >App Feature and Functionality -->Event Subscription OR Directly click on the Event Subscription from left . 
##ENABLE EVENTS TURN ON By default it is off. Enable following Events /Subscribe to Bots Events :  

|Event Name | Description | Required Scopre|
| --------- | ----------- | -------------- |
| app_home_opened | User Clicked into Your App Home | None |
| app_mention | Subscribe to only the message events that mention your app or bot | app_mentions:read |
| message.im | A message was posted in a direct message channel | im.history |


 ####  Bots Basic Information - > App Feature and Functionality ->Bots Give your app a name, show online yes , show tab and home yes /turn on.
 ##  Permission/Bot Scope : 
 this is important section as this will determine your app scope . some of the scope needed for advance automations are below.

| Oauth Scope | Description |
| ----------- | ----------- |
| app_mentions:read | View message that directly mention @tabforslack in conversations that the app is in |
| chat:write | Send message as tabforslack |
| commands | Add shortcuts and/or slash commands that people can use | 
| files:write | Upload, edit and delte files as tabforslack |
| im:history | View message and other content in direct messages that tabforslack has been added to |
| im:read |  View basic information about direct message that tabforslack has been added to |
| im:write | Start direct message with people |
| users:read | View People in a workspace |
| users:read.email | View email address of people in a workspace |

*  Once you are done with the configuration above, the next obvious steps is to make it available to use within slack and for that this app need to install on your workspace . Click on install All on your left Navigatiob menu or click on Basic Information and then you have the step 2 install option there, click on Install App to install it to workspace. if your slack has Admin review process , it may go to your admin for review and once they approve it you should be able to search the app and add it to your slack.  
*  Copy following information to be configured into Python . Slack App Name : this is App name that you provided earlier ( eg. tabforslack) Token Name : on your left side menu click on Basic Information - >Scroll down on The right to the App level Token and click on the socket app name to reveal the Token Name. BOT User Token : Click on the OAuth Section of left side menu and then copy the BOT USER TOKEN .  
## Python Config :
Download/Clone the git repo file https://github.com/jambesh/tabforslack-app  this repo has the venv file which has all the python package require to run the app but if you like to build , you can build your own Python Virtual Env Following are the require module need to be install on your virtual env : slack_bolt , tableauserverclient pdfkit.  
###### File Name : Library/Config.yaml :
*  Make changes to the Config file and update the Tableau and Slack Environment Information on the downloaded git repo.  
   Unzip the downloaded repo file, Under the folder slackapp-main folder you will have all the files. Open this folder with VS Studio Code. Under Library ->Open the Config.yaml file.  
*  Modify your Tableau Server Name, Site Name . for each of the tableau environment you have you can tag those environment with name like dev/stg/prd for quick access from the slack instead of the url. The first site on the list will be fefault site to perform operations if the user don't spefy site name. You can also specify the default server , in case you have multipls server to perform operation if user don;t specify any server or site . Specify the User Name/Password that will be use to perform this operation , you can setup a generic user id/password and use that. 3) Domain Name: modify the domain name to match your company name.  
*  Slack setting: specify the copied Slack details like App name, BOT Name, App Token etc .  
*	Slack App Home Page Configuration : if you want to make change to the Slack App Home page with additional information like help/instruction/image/video link - use slackuser dialog configuration json file to modify it. file to modify for the Slack App Home : # slackuserdialog.json #  
## Running the App :
For local testing/trouble shooting, the best option is to do below cd to the downloaded git repo folder after unzip . use the virtual environment by using # source venv/bit/activate # this will run in interactive mode if all goes well
## Testing the App :
In Slack , Search for tabforslack and add the app and this should show the App Home/Message/About . The App home shows the Help/Instruction /demo etc the message section is the majic section , where you can invoke the majic command /tabforslack
type /tabforslack create project and hit enter. this should bring the project creation dialog box .

 ![image](https://github.com/jambesh/tabforslack-app/assets/12127470/d49c618b-a34d-4d9f-bdec-7f41a872eaa5)

![image](https://github.com/jambesh/tabforslack-app/assets/12127470/9bcd261d-89c1-4199-a3df-e549aeeaa580)

 
Fill the info and submit !!! it should shows the message with tableau project create status and the new project url ...!!
## Production Deployment considerations:
Run this app on a dedicate Virtual Machine or Container in nohup background mode.
Toubel Shoot : it has the log module, if you run into issue, enable logging and check what is missing .

## Warning/Notes:
While I used this App in production grade, you can do further customize and add new features as per your need.

## Future Additions:
*  Ability to Audit the performance of the workbook from slack and suggest improvement .   
*  Ability to migrate content from one server to other without leaving slack.  
*  Ability to schedule a tableau Prep Flow using a third party scheduler like cron outside of Tableau (Without Data management Add On).  
