import glob
import json
import os
import subprocess
import yaml

with open('config.yml', 'r') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

attachmentPath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'])

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

    dictResource = {
        'listResource': listResource
    }

    with open(os.path.join(attachmentPath, 'GetResourceListOutput.json'), 'w', encoding = 'utf-8') as f:
        json.dump(dictResource, f, indent = 4, ensure_ascii = False)

    return

'''
def getMax3Element(listInput):
    listOutput = listInput

    if len(listInput) > 3:
        middleIndex = len(listInput) // 2
        listOutput = [listInput[0], listInput[middleIndex], listInput[-1]]

    return listOutput
'''

def getMax2Element(listInput):
    listOutput = listInput

    if len(listInput) > 2:
        listOutput = [listInput[0], listInput[-1]]

    return listOutput

def getPlanTimeCatchPropertyPair(dictInput):
    with open(os.path.join(attachmentPath, 'GetPairablePropertyOutput.json'), 'r', encoding = 'utf-8') as f:
        dictPairableProperty = json.load(f)['dictPairableProperty']

    listPairableProperty = []

    for pairableProperty, tupleMetadata in dictPairableProperty.items():
        propertyType = tupleMetadata[0]
        bRequired = tupleMetadata[1]
        bDefault = tupleMetadata[2]
        listPossibleValue = tupleMetadata[3]
        
        if (not bRequired and not bDefault) or (propertyType == 'TypeString' and len(listPossibleValue) > 1) or propertyType == 'TypeBool':
            listPairableProperty.append(pairableProperty)

    listAllPairedProperty = []

    for i in range(len(listPairableProperty)):
        property0 = listPairableProperty[i]
        listPossibleValue0 = [None]
        listPossibleValue = dictPairableProperty[property0][3]

        if len(listPossibleValue) > 0:
            listPossibleValue0 = getMax2Element(listPossibleValue)

        for j in range(i + 1, len(listPairableProperty)):
            property1 = listPairableProperty[j]
            listPossibleValue1 = [None]
            listPossibleValue = dictPairableProperty[property1][3]

            if len(listPossibleValue) > 0:
                listPossibleValue1 = getMax2Element(listPossibleValue)

            for value0 in listPossibleValue0:
                for value1 in listPossibleValue1:
                    listAllPairedProperty.append(
                        {
                            'property0': property0,
                            'value0': value0,
                            'property1': property1,
                            'value1': value1
                        }
                    )

    dictPairedProperty = {
        'listPlanTimeCatchPropertyPair': listAllPairedProperty
    }

    with open(os.path.join(attachmentPath, 'GetPlanTimeCatchPropertyPairOutput.json'), 'w', encoding = 'utf-8') as f:
        json.dump(dictPairedProperty, f, indent = 4, ensure_ascii = False)

    return
