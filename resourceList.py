from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import json
import yaml

with open('config.yaml', 'r') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

subscription_id = "<SUBSCRIPTION_ID>"
resource_group = "<RG_NAME>"

credential = DefaultAzureCredential()
client = ResourceManagementClient(credential, subscription_id)

for res in client.resources.list_by_resource_group(resource_group):
    full = client.resources.get_by_id(
        res.id,
        api_version="2023-07-01"
    )
    print(json.dumps(full.as_dict(), indent=2))