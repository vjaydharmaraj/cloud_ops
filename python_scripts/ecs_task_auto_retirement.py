import boto3
import os
import time
import slack_sdk

ecs_client = boto3.client('ecs')
cloudwatch_client = boto3.client('cloudwatch')
health_client = boto3.client('health')

slack_token = os.getenv("SLACK_API_TOKEN")                    #slack token in repo secrets
channel = "#test-vijay"                                       #test slack channel
slack_client = slack_sdk.WebClient(token=slack_token)

def fetch_recent_events():
    response = health_client.describe_events(
        filter={
            'eventTypeCodes': ['AWS_ECS_TASK_PATCHING_RETIREMENT'],
            'eventStatusCodes': ['upcoming'],
            'services': ['ECS'],
            'startTimes': [
                {
                    'from': (time.time() - 7 * 24 * 3600),
                    'to': time.time()
                }
            ]
        }
    )
    return response.get('events', [])

def fetch_affected_entities(event_arn):
    response = health_client.describe_affected_entities(
        filter={
            'eventArns': [event_arn]
        }
    )
    return response.get('entities', [])

def disable_cloudwatch_alarms(entity_arn):
    metrics = ['CPUUtilization', 'MemoryUtilization', 'UnhealthyHostCount']           
    for metric in metrics:
        alarms = cloudwatch_client.describe_alarms_for_metric(
            MetricName=metric,
            Namespace='AWS/ECS',
            Dimensions=[{'Name': 'ClusterName', 'Value': entity_arn}]
        )
        for alarm in alarms['MetricAlarms']:
            cloudwatch_client.disable_alarm_actions(
                AlarmNames=[alarm['AlarmName']]
            )

def refresh_ecs_service(cluster, service):
    response = ecs_client.update_service(
        cluster=cluster,
        service=service,
        forceNewDeployment=True
    )
    return response

def wait_for_service_stabilization(cluster, service, timeout=300):
    start_time = time.time()
    
    while True:
        response = ecs_client.describe_services(
            cluster=cluster,
            services=[service]
        )
        service_info = response['services'][0]
        
        if service_info['deployments'][0]['rolloutState'] == 'COMPLETED':
            return True
        
        if time.time() - start_time > timeout:
            return False
        
        time.sleep(30)

def reenable_cloudwatch_alarms(entity_arn):
    metrics = ['CPUUtilization', 'MemoryUtilization', 'UnhealthyHostCount']
    for metric in metrics:
        alarms = cloudwatch_client.describe_alarms_for_metric(
            MetricName=metric,
            Namespace='AWS/ECS',
            Dimensions=[{'Name': 'ClusterName', 'Value': entity_arn}]
        )
        for alarm in alarms['MetricAlarms']:
            cloudwatch_client.enable_alarm_actions(
                AlarmNames=[alarm['AlarmName']]
            )

def send_slack_notification(cluster, service, critical=False):
    if critical:
        message = f":warning: ECS Service `{service}` in Cluster `{cluster}` failed to stabilize after a refresh."
        channel = '#test-vijay'
    else:
        message = f"ECS Service `{service}` in Cluster `{cluster}` has been refreshed and is now stable."
        channel = '#test-vijay'
    
    slack_client.chat_postMessage(channel=channel, text=message)


def process_event(event_arn):                                                       #main_method
    affected_entities = fetch_affected_entities(event_arn)
    for entity in affected_entities:
        cluster, service = entity['entityValue'].split('|')

        disable_cloudwatch_alarms(cluster)

        refresh_ecs_service(cluster, service)

        service_stable = wait_for_service_stabilization(cluster, service)

        if service_stable:
            reenable_cloudwatch_alarms(cluster)
            send_slack_notification(cluster, service)
        else:
            send_slack_notification(cluster, service, critical=True)
            break

def fetch_and_process_events():                                
    events = fetch_recent_events()
    for event in events:
        event_arn = event['arn']
        process_event(event_arn)

fetch_and_process_events()
