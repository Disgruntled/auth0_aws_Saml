#!/usr/bin/python

import sys
import boto.sts
import boto.s3
import requests
import getpass
import ConfigParser
import base64
import logging
import xml.etree.ElementTree as ET
import re
from urlparse import parse_qs
from bs4 import BeautifulSoup
from os.path import expanduser
from urlparse import urlparse, urlunparse

##########################################################################
# Variables

# region: The default AWS region that this script will connect
# to for all API calls
region = 'us-east-1'

# output format: The AWS CLI output format that will be configured in the
# saml profile (affects subsequent CLI calls)
outputformat = 'json'

# awsconfigfile: The file where this script will store the temp
# credentials under the saml profile
# Note you will have to make this file if it does not exist. I have not studied this in depth, but you may need to do make ~/.aws/credentials
# to that extent, I've provided you the "default" credentials file you can place there. you DO NOT need to update the region.

awsconfigfile = '/.aws/credentials'

# SSL certificate verification: Whether or not strict certificate
# verification is done, False should only be used for dev/test
sslverification = True

# idpentryurl: The initial url that starts the authentication process.
# You can get this from your Auth0 Saml Client set up
#this is the LANDING page of auth0, and not the FBL form that is posted to
idpentryurl = 'my_idp_entry_url'


# Uncomment to enable low level debugging
#logging.basicConfig(level=logging.DEBUG)


#the client_id from your auth0 client.
#you can get this from the page about you client . Client ID's are not secrets and can be stored in code/config without further concern


client_id = "My_client_id_from_auth0_that_I_setup_for_saml"



#the connection from auth0
#THis is your userpool connection. This is required for the login action.

connection = "My_Userpool_connection_from_auth0_that_I_put_users_on"


###Tenant. Your auth0 tenant name. This is your username on auth0 (not email!)
tenant = "my_auth0_tenant_that_I_got"


####The actual URL we will be posting or login payload to, after we get our state/csrf set.

idpauthformsubmiturl = "https://"+tenant+".auth0.com/usernamepassword/login"

###This is a user from your Auth0 user store
###Keep in mind this script does not authorize users, its up for you to do that in your auth0 "rules" Section.



username = "sample.user@yourDomain.com"

###Enter a valid password. the script-as is does not support 2fa but it would NOT be difficult to make it support 2fa if you want to plum it in
password = "A_Sample_Credential_battery_stapler"



##########################################################################
##########################################################################
###############################Let' boogie################################
##########################################################################
##########################################################################

# Initiate session handler
# it's mandatory we use a session, auth0 sets a CSRF cookie and we pick it up with this.
session = requests.Session()


#Like a good OAUTH client, Auth0 Set's a STATE parameter, even though we're using SAML and there's already a CSRF token.
#We need to get the state from the IDP entry url and parse it out to use again later.
r = session.get(idpentryurl, allow_redirects=False)
t = r.headers['location']
state = parse_qs(t)['/login?state']

# Programmatically get the SAML assertion
# Opens the initial IdP url and follows all of the HTTP302 redirects, and
# gets the resulting login page
formresponse = session.get(idpentryurl)



# Parse the response and extract all the necessary values
# in order to build a dictionary of all of the form values the IdP expects
formsoup = BeautifulSoup(formresponse.text.decode('utf8'),"html.parser")
payload = {}

for inputtag in formsoup.find_all(re.compile('(INPUT|input)')):
    name = inputtag.get('name','')
    value = inputtag.get('value','')
    if "user" in name.lower():
        #Make an educated guess that this is the right field for the username
        payload[name] = username
    elif "email" in name.lower():
        #Some IdPs also label the username field as 'email'
        payload[name] = username
    elif "pass" in name.lower():
        #Make an educated guess that this is the right field for the password
        payload[name] = password
    else:
        #Simply populate the parameter with the existing value (picks up hidden fields in the login form)
        payload[name] = value

# Debug the parameter payload if needed
# Use with caution since this will print sensitive output to the screen
#print payload

# Some IdPs don't explicitly set a form action, but if one is set we should
# build the idpauthformsubmiturl by combining the scheme and hostname 
# from the entry url with the form action target
# If the action tag doesn't exist, we just stick with the 
# idpauthformsubmiturl above

payload["username"] = username
payload["password"] = password
payload["client_id"] = client_id
payload["connection"] = connection
payload["state"] = state
payload["tenant"] = tenant
payload["protocol"] = "samlp"

# Performs the submission of the IdP login form with the above post data
response = session.post(
    idpauthformsubmiturl, data=payload, verify=False)



# Debug the response if needed
#print (response.text)

# Overwrite and delete the credential variables, just for safety
username = '##############################################'
password = '##############################################'
del username
del password

# Decode the response and extract the SAML assertion
soup = BeautifulSoup(response.text.decode('utf8'),"lxml")
#print(soup)
#print soup.body.find('input', attrs={'name':'wresult'}).get('value')
#print soup.body.find('input', attrs={'name':'wa'}).get('value')
#print soup.body.find('input', attrs={'name':'wctx'}).get('value')

newpayload = {}
newpayload["wresult"] = soup.body.find('input', attrs={'name':'wresult'}).get('value')
newpayload["wa"] = soup.body.find('input', attrs={'name':'wa'}).get('value')
newpayload["wctx"] = soup.body.find('input', attrs={'name':'wctx'}).get('value')

response = session.post("https://"+tenant+".auth0.com/login/callback", data=newpayload, verify=False)

soup = BeautifulSoup(response.text.decode('utf8'),"lxml")

assertion = ''

# Look for the SAMLResponse attribute of the input tag (determined by
# analyzing the debug print lines above)
for inputtag in soup.find_all('input'):
    if(inputtag.get('name') == 'SAMLResponse'):
        #print(inputtag.get('value'))
        assertion = inputtag.get('value')

# Better error handling is required for production use.
#if (assertion == ''):
    #TODO: Insert valid error checking/handling
 #   print('Response did not contain a valid SAML assertion')
 #   sys.exit(0)

# Debug only
# print(base64.b64decode(assertion))

# Parse the returned assertion and extract the authorized roles
awsroles = []

root = ET.fromstring(base64.b64decode(assertion))

for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
    if (saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'):
        for saml2attributevalue in saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
            awsroles.append(saml2attributevalue.text)

# Note the format of the attribute value should be role_arn,principal_arn
# but lots of blogs list it as principal_arn,role_arn so let's reverse
# them if needed
for awsrole in awsroles:
    chunks = awsrole.split(',')
    if'saml-provider' in chunks[0]:
        newawsrole = chunks[1] + ',' + chunks[0]
        index = awsroles.index(awsrole)
        awsroles.insert(index, newawsrole)
        awsroles.remove(awsrole)

# If I have more than one role, ask the user which one they want,
# otherwise just proceed
print("")
if len(awsroles) > 1:
    i = 0
    print("Please choose the role you would like to assume:")
    for awsrole in awsroles:
        print('[', i, ']: ', awsrole.split(',')[0]())
        i += 1

    print("Selection: ")
    selectedroleindex = raw_input()

    # Basic sanity check of input
    if int(selectedroleindex) > (len(awsroles) - 1):
        print('You selected an invalid role index, please try again')
        sys.exit(0)

    role_arn = awsroles[int(selectedroleindex)].split(',')[0]
    principal_arn = awsroles[int(selectedroleindex)].split(',')[1]
else:
    role_arn = awsroles[0].split(',')[0]
    principal_arn = awsroles[0].split(',')[1]

# Use the assertion to get an AWS STS token using Assume Role with SAML
conn = boto.sts.connect_to_region(region)
token = conn.assume_role_with_saml(role_arn, principal_arn, assertion)

# Write the AWS STS token into the AWS credential file
home = expanduser("~")
filename = home + awsconfigfile

# Read in the existing config file
config = ConfigParser.RawConfigParser()
config.read(filename)

# Put the credentials into a saml specific section instead of clobbering
# the default credentials
if not config.has_section('saml'):
    config.add_section('saml')

config.set('saml', 'output', outputformat)
config.set('saml', 'region', region)
config.set('saml', 'aws_access_key_id', token.credentials.access_key)
config.set('saml', 'aws_secret_access_key', token.credentials.secret_key)
config.set('saml', 'aws_session_token', token.credentials.session_token)

# Write the updated config file
with open(filename, 'w+') as configfile:
    config.write(configfile)

# Give the user some basic info as to what has just happened
print('\n\n----------------------------------------------------------------')
print('Your new access key pair has been stored in the AWS configuration file {0} under the saml profile.'.format(filename))
print('Note that it will expire at {0}.'.format(token.credentials.expiration))
print('After this time, you may safely rerun this script to refresh your access key pair.')
print('To use this credential, call the AWS CLI with the --profile option (e.g. aws --profile saml ec2 describe-instances).')
print('----------------------------------------------------------------\n\n')

# Use the AWS STS token to list all of the S3 buckets
s3conn = boto.s3.connect_to_region(region,
                     aws_access_key_id=token.credentials.access_key,
                     aws_secret_access_key=token.credentials.secret_key,
                     security_token=token.credentials.session_token)

