# 🚀 ECS Service Refresh Automation

## 📜 Overview

The **ECS Service Refresh Automation** project automates the refresh of Amazon ECS services in response to upcoming infrastructure update notifications from AWS. By streamlining this process, it ensures services remain up-to-date and performant, minimizing the manual effort.

---

## 🌟 Features

- **Event Monitoring**: Automatically fetches AWS Health events for ECS task patching retirement.
- **Multi-Region Support**: Scans all AWS regions to identify affected ECS services.
- **CloudWatch Management**: Disables alarms before service refresh and re-enables them post-stabilization.
- **Slack Notifications**: Sends real-time updates about the refresh status directly to your Slack channel.
- **Flexible Execution**: Can be triggered on-demand or through scheduled GitHub Actions.

---

## 🔧 Prerequisites
Before running this project, ensure you have:

- An **AWS account** with permissions for ECS, CloudWatch, and Health APIs.
- A **Slack account** with a webhook URL for notifications.
- **Python 3.x** installed (if running locally).
- Required Python packages: `boto3`, `requests`.

## 🛠 Installation
1. **Clone the repository**:
_git clone https://github.com/yourusername/ecs-service-refresh-automation.git_


# 🚀 Usage

Running the Script

**Execute the script manually using:**
_python python_scripts/ecs_task_auto_retirement.py_


# GitHub Actions Workflow

This project includes a GitHub Actions workflow for automatic service refresh every 7 days. You can also trigger it manually.
Setup Secrets: Configure the following GitHub repository secrets:
**AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
SLACK_WEBHOOK_URL**
The workflow is defined in .github/workflows/ecs_task_retirement.yml

# 🧩 How It Works

**Fetch Notifications:** Retrieves upcoming ECS task patching retirement events from AWS Health.
**Identify Affected Services:** Scans all regions to find ECS services that need updates.
**Manage Alarms:** Disables relevant CloudWatch alarms before refreshing services.
**Service Refresh:** Refreshes ECS services and waits for stabilization.
**Re-enable Alarms:** Once stabilized, re-enables alarms and sends Slack notifications.

# 💡 Contributing
Contributions are welcome! If you have suggestions or find bugs, feel free to open an issue or submit a pull request. Let's enhance this automation together!
