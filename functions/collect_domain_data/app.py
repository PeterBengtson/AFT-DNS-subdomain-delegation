import re
import os
import boto3

sts_client = boto3.client('sts')


def lambda_handler(data, _context):
    account_id = data['account_id']
    print(f"Account: {account_id}")

    client = get_client('route53', account_id, 'us-east-1')

    result = {}
    zones = get_zones(client)
    for zone in zones:
        result[zone['Name']] = zone['Id']

    return result


def get_zones(client):
    response = client.list_hosted_zones()
    zones = response['HostedZones']
    while response['IsTruncated']:
        response = client.list_hosted_zones(Marker=response['NextMarker'])
        zones.extend(response['HostedZones'])
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
