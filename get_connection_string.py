from azure.identity import DefaultAzureCredential
from azure.mgmt.storage import StorageManagementClient
from dotenv import load_dotenv
import os

load_dotenv()

account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
subscription_id = os.getenv("subscription_id")
resource_group_name = os.getenv("resource_group_name")

credential = DefaultAzureCredential()

storage_client = StorageManagementClient(credential, subscription_id)

storage_accounts = storage_client.storage_accounts.list_by_resource_group(resource_group_name)

storage_account = None
for account in storage_accounts:
    if account.name == account_name:
        storage_account = account
        break

if storage_account is None:
    print("Storage account not found.")
else:
    storage_keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account.name)
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account.name};AccountKey={storage_keys.keys[0].value};EndpointSuffix=core.windows.net"
    print("Storage Account Connection String:", connection_string)