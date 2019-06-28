# Auth0 Ready AWS STS AssumeRole by SAML client

A really basic script which is a modification of some AWS code to allow you to do FBL login to Auth0, receive your SAML assertion, and then STSASSUMEROLE by SAML to get an Access Key/Secret Access key to allow you use the AWS API/CLI.

This code is incredibly barebones and doesn't perform basic things like error checking, and if something is not exactly as it was in my test environment it will probably explode. This was written against python2 and I am not proud of that, that's just how AWS provided their skeleton code and I have not found the time to update it to python3 yet.

The code is fairly heavily commented, and I would sugget a read of it to help you get a grasp on it.

While you could tweak this to work with other FBL SAML IDPs, this has alot of enhancements to work out of the box and "as is" with auth0 FBL SAML.

## Customizing to your environment.

This version .1 effort does not feature a config file and unfortunately the variables themselves will need to be modified.


## Invocation

Simply call the script with your python 2 executable after all dependencies have been resolved.

after that you can then use the "saml" profile as it has been saved to your ~.aws/credentials file.

This can be referenced in your aws SDK, or if using the cli add "--profile saml" to all your one-liners.

## Config File

Recently added capabilities:

Will read from samlapi_formauth.conf to parse a config. Example configuration provided.

The variables are all things you will need to get from auth0, including:

your tenant (auth0 displayname)
your client_id
your auth0 userpool (connection)
username/password
output format/region to your own AWS taste



## Dependencies

see requirements.tst

## Pre-Requisite steps

You'll need to create an Auth0 Tenant (free tier works), and you'll need to create a new client(application), and a user database (Connections->Database) filled with a few users, and enable that user database for your Application both in the database window and in the application window.

You'll need to configure the client to be a SAML IDP by enabling  the SAML webapp on the application in Application->Addons

Detailed steps:

https://auth0.com/docs/protocols/saml/saml-idp-generic

https://auth0.com/docs/integrations/aws/sso

## Auth0 Rules

The authorization model fort this is set at the auth0 rule model. Each user in your auth0 user pool requires an entry in your auth0 tenants rules to mape them to a list of IAM roles on the accounts that trust your SAML IDP

You could do one rule per user, or one 

