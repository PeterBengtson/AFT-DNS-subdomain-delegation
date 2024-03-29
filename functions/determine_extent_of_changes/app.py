import re
import os

def lambda_handler(data, _context):
    account_id = data['account_id']
    goal = data['subdomain_delegations']
    goners = data['subdomain_delegations_to_remove']

    print(f"Account: {account_id}")
    print(f"Goal: {goal}")
    print(f"Goners: {goners}")

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

        if subdomains.get(subdomain_fqdn):
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

        if subdomains.get(subdomain_fqdn):
            # The goner domain is delegated to the account. Delete the delegation.
            print(f"Deleting '{subdomain_fqdn}' delegation to account {account_id}.")
            delete.append(parameters)
            continue

    data['create'] = create
    data['update'] = update
    data['delete'] = delete

    return data
