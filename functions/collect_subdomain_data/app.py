import re
import boto3


def lambda_handler(data, _context):
    account_id = data['account_id']
    subdomain_delegations = re.split('[,\s]+', data['subdomain_delegations'].strip())
    print(f"Account: {account_id}")
    print(f"Subdomains: {subdomain_delegations}")

    route53 = boto3.client('route53')

    zones = []
    marker = None
    while True:
        response = route53.list_hosted_zones(Marker=marker)
        zones += response['HostedZones']
        if not response['IsTruncated']:
            break
        marker = response['NextMarker']

    return zones
