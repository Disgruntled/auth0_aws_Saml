import urllib, json, sys
import requests
import boto3
from os import environ
from os.path import expanduser
import configparser as ConfigParser
import argparse

############################Arg parsing logic##################################

parser = argparse.ArgumentParser(description="Creates an AWS console sign in link from an assumed role")
parser.add_argument('-p',type=str, action="store", dest="profile",help="Profile inside of aws creds file you want used. Defaults to \"default\". If set, env variables are not read.",nargs='?')
parser.add_argument('-c',type=str, action="store", dest="credfile",help="Absolute path to AWS credentials file. If set, env variables are not read.",nargs='?')
parser.add_argument('--metadata', action="store_true", dest="metadata",help="Tries to get credentials from the metadata endpoint (169.254.169.254). if set, only metadata is attempted")
args = parser.parse_args()


if args.profile != None:
    profile = args.profile
else:
    profile = "default"


if args.credfile == None:
    awsconfigfile = '/.aws/credentials'
    home = expanduser("~")
    credentialsfile = home + awsconfigfile
else:
    credentialsfile = args.credfile

#########################End Arg parsing logic##################################


# Step 1: Gather the AWS credentials. First try from environment variables, then look to ~.aws/credentials [default]
#if the environment variables are set, use those. If not, fall back ~.aws/credentials [default]


def getCredsFromEnv():
    url_credentials = {}
    url_credentials['sessionId'] = environ.get('AWS_ACCESS_KEY_ID')
    url_credentials['sessionKey'] = environ.get('AWS_SECRET_ACCESS_KEY')
    url_credentials['sessionToken'] = environ.get('AWS_SESSION_TOKEN')
    json_string_with_temp_credentials = json.dumps(url_credentials)
    return(json_string_with_temp_credentials)



def getCredsFromFile(profile,credentialsfile):
    url_credentials = {}
    config = ConfigParser.RawConfigParser()
    try:
        config.read(credentialsfile)
    except:
        raise("Could not open AWS credentials file")
    url_credentials['sessionId'] = config.get(profile, 'aws_access_key_id')
    url_credentials['sessionKey'] = config.get(profile, 'aws_secret_access_key')
    url_credentials['sessionToken'] = config.get(profile, 'aws_session_token')
    json_string_with_temp_credentials = json.dumps(url_credentials)
    return(json_string_with_temp_credentials)


def getCredsFromMetaData():
    url_credentials = {}
    roleName = requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials/').text
    ec2Creds = json.loads(requests.get("http://169.254.169.254/latest/meta-data/iam/security-credentials/{}".format(roleName)).text)
    url_credentials['sessionId'] = ec2Creds['AccessKeyId']
    url_credentials['sessionKey'] = ec2Creds['SecretAccessKey']
    url_credentials['sessionToken'] = ec2Creds['Token']
    json_string_with_temp_credentials = json.dumps(url_credentials)
    return(json_string_with_temp_credentials)



#Default behavior: if no arguments, first try environment, then try default aws credential file with 'default' profile
if args.credfile == None and args.profile == None and args.metadata == False:
    if environ.get('AWS_ACCESS_KEY_ID') != None:
        json_string_with_temp_credentials = getCredsFromEnv()
    else:
        json_string_with_temp_credentials = getCredsFromFile(profile,credentialsfile)
elif args.metadata == False:
    json_string_with_temp_credentials = getCredsFromFile(profile,credentialsfile)

if args.metadata == True:
    json_string_with_temp_credentials = getCredsFromMetaData()


# Step 2. Make request to AWS federation endpoint to get sign-in token. Construct the parameter string with
# the sign-in action request, a 12-hour session duration, and the JSON document with temporary credentials 
# as parameters.
request_parameters = "?Action=getSigninToken"
request_parameters += "&SessionDuration=43200"
if sys.version_info[0] < 3:
    def quote_plus_function(s):
        return urllib.quote_plus(s)
else:
    def quote_plus_function(s):
        return urllib.parse.quote_plus(s)
request_parameters += "&Session=" + quote_plus_function(json_string_with_temp_credentials)
request_url = "https://signin.aws.amazon.com/federation" + request_parameters
r = requests.get(request_url)
# Returns a JSON document with a single element named SigninToken.
try:
    signin_token = json.loads(r.text)
except:
    raise("Invalid JSON response from AWS Federation Service. Verify your AWS credentials exist and are valid")

# Step 3: Create URL where users can use the sign-in token to sign in to 
# the console. This URL must be used within 15 minutes after the
# sign-in token was issued.
request_parameters = "?Action=login" 
request_parameters += "&Issuer=Example.org" 
request_parameters += "&Destination=" + quote_plus_function("https://console.aws.amazon.com/")
request_parameters += "&SigninToken=" + signin_token["SigninToken"]
request_url = "https://signin.aws.amazon.com/federation" + request_parameters

# Send final URL to stdout
print ("")
print (request_url)
print ("")