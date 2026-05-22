import functools
import os
import yaml

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

def formatMultilineCommand(inputString):
    outputString = inputString.replace('  ', '').strip('\n').replace('\n', '; ')

    return outputString

outputFormatPrompt = functools.partial(
    'Under any circumstances, generate last output in JSON format according to [`{_step}Output` class]({dataStructurePath}).'.format,
    dataStructurePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['code'], 'dataStructure.py')
)

def getRegistration2PortalPropertyFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateEmptyRegistration'
    }

    step = 'GenerateEmptyRegistration'
    stepType = 'generateCode'
    servicePath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'])
    registrationPath = os.path.join(servicePath, 'registration.go')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'path': registrationPath
        },
        'nextStep': 'GenerateEmptyClient'
    }

    step = 'GenerateEmptyClient'
    stepType = 'generateCode'
    clientPath = os.path.join(servicePath, 'client', 'client.go')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'path': clientPath
        },
        'nextStep': 'EditMainServiceClient'
    }

    step = 'EditMainServiceClient'
    stepType = 'copilot'
    mainServicePath = os.path.join(dictConfig['path']['azurerm'], 'internal', 'provider', 'services.go')
    mainClientPath = os.path.join(dictConfig['path']['azurerm'], 'internal', 'clients', 'client.go')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f'Add [service]({registrationPath}) and [client]({clientPath}) to [main service file]({mainServicePath}) and [main client file]({mainClientPath}) respectively if have not done so.Decide whether to add untyped, typed, and framework services based on interfaces of `Registration` structure in [service file]({registrationPath}).'
            }
        ],
        'nextStep': 'PreGenerateSdk'
    }

    step = 'PreGenerateSdk'
    stepType = 'copilot'
    vendorSdkPath = os.path.join(dictConfig['path']['azurerm'], 'vendor', 'github.com', 'hashicorp', 'go-azure-sdk')
    outputSavePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Check if [local Go Azure SDK with exact version]({vendorSdkPath}) of {dictConfig['resource']} exists according to [specification]({dictConfig['specification']}). If not, check if the SDK with exact version exists in [repository](https://github.com/hashicorp/go-azure-sdk/tree/main/resource-manager). If the SDK with exact version exists in the repository, check the SDK package path to be imported. {outputFormatPrompt(_step = step)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'outputSavePath': outputSavePath,
        'nextStep': {
            'sdkExist': {
                'existLocally': 'EditResourceClient',
                'existInRepo': 'GenerateSdkImport',
                'notExist': 'UpdatePandora'
            }
        }
    }

    step = 'UpdatePandora'
    stepType = 'command'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'cwd': dictConfig['path']['pandora'],
            'command': [
                ['git', 'checkout', 'main'],
                ['git', 'fetch', 'upstream'],
                ['git', 'merge', 'upstream/main'],
                ['git', 'push', 'origin', 'main'],
                ['git', 'checkout', '-b', dictConfig["resource"].replace('_', '-')],
                ['git', 'checkout', dictConfig["resource"].replace('_', '-')],
                ['git', 'merge', 'main'],
                ['git', 'submodule', 'init'],
                ['git', 'submodule', 'update']
            ]
        },
        'nextStep': 'GenerateApiVersion'
    }

    step = 'GenerateApiVersion'
    stepType = 'copilot'
    resourceManagerPath = os.path.join(dictConfig['path']['pandora'], 'config', 'resource-manager.hcl')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Add API version in [Pandora resource-manager.hcl]({resourceManagerPath}) based on [specification]({dictConfig['specification']}) if have not done so."
            }
        ],
        'nextStep': 'GenerateApiDefinition'
    }

    step = 'GenerateApiDefinition'
    stepType = 'command'
    workingDirectoryPath = os.path.join(dictConfig['path']['pandora'], 'tools', 'importer-rest-api-specs')
    pandoraServiceName = dictConfig['pandoraServiceName'] if dictConfig['pandoraServiceName'] else dictConfig['serviceName'].replace(' ', '')
    dictEnvironment = {
        'SERVICES': pandoraServiceName
    }
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'cwd': workingDirectoryPath,
            'command': [
                ['make', 'import']
            ],
            'env': dictEnvironment
        },
        'nextStep': 'InitializePandoraDataApi'
    }

    step = 'InitializePandoraDataApi'
    stepType = 'service'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {},
        'nextStep': 'GenerateSdkWithPandora'
    }

    step = 'GenerateSdkWithPandora'
    stepType = 'command'
    workingDirectoryPath = os.path.join(dictConfig['path']['pandora'], 'tools', 'generator-go-sdk')
    dataApiUrl = f"http://localhost:{dictConfig['dataApiPort']}"
    sourceSdkPath = os.path.join(dictConfig['path']['locallyGeneratedSdk'], 'resource-manager', pandoraServiceName.lower())
    destinationSdkPath = os.path.join(dictConfig['path']['sdk'], 'resource-manager')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'cwd': workingDirectoryPath,
            'command': [
                ['go', 'build', '.'],
                ['./generator-go-sdk', 'resource-manager', 'generate', '--output-dir', dictConfig['path']['locallyGeneratedSdk'], '--services', pandoraServiceName, '--data-api', dataApiUrl],
                ['cp', '-r', sourceSdkPath, destinationSdkPath]
            ]
        },
        'nextStep': 'UpdateGoAzureSdk'
    }

    step = 'UpdateGoAzureSdk'
    stepType = 'command'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'cwd': dictConfig['path']['sdk'],
            'command': [
                ['git', 'checkout', 'main'],
                ['git', 'restore', '.'],
                ['git', 'fetch', 'upstream'],
                ['git', 'merge', 'upstream/main'],
                ['git', 'push', 'origin', 'main']
            ]
        },
        'nextStep': 'GenerateReplaceDirective'
    }

    step = 'GenerateReplaceDirective'
    stepType = 'copilot'
    goModPath = os.path.join(dictConfig['path']['azurerm'], 'go.mod')
    outputSavePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Add replace directive in [go.mod file]({goModPath}) for [local Go Azure SDK]({destinationSdkPath}) if have not done so. Now, SDK with exact version exists in [repository](https://github.com/hashicorp/go-azure-sdk/tree/main/resource-manager). Check SDK package path of {dictConfig['resource']} to be imported according to [specification]({dictConfig['specification']}). {outputFormatPrompt(_step = step)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'outputSavePath': outputSavePath,
        'nextStep': 'GenerateSdkImport'
    }

    step = 'GenerateSdkImport'
    stepType = 'generateCode'
    dummyFilePath = os.path.join(servicePath, 'dummy.go')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'path': dummyFilePath
        },
        'nextStep': 'GenerateSdk'
    }

    step = 'GenerateSdk'
    stepType = 'command'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'command': [
                ['go', 'mod', 'tidy'],
                ['go', 'mod', 'vendor'],
                ['rm', dummyFilePath]
            ]
        },
        'nextStep': 'EditResourceClient'
    }

    step = 'EditResourceClient'
    stepType = 'copilot'
    listAttachmentPath = [
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'PreGenerateSdkOutput.json'),
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'GenerateReplaceDirectiveOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Import `sdkPackage` listed in attached files to [client file]({clientPath}) if have not done so. Add {dictConfig['resource']} client in [client file]({clientPath}) if have not done so. The error returned by client initialization should be wrapped with `fmt.Errorf(\"building Resources Client: %+v\", err)`.",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'GetPortalProperty'
    }

    step = 'GetPortalProperty'
    stepType = 'copilot'
    listRule = [
        '1. URI parameters are considered as properties too.',
        '2. Child properties that are present in screenshots should be included.',
        '3. Exclude parent properties.',
        '4. Exclude `Subscription`.'
    ]
    listAttachmentPath = [
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'portal*.png')
    ]
    outputSavePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Get list of {dictConfig['resource']} properties which are present in attached portal screenshots according to [specification]({dictConfig['specification']}) according to the rules: {' '.join(listRule)} {outputFormatPrompt(_step = step)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-opus-4.7',
        'outputSavePath': outputSavePath,
        'nextStep': ''
    }

    return dictStepConfig

def getResourceFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateSchema'
    }

    step = 'GenerateSchema'
    stepType = 'copilot'
    resourceFile = f"{dictConfig['resource']}_resource.go"
    resourcePath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], resourceFile)
    listRule = [
        '1. Generate resource schema and other methods except CRUD.',
        '2. Only the properties listed in attached file should be included.',
        '3. Write typed resource.',
        '4. Apply `Required` behavior to properties according to specification. Otherwise, apply `Optional` behavior.',
        '5. Do not apply `ForceNew`, `ValidateFunc`, and `Sensitive` behaviors to any properties except `name`, `location`, and `resource_group_name`.',
        '6. Apply `MaxItems: 1` to `TypeList` property that corresponds to specification parent properties which are not `array` type.'
    ]
    listAttachmentPath = [
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'GetPortalPropertyOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Create [{resourceFile}]({resourcePath}) based on [specification]({dictConfig['specification']}) accoding to the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'FlattenProperty'
    }

    step = 'FlattenProperty'
    stepType = 'copilot'
    listRule = [
        '1. `TypeList` or `TypeSet` parent property that contains only 1 child property.',
        '2. `TypeList` parent property that has `MaxItem` as `1` and less than 3 child properties.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Flatten child properties in schema of [{resourceFile}]({resourcePath}) if necessary. If the flattened child property name is same as any existing resource name, append the child property name to that of parent. These apply recursively to: {' '.join(listRule)} Carry out any necessary modification after flattening."
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    step = 'GenerateCrudMethod'
    stepType = 'copilot'
    listRule = [
        '1. `expand` method should only be created when assigning more than 1 child property to a Go SDK parent property.',
        '2. Do not expand Go SDK root level `Properties` structure.'
        '2. `flatten` method should only be created to return a Terraform parent property in type of `interface` and more than 1 child property.',
        '3. For `Optional` properties, check if properties are set before assigning to Go SDK structure.',
        '4. For `Optional` `TypeInt` properties, use `metadata.ResourceDiff.GetRawConfig` to check if properties are not null before assigning to Go SDK structure.'
    ]
    listAttachmentPath = [
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'PreGenerateSdkOutput.json'),
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'GenerateReplaceDirectiveOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate CRUD methods in [{resourceFile}]({resourcePath}) according to `sdkPackage` in attached files and rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    return dictStepConfig

def generateFlow():
    dictStepConfig = None

    match dictConfig['flow']:
        case 'registration2PortalProperty':
            dictStepConfig = getRegistration2PortalPropertyFlow()
        case 'resource':
            dictStepConfig = getResourceFlow()

    with open('flowConfig.yml', 'w') as f:
        yaml.dump(dictStepConfig, f)

    return

if __name__ == "__main__":
    generateFlow()