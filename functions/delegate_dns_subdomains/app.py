import re
import os
import boto3

NETWORKING_ACCOUNT_ID = os.environ.get('NETWORKING_ACCOUNT_ID')

sts_client = boto3.client('sts')


def lambda_handler(data, _context):
    account_id = data['account_id']
    subdomain_delegations = re.split('[,\s]+', data['subdomain_delegations'].strip())

    print(f"Account: {account_id}")
    print(f"Subdomains: {subdomain_delegations}")
    print(f"Networking account: {NETWORKING_ACCOUNT_ID}")


def find_domain(fqdn, domains):
    for domain in domains:
        if domain['Name'] == fqdn:
            return domain
    return False
    

def get_client(client_type, account_id, region, role='AWSControlTowerExecution'):
    other_session = sts_client.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/{role}",
        RoleSessionName=f"aft_delegate_subdomains_{account_id}"
    )
    access_key = other_session['Credentials']['AccessKeyId']
    secret_key = other_session['Credentials']['SecretAccessKey']
    session_token = other_session['Credentials']['SessionToken']
    return boto3.client(
        client_type,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )

