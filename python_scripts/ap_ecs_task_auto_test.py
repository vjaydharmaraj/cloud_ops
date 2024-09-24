import boto3
import time
import requests
from datetime import datetime
import threading

ecs_client = boto3.client('ecs', region_name='ap-southeast-2')
cloudwatch_client = boto3.client('cloudwatch')
health_client = boto3.client('health')

slack_token = ""              #replace the webhook token
channel = "#test-vijay"

def fetch_recent_events():
    response = health_client.describe_events(
        filter={
            'eventTypeCodes': ['AWS_ECS_TASK_PATCHING_RETIREMENT'],
            'eventStatusCodes': ['upcoming'],
            'services': ['ECS']
        }
    )
    return response.get('events', [])

def fetch_affected_entities(event_arn):
    response = health_client.describe_affected_entities(
        filter={
            'eventArns': [event_arn]
        }
    )
    entities = [entity for entity in response.get('entities', []) if 'ap-southeast-2' in entity.get('entityArn', '')]
    if not entities:
        print("No affected entities found.")
    return entities

def check_and_manage_alarms(cluster, service):
    metrics = ['CPUUtilization', 'MemoryUtilization', 'UnhealthyHostCount']
    alarms_found = False

    for metric in metrics:
        alarm_name = f"{cluster}-{service}-ecs-{metric.lower()}-call-alarm"
        alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])

        if alarms['MetricAlarms']:
            alarms_found = True
            print(f"Alarm found for {metric} in {cluster} for service {service}: {alarm_name}")
            
            cloudwatch_client.disable_alarm_actions(AlarmNames=[alarm_name])
            print(f"Alarm {alarm_name} disabled.")
        else:
            print(f"No alarms found for {metric} in {cluster} for service {service}.")

    if not alarms_found:
        print(f"No alarms were found for service {service} in cluster {cluster}. Continuing...\n")

def refresh_ecs_service(cluster, service):
    print(f"Updating service {service} in cluster {cluster}...")
    try:
        start_time = datetime.now()  # Record the time when the refresh starts
        ecs_client.update_service(
            cluster=cluster,
            service=service,
            forceNewDeployment=True
        )
        print(f"Service {service} updated successfully at {start_time.strftime('%Y-%m-%d %H:%M:%S')}.")
    except Exception as e:
        print(f"Error updating service {service}: {e}")
        send_slack_notification(cluster, service, critical=True)

def wait_for_service_stabilization(cluster, service, timeout=200):
    start_time = time.time()
    while True:
        response = ecs_client.describe_services(cluster=cluster, services=[service])
        service_info = response['services'][0]

        if service_info['deployments'][0]['rolloutState'] == 'COMPLETED':
            end_time = datetime.now()
            print(f"Service {service} in cluster {cluster} stabilized at {end_time.strftime('%Y-%m-%d %H:%M:%S')}.")
            return True

        if time.time() - start_time > timeout:
            return False

        time.sleep(30)

def reenable_cloudwatch_alarms(cluster, service):
    metrics = ['CPUUtilization', 'MemoryUtilization', 'UnhealthyHostCount']
    alarms_found = False

    for metric in metrics:
        alarms = cloudwatch_client.describe_alarms_for_metric(
            MetricName=metric,
            Namespace='AWS/ECS',
            Dimensions=[{'Name': 'ClusterName', 'Value': cluster}]
        )
        if alarms['MetricAlarms']:
            alarms_found = True
            for alarm in alarms['MetricAlarms']:
                cloudwatch_client.enable_alarm_actions(
                    AlarmNames=[alarm['AlarmName']]
                )
            print(f"Alarms re-enabled for {metric} in {cluster} for service {service}.")
        else:
            print(f"No alarms found for {metric} in {cluster} for service {service}.")

    if not alarms_found:
        print(f"No alarms were found for service {service} in cluster {cluster}. Continuing...")

def send_slack_notification(cluster, service, critical=False):
    if critical:
        message = f":warning: ECS Service `{service}` in Cluster `{cluster}` failed to stabilize after a refresh."
    else:
        message = f"ECS Service `{service}` in Cluster `{cluster}` has been refreshed and is now stable."

    slack_payload = {
        "channel": channel,
        "text": message
    }

    # Asynchronous request to speed up Slack notifications
    thread = threading.Thread(target=send_slack_message, args=(slack_payload,))
    thread.start()

def send_slack_message(slack_payload):
    try:
        response = requests.post(slack_token, json=slack_payload, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send notification: {e}")

def process_event(event_arn):
    affected_entities = fetch_affected_entities(event_arn)
    if not affected_entities:
        return  # Break the loop if no affected entities are found

    for entity in affected_entities:
        cluster, service = entity['entityValue'].split('|')
        print(f"Processing Cluster: {cluster}, Service: {service}")

        check_and_manage_alarms(cluster, service)

        refresh_ecs_service(cluster, service)

        service_stable = wait_for_service_stabilization(cluster, service)

        if service_stable:
            reenable_cloudwatch_alarms(cluster, service)
            send_slack_notification(cluster, service)
        else:
            send_slack_notification(cluster, service, critical=True)
            break

def fetch_and_process_events():
    events = fetch_recent_events()
    for event in events:
        event_arn = event['arn']
        process_event(event_arn)

if __name__ == "__main__":
    fetch_and_process_events()
