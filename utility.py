import glob
import json
import os
import subprocess
import yaml

with open('config.yml', 'r') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

def bumpApiVersion(dictInput):
    sdkServicePath = os.path.join(dictConfig['path']['azurerm'], 'vendor', 'github.com', 'hashicorp', 'go-azure-sdk', 'resource-manager', dictConfig['sdkServiceName'])
    listPath = glob.glob(os.path.join(sdkServicePath, '*', '*'))
    listVersionPackage = [i.removeprefix(sdkServicePath) for i in listPath]
    dictCurrentVersion = {}

    for versionPackage in listVersionPackage:
        versionPackage = [i for i in versionPackage.split('/') if i]
        
        if versionPackage[1] in dictCurrentVersion:
            dictCurrentVersion[versionPackage[1]].append(versionPackage[0])
        else:
            dictCurrentVersion[versionPackage[1]] = [versionPackage[0]]

    dictLatestVersion = {}

    if dictConfig['bBumpWithLocallyGeneratedSdk']:
        sdkServicePath = os.path.join(dictConfig['path']['sdk'], 'resource-manager', dictConfig['sdkServiceName'])
        listPath = glob.glob(os.path.join(sdkServicePath, '*', '*'))
        listVersionPackage = [i.removeprefix(sdkServicePath) for i in listPath]

        for versionPackage in listVersionPackage:
            versionPackage = [i for i in versionPackage.split('/') if i]
            
            if versionPackage[1] in dictLatestVersion:
                if versionPackage[0] > dictLatestVersion[versionPackage[1]]:
                    dictLatestVersion[versionPackage[1]] = versionPackage[0]
            else:
                dictLatestVersion[versionPackage[1]] = versionPackage[0]
    else:
        for package, listVersion in dictCurrentVersion.items():
            dictLatestVersion[package] = max(listVersion)

    servicePath = os.path.join(dictConfig['path']['azurerm'], 'internal', 'services')

    for package, listCurrentVersion in dictCurrentVersion.items():
        latestVersion = dictLatestVersion[package]

        for currentVersion in listCurrentVersion:
            subprocess.run(['find', servicePath, '-type', 'f', '-exec', 'sed', '-i', f"s/{dictConfig['sdkServiceName']}\\/{currentVersion}\\/{package}/{dictConfig['sdkServiceName']}\\/{latestVersion}\\/{package}/g", '{}', '+'])

    return

def getResourceList(dictInput):
    result = subprocess.run(
        ['az', 'resource', 'list', '--resource-group', dictConfig['resourceGroupName'], '--query', '[].id', '-o', 'tsv'],
        capture_output = True,
        text = True
    )
    
    listResource = []

    for id in result.stdout.split():
        listResource.append(json.loads(subprocess.run(
            ['az', 'resource', 'show', '--ids', id, '-o', 'json'],
            capture_output = True,
            text = True
        ).stdout))

    outputSavePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'GetResourceListOutput.json')

    with open(outputSavePath, "w", encoding="utf-8") as f:
        json.dump(listResource, f, indent=4, ensure_ascii=False)

    return
