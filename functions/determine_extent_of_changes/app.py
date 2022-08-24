import re
import os

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
        full_subdomain_name = f"{subdomain_name}.{base_domain_fqdn}"

        domain = find_domain(base_domain_fqdn, domains)
        subdomain = find_domain(full_subdomain_name, subdomains)

        print("Domain", domain)
        print("Subdomain", subdomain)

        if not domain and not subdomain:
            # This is an error, just ignore: not an existing domain
            print(f"Error: Domain '{base_domain_name}' not found.")
            continue

        parameters = {
            "subdomain_name": subdomain_name,
            "fqdn": base_domain_fqdn
        }

        if not domain and subdomain:
            # The domain has been deleted in the Networking account. Delete the delegation too.
            print(f"Domain {base_domain_name} has been deleted from the Networking account. Deleting {str} from account {account_id}.")
            delete.append(parameters)
            continue

        if domain and not subdomain:
            # The domain exists and has not been delegated. Create a delegation.
            print(f"Delegating {str} to account {account_id}.")
            create.append(parameters)
            continue

        if domain and subdomain:
            # The domain exists and has been delegated. Check and update if necessary.
            print(f"Updating {str} delegation in account {account_id}.")
            update.append(parameters)
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