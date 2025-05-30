import sys
import getpass
import requests
import json
import subprocess
import os

def get_precommit_output(file_path):
    try:
        base_directory = os.path.abspath(file_path)
        resolved_path = os.path.abspath(file_path)

        if not os.path.commonpath([resolved_path, base_directory]) == base_directory:
            raise PermissionError(f"Unauthorized access to file: {resolved_path}")

        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"File not found: {resolved_path}")

        with open(resolved_path, 'r') as file:
            content = file.read()

        email_line = next((line for line in content.splitlines() if "Email:" in line), None)
        user_email = email_line.split(":")[1].strip() if email_line else None
        project_name_line = next((line for line in content.splitlines() if "Project Name:" in line), None)
        project_name = project_name_line.split(":")[1].strip() if project_name_line else None
        print(f"Extracted Project Name: {project_name}")
        return content, user_email, project_name
    except Exception as e:
        return f"Error reading pre-commit output: {str(e)}", None, None

def parse_precommit_output(output):
    hook_results = []
    for line in output.splitlines():
        if ("Passed" in line or "Failed" in line or "Skipped" in line) and "Datadog Metrics Hook" not in line:
            hook_results.append(line.strip())
    return hook_results

def get_git_branch():
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error getting branch name: {e.stderr.strip()}"
    except Exception as e:
        return f"Error getting branch name: {str(e)}"
        
user_name = getpass.getuser()

if len(sys.argv) > 1:
    pre_commit_output_path = sys.argv[1]
else:
    pre_commit_output_path = None

pre_commit_output, user_email, project_name = get_precommit_output(pre_commit_output_path)

pre_commit_results = parse_precommit_output(pre_commit_output)

if not isinstance(pre_commit_results, list):
    pre_commit_results = [pre_commit_results] if pre_commit_results else []

branch_name = get_git_branch()

pre_commit_status = "Success" if "Failed" not in pre_commit_results else "Failed"

detailed_message = f"User Name: {user_name}\nBranch Name: {branch_name}\nProject Name: {project_name}"

detailed_message += "\n\nPre-commit Results:\n\n" + "\n".join(pre_commit_results)

api_gateway_url = "https://3ow8bnjb94.execute-api.eu-west-1.amazonaws.com/pre-commit/webhook"

data = {
    "user_name": user_name,
    "branch_name": branch_name,
    "project_name": project_name,
    "pre_commit_status": pre_commit_status,
    "pre_commit_results": pre_commit_results,
    "message": detailed_message,
    "user_email": user_email
}

if all([data.get("user_name"), data.get("branch_name"), data.get("project_name"), 
        data.get("pre_commit_status"), data.get("pre_commit_results"), data.get("message"), data.get("user_email")]):
    
    headers = {
        'Content-Type': 'application/json',
        'X-PreCommit-Auth': '8VWa8IyzVfApNVAqsbvvHlNkiLcTSHAhM19973LxTlp5Kja5IJQdb12tCUbAiyJEEPMNP3JJOtqeqXgh3I5x1VuMD7GmtpUWIqwqYEE'
    }

    try:
        response = requests.post(api_gateway_url, data=json.dumps(data), headers=headers)

        if response.status_code == 200:
            print("Successfully sent data to AWS API Gateway")
        else:
            print(f"Failed to send data. Status Code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error sending data to API Gateway: {str(e)}")
else:
    print("Data dictionary:", data)
    print("Missing required fields. Data was not sent.")
