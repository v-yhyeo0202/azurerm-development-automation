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
        'firstStep': 'GetPortalProperty'
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
    goAzureSdkPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['go-azure-sdk'])
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Check if [Go Azure SDK]({goAzureSdkPath}) of {dictConfig['resource']} exists according to [specification]({dictConfig['specification']}). If not, check the SDK package path to be imported from [repository](https://github.com/hashicorp/go-azure-sdk/tree/main/resource-manager). {outputFormatPrompt(_step = step)}"
            }
        ],
        'nextStep': {
            'bSdkExist': {
                True: 'EditResourceClient',
                False: 'GenerateSdkImport'
            }
        },
        'bOutput2NextStep': True
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
                ['go', 'mod', 'vendor']
            ]
        },
        'nextStep': 'EditResourceClient'
    }

    step = 'EditResourceClient'
    stepType = 'copilot'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Import SDK package listed in [dummy file]({dummyFilePath}) to [client file]({clientPath}) if have not done so. Add {dictConfig['resource']} client in [client file]({clientPath}) if have not done so. The error returned by client initialization should be wrapped with `fmt.Errorf(\"building Resources Client: %+v\", err)`."
            }
        ],
        'nextStep': ''
    }

    step = 'GetPortalProperty'
    stepType = 'copilot'
    listAttachmentPath = [
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], 'portal*.png')
    ]
    outputSavePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Get list of {dictConfig['resource']} properties which are present in attached portal screenshots according to [specification]({dictConfig['specification']}). Child properties that are present in screenshots should be included. Do not include parent properties. {outputFormatPrompt(_step = step)}",
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
        'firstStep': 'GenerateResourceSchema'
    }

    step = 'GenerateResourceSchema'
    stepType = 'copilot'
    resourceFile = f"{dictConfig['resource']}_resource.go"
    resourcePath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], resourceFile)
    listRule = [
        '1. Generate resource schema and other methods except CRUD.',
        '2. Only the properties listed in attached file should be included.',
        '3. Write typed resource.',
        '4. Decide.',
        '5. Do not apply `ForceNew`, `ValidateFunc`, and `Sensitive` behaviors to any properties except `name`, `location`, and `resource_group_name`.',
        '6. If specification property has `array` parent property (this applies recursively), create the corresponding property as child property under `TypeList` parent property in Terraform schema.'
    ]
    listAttachmentPath = [
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], 'GetPortalPropertyOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Create [{resourceFile}]({resourcePath}) based on [specification]({dictConfig['specification']}) accoding to the following rules: {' '.join(listRule)}",
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
                'prompt': f"Flatten child properties in schema of [{resourceFile}]({resourcePath}). If the flattened child property name is same as any existing resource name, append the child property name to that of parent. These apply recursively to: {' '.join(listRule)} Carry out any necessary modification after flattening."
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'GenerateResourceMethod'
    }

    step = 'GenerateResourceMethod'
    stepType = 'copilot'
    listRule = [
        '1. `expand` method should only be created when assigning more than 1 child property to a Go SDK parent property.',
        '2. `flatten` method should only be created to return a Terraform parent property in type of `interface` and more than 1 child property.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate CRUD methods in [{resourceFile}]({resourcePath}) according to the following rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    '''
    step = 'GenerateService'
    stepType = 'copilot'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': f"{generalPrompt} If [service]({servicePath}) does not exist, generate the service with name {dictConfig['serviceName']}.",
        'nextStep': 'PreGenerateSdk'
    }
    '''

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