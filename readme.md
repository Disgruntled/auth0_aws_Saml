# Auth0 Ready AWS STS AssumeRole by SAML client

A really basic script which is a modification of some AWS code to allow you to do FBL login to Auth0, receive your SAML assertion, and then STSASSUMEROLE by SAML to get an Access Key/Secret Access key to allow you use the AWS API/CLI.

This code is incredibly barebones and doesn't perform basic things like error checking, and if something is not exactly as it was in my test environment it will probably explode. This was written against python2 and I am not proud of that, that's just how AWS provided their skeleton code and I have not found the time to update it to python3 yet.

The code is fairly heavily commented, and I would sugget a read of it to help you get a grasp on it.

While you could tweak this to work with other FBL SAML IDPs, this has alot of enhancements to work out of the box and "as is" with auth0 FBL SAML.

## Invocation

Simply call the script with your python 2 executable after all dependencies have been resolved.


## Dependencies

see requirements.tst

## Auth0 Rules

The authorization model fort this is set at the auth0 rule model. Each user in your auth0 user pool requires an entry in your auth0 tenants rules to mape them to a list of IAM roles on the accounts that trust your SAML IDP

You could do one rule per user, or one 

