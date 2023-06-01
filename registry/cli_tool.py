import argparse
import requests

# Define the command-line arguments
parser = argparse.ArgumentParser(description="CLI tool to interact with the Namespace Management API")
parser.add_argument("action", choices=["register", "delete", "list"], help="Action to perform (register or delete)")
parser.add_argument("--prefix", help="Namespace prefix")
parser.add_argument("--pubkey", help="Public key for registering a namespace (required for 'register' action)")
args = parser.parse_args()
print(args)
# Define the base API URL
api_base_url = "http://localhost:5001/"

# Perform the specified action
if args.action == "register":
    if not args.pubkey:
        print("Error: --pubkey is required for registering a namespace")
    else:
        response = requests.post(f"{api_base_url}/namespace/{args.prefix}", data={"pubkey": args.pubkey})
        if response.status_code == 201:
            print("Namespace registered successfully.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
elif args.action == "delete":
    response = requests.delete(f"{api_base_url}/{args.prefix}")
    if response.status_code == 200:
        print("Namespace deleted successfully.")
    else:
        print(f"Error: {response.status_code} - {response.text}")
elif args.action == "list":
    response = requests.get(f"{api_base_url}/namespaces")
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.status_code} - {response.text}")