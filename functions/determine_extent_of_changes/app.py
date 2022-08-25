import re
import os

def lambda_handler(data, _context):
    account_id = data['account_id']

    goal = re.split('[,\s]+', data['subdomain_delegations'].strip())
    if goal == ['']:
        goal = []

    goners = re.split('[,\s]+', data['subdomain_delegations_to_remove'].strip())
    if goners == ['']:
        goners = []

    print(f"Account: {account_id}")
    print(f"Goal: {goal}")
    print(f"Goners: {goners}")

    # domains = data['domains']
    subdomains = data['subdomains']

    create = []
    update = []
    delete = []

    for domain_name in goal:
        subdomain_fqdn = domain_name + '.'
        subdomain_name, base_domain_fqdn = subdomain_fqdn.split('.', 1)
        parameters = {
            "subdomain_name": subdomain_name,
            "fqdn": base_domain_fqdn
        }

        subdomain = find_domain(subdomain_fqdn, subdomains)
        if subdomain:
            # The domain exists and has been delegated. Check and update if necessary.
            print(f"Updating '{subdomain_fqdn}' delegation in account {account_id}.")
            update.append(parameters)
            continue
        else:
            # The domain exists and has not been delegated. Create a delegation.
            print(f"Delegating '{subdomain_fqdn}' to account {account_id}.")
            create.append(parameters)
            continue

    for goner in goners:
        subdomain_fqdn = goner + '.'
        subdomain_name, base_domain_fqdn = subdomain_fqdn.split('.', 1)
        parameters = {
            "subdomain_name": subdomain_name,
            "fqdn": base_domain_fqdn
        }

        subdomain = find_domain(subdomain_fqdn, subdomains)
        if subdomain:
            # The goner domain is delegated to the account. Delete the delegation.
            print(f"Deleting '{subdomain_fqdn}' delegation to account {account_id}.")
            delete.append(parameters)
            continue

    data['create'] = create
    data['update'] = update
    data['delete'] = delete

    return data


def find_domain(fqdn, domains):
    for domain in domains:
        if domain['Name'] == fqdn:
            return domain
    return False
