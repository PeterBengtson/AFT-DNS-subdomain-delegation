import os
import boto3

NETWORKING_ACCOUNT_ID = os.environ.get('NETWORKING_ACCOUNT_ID')

sts_client = boto3.client('sts')


def lambda_handler(data, _context):
    print(data)

    account_id = data['account_id']
    subdomain_name = data['domain_data']['subdomain_name']
    fqdn = data['domain_data']['fqdn']
    domains = data['domains']
    subdomains = data['subdomains']

    source_client = get_client('route53', NETWORKING_ACCOUNT_ID, 'us-east-1')
    target_client = get_client('route53', account_id, 'us-east-1')

    name = f"{subdomain_name}.{fqdn}"
    subdomain_hosted_zone_id = subdomains[name]
    nameserver_resource_records = find_nameserver_records(target_client, subdomain_hosted_zone_id)

    print(f"Updating NS records in {fqdn} in Networking account {NETWORKING_ACCOUNT_ID}...")
    domain_hosted_zone_id = domains[fqdn]
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


def find_nameserver_records(client, hosted_zone_id):
    resource_record_sets = get_ns_records(client, hosted_zone_id)
    for record_set in resource_record_sets:
        if record_set['Type'] == 'NS':
            return record_set['ResourceRecords']
    return False


def get_ns_records(client, hosted_zone_id):
    response = client.list_resource_record_sets(
        HostedZoneId=hosted_zone_id
    )
    resource_record_sets = response['ResourceRecordSets']
    while response['IsTruncated']:
        response = client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=response['NextRecordName'],
            StartRecordType=response['NextRecordType'],
            StartRecordIdentifier=response['NextRecordIdentifier']
        )
        resource_record_sets.extend(response['ResourceRecordSets'])
    return resource_record_sets


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

