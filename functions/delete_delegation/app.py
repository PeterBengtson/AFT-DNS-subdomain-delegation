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

    name = f"{subdomain_name}.{fqdn}"
    nameserver_resource_records = find_nameserver_records(find_domain(name, subdomains))
    subdomain_hosted_zone_id = find_domain(name, subdomains)['Id']
    domain_hosted_zone_id = find_domain(fqdn, domains)['Id']

    target_client = get_client('route53', account_id, 'us-east-1')
    print(f"Deleting hosted zone {name} from account {account_id}...")
    response = target_client.delete_hosted_zone(
        Id=subdomain_hosted_zone_id
    )
    print(response)

    source_client = get_client('route53', NETWORKING_ACCOUNT_ID, 'us-east-1')

    print(f"Deleting NS records in {fqdn} in Networking account {NETWORKING_ACCOUNT_ID}...")
    response = source_client.change_resource_record_sets(
        HostedZoneId=domain_hosted_zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'DELETE',
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


def find_nameserver_records(subdomain):
    for record_set in subdomain['ResourceRecordSets']:
        if record_set['Type'] == 'NS':
            return record_set['ResourceRecords']
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

