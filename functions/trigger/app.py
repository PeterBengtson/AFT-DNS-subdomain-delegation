import os
import re
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
    message['subdomain_delegations'] = convert_to_list(message.get('subdomain_delegations'))
    message['subdomain_delegations_to_remove'] = convert_to_list(message.get('subdomain_delegations_to_remove'))

    random_number = randint(100000, 999999)
    name = f'delegate-account-{account_id}-subdomains-{random_number}'

    print(f"Starting job {name} with input {message}")

    step_function_client.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=name,
        input=json.dumps(message)
    )

    return True


def convert_to_list(thing):
    if not thing:
        return []
    list = re.split('[,\s]+', thing.strip())
    if list == ['']:
        list = []
    return list

