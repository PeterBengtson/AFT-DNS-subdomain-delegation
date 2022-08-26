# AFT DNS Subdomain delegation
Allows you to use AFT (Account Factory for Terraform) to declaratively specify subdomain
delegations from a central networking account to individual member accounts in the
following way:

```terraform
module "john-doe-account" {
  source = "./modules/aft-account-request"
  control_tower_parameters = {
    AccountEmail              = "accounts@example.com"
    AccountName               = "JohnDoeAccount"                                
    ManagedOrganizationalUnit = "Sandbox"  
    SSOUserEmail              = "accounts@example.com"
    SSOUserFirstName          = "Admin"
    SSOUserLastName           = "User"
  }

  custom_fields = {
    subdomain_delegations = "foo.example.com, foo.example.io"
    subdomain_delegations_to_remove = "gone.example.io"
  }
}
```
Since there already might be any number of subdomains on different levels in the accounts, 
we cannot just remove everything not explicitly mentioned. Instead, we separate creation and 
deletion lists into two arguments:

`subdomain_delegations` is a list of subdomains that are to be delegated to the account. If
an account in this list already exists, its NS information will be updated in the Networking
account. If it does not exist, a local zone will be created and its NS information used to
set up the delegation from the Networking account.

`subdomain_delegations_to_remove` is a list of subdomains delegations that are to be removed
from the account. If a delegation does not exist, nothing will be done.


## Installation

Deploy this SAM project in the organisation account, in your main region. All that's required
is
```console
sam build
sam deploy --guided
```
Subsequent deploys are done just by `sam build && sam deploy`.

To activate, put the following in your `aft-global-customizations` repo, in `pre-api-helpers.sh`
in the `api_helpers` directory. Substitute the `--topic-arn` value for the SNS topic.

```bash
#!/bin/bash -e
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#

echo "Executing Pre-API Helpers"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Obtaining subdomain delegations for account $ACCOUNT_ID..."
SUBDOMAIN_DELEGATIONS=$(aws ssm get-parameters --names /aft/account-request/custom-fields/subdomain_delegations --query "Parameters[0].Value")
echo "Subdomain delegations: $SUBDOMAIN_DELEGATIONS"

echo "Obtaining subdomain delegations to remove for account $ACCOUNT_ID..."
SUBDOMAIN_DELEGATIONS_TO_REMOVE=$(aws ssm get-parameters --names /aft/account-request/custom-fields/subdomain_delegations_to_remove --query "Parameters[0].Value")
echo "Subdomain delegations to remove: $SUBDOMAIN_DELEGATIONS_TO_REMOVE"

echo "Posting SNS message to configure subdomain delegations for the account $ACCOUNT_ID..."
aws sns publish --topic-arn "arn:aws:sns:xx-xxxx-1:111122223333:aft-subdomain-delegation-topic" \
  --message "{\"account_id\": \"$ACCOUNT_ID\", \"subdomain_delegations\": $SUBDOMAIN_DELEGATIONS, \"subdomain_delegations_to_remove\": $SUBDOMAIN_DELEGATIONS_TO_REMOVE}"
```


## Protecting the settings

You will probably want to include something like the following in an SCP and/or a boundary policy to protect the AFT settings 
from tampering:
```json
{
  "Sid": "DenyAFTCustomFieldsModification",
  "Effect": "Deny",
  "Action": [
    "ssm:DeleteParameter*",
    "ssm:PutParameter"
  ],
  "Resource": "arn:aws:ssm:*:*:parameter/aft/account-request/custom-fields/*",
  "Condition": {
    "ArnNotLike": {
      "aws:PrincipalArn": [
        "arn:aws:iam::*:role/AWSControlTowerExecution",
        "arn:aws:iam::*:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_AWSAdministratorAccess_*",
        "arn:aws:iam::*:role/stacksets-exec-*",
        "arn:aws:iam::*:role/AWSAFTService",
        "arn:aws:iam::*:role/AWSAFTExecution"
      ]
    }
  }
}
```

You can add the following to the same SCP and/or boundary policy to block users of a permission set from using or 
even seeing the values of the SSO parameters in their own accounts. Substitute `DeveloperAccess`
with the name of your own permission set, but keep the prefix and wildcard characters:
```json
{
  "Sid": "DenyAFTCustomFieldsUseAndVisibility",
  "Effect": "Deny",
  "Action": [
    "ssm:DeleteParameter*",
    "ssm:DescribeParameters",
    "ssm:GetParameter*",
    "ssm:PutParameter"
  ],
  "Resource": "arn:aws:ssm:*:*:parameter/aft/account-request/custom-fields/*",
  "Condition": {
    "ArnLike": {
      "aws:PrincipalArn": [
        "arn:aws:iam::*:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_DeveloperAccess_*"
      ]
    }
  }
}
```
