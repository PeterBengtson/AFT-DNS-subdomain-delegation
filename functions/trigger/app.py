import os
from random import randint
import json
import boto3

step_function_client = boto3.client('stepfunctions')

STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']


def lambda_handler(event, _context):
    print(event)

    message_raw = event['Records'][0]['Sns']['Message']
    message = json.loads(message_raw)

    account_id = message['account_id']
    subdomain_delegations = message.get('subdomain_delegations')
    subdomain_delegations_to_remove = message.get('subdomain_delegations_to_remove')

    message['subdomain_delegations'] = subdomain_delegations if subdomain_delegations else ''
    message['subdomain_delegations_to_remove'] = subdomain_delegations_to_remove if subdomain_delegations_to_remove else ''

    random_number = randint(100000, 999999)
    name = f'delegate-account-{account_id}-subdomains-{random_number}'

    print(f"Starting job {name} with input {message}")

    step_function_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=name,
        input=json.dumps(message)
    )

    return True
