# Auth0 Ready AWS STS AssumeRole by SAML client

A really basic script which is a modification of some AWS code to allow you to do FBL login to Auth0, receive your SAML assertion, and then STSASSUMEROLE by SAML to get an Access Key/Secret Access key to allow you use the AWS API/CLI.

This code is incredibly barebones and doesn't perform basic things like error checking, and if something is not exactly as it was in my test environment it will probably explode. This was written against python2 and I am not proud of that, that's just how AWS provided their skeleton code and I have not found the time to update it to python3 yet.

The code is fairly heavily commented, and I would sugget a read of it to help you get a grasp on it.

While you could tweak this to work with other FBL SAML IDPs, this has alot of enhancements to work out of the box and "as is" with auth0 FBL SAML.

Two flavours of this script are provided, samlapi_formauth.py for python2 and samlap_formauth3.py for python3.

## Invocation

with the environment setup and the requirements installed you may simply invoke the script as itself without arguments for it to run

Python 2:

```bash
samlapi_formauth.py
```

Python 3:

```bash
samlapi_formauth3.py
```

## Getting a console session from the AWS credentials

The main repo for this script has moved here: https://github.com/Disgruntled/awsConsoleSession, but it will remain in this repo as well but not kept in sync.

The script "consoleSession.py" will take the AWS access key/secret access key/session tokena and use them to create a url you can use for the AWS console.

It will attempt to read the access key pair+session token from environment variables, then ~.aws/credentials default profile if nothing exists in the environment.

This can be overriden with arguments -c to specify a credfile, and -p for a profile

--metadata is a neat flag that tries to get credentials from the metadata endpoint. It allows you to use the AWS console as an EC2 instance.

This script is using modified boilerplate code provided by AWS. Not like the samlapi_formauth maincode.

```bash
python3 consoleSession.py -c "path/to/credentials/file" -p "profile"
```

or

```bash
python3 consoleSession.py
```

or

```bash
python3 consoleSession.py --metadata
```

## Customizing to your environment

This version .1 effort does not feature a config file and unfortunately the variables themselves will need to be modified.

## Debugging

This is a science experiment with no built in error checking. But to that extent, there is only really a few places where it can mess up. Responses from Auth0/AWS are about the jist of it, and debugging should not be complex.

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

see requirements.txt for python2 and requirements3.txt for python3

note urlparse is folded into urllib in python3.

## Pre-Requisite steps

You'll need to create an Auth0 Tenant (free tier works), and you'll need to create a new client(application), and a user database (Connections->Database) filled with a few users, and enable that user database for your Application both in the database window and in the application window.

You'll need to configure the client to be a SAML IDP by enabling  the SAML webapp on the application in Application->Addons

Detailed steps:

https://auth0.com/docs/protocols/saml/saml-idp-generic

https://auth0.com/docs/integrations/aws/sso

## Auth0 Rules

The authorization model for this is set at the auth0 rule model. Each user in your auth0 user pool requires an entry in your auth0 tenants rules to mape them to a list of IAM roles on the accounts that trust your SAML IDP