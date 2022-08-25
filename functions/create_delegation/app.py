import re
import os
import boto3
import uuid

NETWORKING_ACCOUNT_ID = os.environ.get('NETWORKING_ACCOUNT_ID')

sts_client = boto3.client('sts')


def lambda_handler(data, _context):
    print(data)

    account_id = data['account_id']
    subdomain_name = data['domain_data']['subdomain_name']
    fqdn = data['domain_data']['fqdn']
    domains = data['domains']
    # subdomains = data['subdomains']

    name = f"{subdomain_name}.{fqdn}"
    caller_reference = f"AFT-Delegated:{uuid.uuid4().hex}"

    source_client = get_client('route53', NETWORKING_ACCOUNT_ID, 'us-east-1')
    target_client = get_client('route53', account_id, 'us-east-1')

    print(f"Creating hosted zone {name} in account {account_id}...")
    response = target_client.create_hosted_zone(
        Name=name,
        CallerReference=caller_reference,
    )
    name_servers = response['DelegationSet']['NameServers']
    nameserver_resource_records = [{'Value': ns} for ns in name_servers]

    domain_hosted_zone_id = find_domain(fqdn, domains)['Id']

    print(f"Creating NS records in {fqdn} in Networking account {NETWORKING_ACCOUNT_ID}...")
    response = source_client.change_resource_record_sets(
        HostedZoneId=domain_hosted_zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': name,
                        'Type': 'NS',
                        'TTL': 60,
                        'ResourceRecords': nameserver_resource_records
                    }
                }
            ]
        }
    )
    print(response)


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

