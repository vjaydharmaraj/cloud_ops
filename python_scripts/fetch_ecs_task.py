import boto3
import csv

# Function to list ECS clusters and their services with task counts
def list_clusters(region):
    ecs_client = boto3.client('ecs', region_name=region)
    clusters = ecs_client.list_clusters()['clusterArns']
    
    cluster_details = []
    
    for cluster_arn in clusters:
        # Extract the cluster name from the ARN
        cluster_name = cluster_arn.split('/')[-1]
        
        # Fetch all services in the cluster
        services = ecs_client.list_services(cluster=cluster_arn)['serviceArns']
        service_names = [service_arn.split('/')[-1] for service_arn in services]
        
        for service_arn in services:
            # Get the task count for each service
            service_detail = ecs_client.describe_services(cluster=cluster_arn, services=[service_arn])['services'][0]
            running_count = service_detail['runningCount']
            desired_count = service_detail['desiredCount']
            
            cluster_details.append({
                'Region': region,
                'ClusterName': cluster_name,
                'ServiceName': service_arn.split('/')[-1],
                'RunningTaskCount': running_count,
                'DesiredTaskCount': desired_count
            })
    
    return cluster_details

# Function to fetch ECS clusters from multiple regions
def fetch_cluster_details():
    regions = {
        'EU': 'eu-central-1',  # Example EU region
        'AU': 'ap-southeast-2',  # Example AU region
        'US': 'us-east-1'  # Example US region
    }

    all_cluster_data = []
    
    for region_label, region_code in regions.items():
        print(f"\nFetching ECS Clusters, Services, and Task Counts in {region_label} Region ({region_code}):\n")
        cluster_details = list_clusters(region_code)
        all_cluster_data.extend(cluster_details)
    
    return all_cluster_data

# Function to save the details into a CSV file
def save_to_csv(cluster_data, file_name='ecs_clusters_with_tasks.csv'):
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['Region', 'ClusterName', 'ServiceName', 'RunningTaskCount', 'DesiredTaskCount'])
        
        # Write the cluster and service data
        for cluster in cluster_data:
            writer.writerow([cluster['Region'], cluster['ClusterName'], cluster['ServiceName'], 
                             cluster['RunningTaskCount'], cluster['DesiredTaskCount']])

    print(f"Data saved to {file_name}")

if __name__ == "__main__":
    cluster_data = fetch_cluster_details()
    save_to_csv(cluster_data)
