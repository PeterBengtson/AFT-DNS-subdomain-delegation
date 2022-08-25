import re
import os

def lambda_handler(data, _context):
    account_id = data['account_id']
    goal = re.split('[,\s]+', data['subdomain_delegations'].strip())
    if goal == ['']:
        goal = []
    print(f"Account: {account_id}")
    print(f"Goal: {goal}")

    domains = data['domains']
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

    for subdomain in subdomains:
        subdomain_fqdn = subdomain['Name']
        subdomain_name, base_domain_fqdn = subdomain_fqdn.split('.', 1)
        parameters = {
            "subdomain_name": subdomain_name,
            "fqdn": base_domain_fqdn
        }
        
        domain = find_domain(base_domain_fqdn, domains)
        if not domain:
            # The domain has been deleted in the Networking account. Delete the delegation too.
            print(f"Domain '{subdomain_fqdn}' has been deleted from the Networking account. Deleting it from account {account_id}.")
            delete.append(parameters)
            continue

        if subdomain_not_in_goal(subdomain_name, base_domain_fqdn, goal):
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


def subdomain_not_in_goal(subdomain_name, base_domain_fqdn, goal):
    for domain_name in goal:
        if f"{subdomain_name}.{base_domain_fqdn}" == domain_name + '.':
            return False
    return True
