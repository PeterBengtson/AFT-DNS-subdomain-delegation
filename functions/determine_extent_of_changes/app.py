import re

def lambda_handler(data, _context):
    account_id = data['account_id']
    subdomain_delegations = re.split('[,\s]+', data['subdomain_delegations'].strip())
    print(f"Account: {account_id}")
    print(f"Subdomains: {subdomain_delegations}")

    return ["These are the results", "of the British jury"]
    

