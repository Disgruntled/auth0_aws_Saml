function (user, context, callback) {

/*
You must do your user to role mapping in a rule. you can do them all in one giant rule, or do a rule per user or role or whatever you like to taste

In the below exampled, user "sample.user@yourDomain.com" is getting the role we specify in the AWS,
*/
    user.awsRole = 'ARN:AWS_ROLE_THAT_YOU_WANT_TO_GIVE_TO_USER,ARN:SAML_PROVIDER_ARN_TO_BE_REPLACED';
    user.awsRoleSession = user.name;
    
    if (user.name === "sample.user@yourDomain.com")
        {
    context.samlConfiguration.mappings = {
      'https://aws.amazon.com/SAML/Attributes/Role': 'awsRole',
      'https://aws.amazon.com/SAML/Attributes/RoleSessionName': 'awsRoleSession'
    };
  
    callback(null, user, context);
        }
  
  }