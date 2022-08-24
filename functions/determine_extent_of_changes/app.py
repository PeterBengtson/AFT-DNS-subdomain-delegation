import re

def lambda_handler(data, _context):
    account_id = data['account_id']
    goal = re.split('[,\s]+', data['subdomain_delegations'].strip())
    print(f"Account: {account_id}")
    print(f"Goal: {goal}")

    domains = data['domains']
    subdomains = data['subdomains']

    create = []
    update = []
    delete = []

    for str in goal:
        subdomain_name, base_domain_name = str.strip('.').split('.', 1)
        base_domain_fqdn = base_domain_name + '.'

        domain = find_domain(base_domain_fqdn, domains)
        subdomain = find_domain(base_domain_fqdn, subdomains)

        print("Domain", domain)
        print("Subdomain", subdomain)

        if not domain and not subdomain:
            # This is an error, just ignore: not an existing domain
            continue

        if not domain and subdomain:
            # The domain has been deleted in the Networking account, delete the delegation
            delete.append([subdomain_name, base_domain_fqdn])
            continue

        if domain and not subdomain:
            # The domain exists and has not been delegated
            create.append([subdomain_name, base_domain_fqdn])
            continue

        if domain and subdomain:
            # The domain exists and has a delegation, check and update
            update.append([subdomain_name, base_domain_fqdn])
            continue

    return {
        "create": create,
        "update": update,
        "delete": delete
    }


def find_domain(fqdn, domains):
    for domain in domains:
        if domain['Name'] == fqdn:
            return domain
    return False