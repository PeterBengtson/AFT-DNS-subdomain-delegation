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

    route53 = get_client('route53', NETWORKING_ACCOUNT_ID, 'us-east-1')

    zones = []
    marker = None
    while True:
        response = route53.list_hosted_zones(Marker=marker)
        zones += response['HostedZones']
        if not response['IsTruncated']:
            break
        marker = response['NextMarker']

    return zones
    

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
