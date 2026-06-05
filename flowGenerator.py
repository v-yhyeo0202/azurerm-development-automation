import functools
import json
import os
import yaml

import flowControl
import stepWrapper

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

def formatMultilineCommand(inputString):
    outputString = inputString.replace('  ', '').strip('\n').replace('\n', '; ')

    return outputString

outputFormatPrompt = functools.partial(
    'Generate output in JSON format according to [`{_step}Output` class]({dataStructurePath}).'.format,
    dataStructurePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['code'], 'dataStructure.py')
)
servicePath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'])
registrationPath = os.path.join(servicePath, 'registration.go')
attachmentPath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'])
vendorSdkPath = os.path.join(dictConfig['path']['azurerm'], 'vendor', 'github.com', 'hashicorp', 'go-azure-sdk')
pandoraServiceName = dictConfig['pandoraServiceName'] if dictConfig['pandoraServiceName'] else dictConfig['serviceName'].replace(' ', '')
resourceFile = f"{dictConfig['resource']}_resource.go"
resourcePath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], resourceFile)
testFile = f"{dictConfig['resource']}_resource_test.go"
testPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], testFile)
pascalCaseResource = ''.join([i.capitalize() for i in dictConfig['resource'].split('_')])
validateFuncTestFile = f"{dictConfig['resource']}_resource_vf_test.go"
validateFuncTestPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], validateFuncTestFile)
maxItemsTestFile = f"{dictConfig['resource']}_resource_mi_test.go"
maxItemsTestPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], maxItemsTestFile)
forceNewTestFile = f"{dictConfig['resource']}_resource_fn_test.go"
forceNewTestPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], forceNewTestFile)

listCheckPropertyRule = [
    '1. For properties with schema returned by methods, check the methods too. This applies recursively.'
]
checkPropertyRule = f"Additional rules: {' '.join(listCheckPropertyRule)}"

listTestRule = [
    '1. Always use `Standard_F1als_v7` size when virtual machine is used.',
    '2. Do not run the test.'
]
testRule = f"Additional rules: {' '.join(listTestRule)}"

def getAiAssistedDevelopment2PortalPropertyFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'RemoveAiAssistedDevelopment'
    }

    step = 'RemoveAiAssistedDevelopment'
    stepType = 'command'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'cwd': dictConfig['path']['aiAssistedDevelopment'],
            'command': [
                ['./install-copilot-setup.sh', '-repo-directory', dictConfig['path']['azurerm'], '-clean']
            ]
        },
        'nextStep': 'UpdateAiAssistedDevelopment'
    }

    step = 'UpdateAiAssistedDevelopment'
    stepType = 'command'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'cwd': dictConfig['path']['home'],
            'command': [
                ['rm', '-rf', dictConfig['path']['aiAssistedDevelopment']],
                ['curl', '-L', '-o', '/tmp/terraform-azurerm-ai-installer.tar.gz', 'https://github.com/WodansSon/terraform-azurerm-ai-assisted-development/releases/latest/download/terraform-azurerm-ai-installer.tar.gz'],
                ['mkdir', '-p', dictConfig['path']['aiAssistedDevelopment']],
                ['tar', '-xzf', '/tmp/terraform-azurerm-ai-installer.tar.gz', '-C', dictConfig['path']['aiAssistedDevelopment'], '--strip-components=1']
            ]
        },
        'nextStep': 'RunAiAssistedDevelopment'
    }

    step = 'RunAiAssistedDevelopment'
    stepType = 'command'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'cwd': dictConfig['path']['aiAssistedDevelopment'],
            'command': [
                ['./install-copilot-setup.sh', '-repo-directory', dictConfig['path']['azurerm']]
            ]
        },
        'nextStep': 'GenerateEmptyRegistration'
    }

    step = 'GenerateEmptyRegistration'
    stepType = 'generateCode'
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
    outputSavePath = os.path.join(attachmentPath, f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Check if [local Go Azure SDK with exact version]({vendorSdkPath}) of {dictConfig['resource']} exists according to [specification]({dictConfig['specification']}). If not, check if the SDK with exact version exists in [repository](https://github.com/hashicorp/go-azure-sdk/tree/main/resource-manager). If the SDK with exact version exists in the repository, check the SDK package path to be imported. Do not consider content in {dictConfig['path']['sdk']} and {dictConfig['path']['locallyGeneratedSdk']}."
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'model': 'claude-opus-4.8',
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

    stepWrapper.addService(dictStepConfig, 'InitializePandoraDataApi', 'GenerateSdkWithPandora')

    step = 'GenerateSdkWithPandora'
    stepType = 'command'
    workingDirectoryPath = os.path.join(dictConfig['path']['pandora'], 'tools', 'generator-go-sdk')
    dataApiUrl = f"http://localhost:{dictConfig['port']['dataApi']}"
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
    outputSavePath = os.path.join(attachmentPath, f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Add replace directive in [go.mod file]({goModPath}) for [local Go Azure SDK]({destinationSdkPath}) if have not done so. Now, SDK with exact version exists in [repository](https://github.com/hashicorp/go-azure-sdk/tree/main/resource-manager). Check SDK package path of {dictConfig['resource']} to be imported according to [specification]({dictConfig['specification']})."
            },
            {
                'prompt': outputFormatPrompt(_step = step)
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
    clientResource = dictConfig['clientResource'] if dictConfig['clientResource'] else pascalCaseResource
    listAttachmentPath = [
        os.path.join(attachmentPath, 'PreGenerateSdkOutput.json'),
        os.path.join(attachmentPath, 'GenerateReplaceDirectiveOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Import `sdkPackage` listed in attached files to [client file]({clientPath}) if have not done so. Add {dictConfig['resource']} client in [client file]({clientPath}) if have not done so. The error returned by client initialization should be wrapped with `fmt.Errorf(\"building {clientResource}s Client: %+v\", err)`.",
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
        '4. Exclude `Subscription`.',
        '5. If there is no attached file, skip this step.'
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'portal*.png')
    ]
    outputSavePath = os.path.join(attachmentPath, f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Get list of {dictConfig['resource']} properties which are present in attached portal screenshots according to [specification]({dictConfig['specification']}) and the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'model': 'claude-opus-4.8',
        'outputSavePath': outputSavePath,
        'nextStep': ''
    }

    return dictStepConfig

def getSchemaFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateSchema'
    }

    step = 'GenerateSchema'
    stepType = 'copilot'
    commonSchemaPath = os.path.join(dictConfig['path']['azurerm'], 'vendor', 'github.com', 'hashicorp', 'go-azure-helpers', 'resourcemanager', 'commonschema')
    
    listRule = [
        '1. Generate resource schema (`Arguments`), `Attributes` (can be empty if not applicable), `ModelObject`, `ResourceType`, and `IDValidationFunc` methods in sequence and other relevant codes.',
        '2. Generate empty CRUD methods.',
        '3. Only the properties listed in attached file should be included.',
        '4. Generate typed resource.',
        '5. Apply `sdk.Resource` interface.',
        '6. Do not apply any behaviors except `Type` and `Elem` to all properties.',
        f'7. Apply [common schema]({commonSchemaPath}) to `resource_group_name`, `location`, `tags`, `identity`, and `zone` if they exist in attached file.',
        '8. Model structure name should contain `Model` suffix, not `ResourceModel` suffix.',
        f'9. Add resource model to [service registration file]({registrationPath}).'
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'GetPortalPropertyOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Create [{resourceFile}]({resourcePath}) according to [specification]({dictConfig['specification']}) and the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'GenerateBehavior'
    }

    step = 'GenerateBehavior'
    stepType = 'copilot'
    updatePath = os.path.join(vendorSdkPath, pandoraServiceName.lower(), '*', '*', 'method*update.go')
    validationPath = os.path.join(dictConfig['path']['azurerm'], 'vendor', 'github.com', 'terraform-provider-azurerm', 'internal', 'tf', 'validation')
    listRule = [
        '1. Apply `Required` behavior to properties according to specification. Otherwise, apply `Optional` behavior.',
        f'2. Apply `ForceNew` behavior to properties which are absent from [`Update` method argument of Go Azure SDK]({updatePath}).',
        f'3. Apply `ValidateFunc` behavior to ID properties using [Go Azure SDK validation methods]({vendorSdkPath}).',
        f'4. Apply `ValidateFunc` behavior to `TypeString` properties which have `enum` field in specification using `validation.StringInSlice` method with [possible value slice method from Go Azure SDK]({vendorSdkPath}).',
        f'5. Add comment above `TypeString` properties suggesting suitable `ValidateFunc` method from [validation package]({validationPath}).',
        '6. Do not apply `Sensitive` behaviors.',
        '7. Apply `MaxItems: 1` to `TypeList` property that corresponds to specification parent properties which are not `array` type.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate behaviors to properties in [{resourceFile}]({resourcePath}) according to [specification]({dictConfig['specification']}) and the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': 'FlattenProperty'
    }

    step = 'FlattenProperty'
    stepType = 'copilot'
    listRule = [
        '1. `TypeList` or `TypeSet` parent property that contains only 1 child property.',
        '2. `TypeList` parent property that has `MaxItem` as `1` and less than 3 child properties.',
        f"3. `TypeList` `Required` parent property that has `MaxItem` as `1`.",
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Flatten child properties in schema of [{resourceFile}]({resourcePath}) if necessary. If the flattened child property name is same as any existing resource name, append the child property name to that of parent. These apply recursively to: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    return dictStepConfig

def getCrud2BasicTestFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateCreate'
    }

    step = 'GenerateCreate'
    stepType = 'copilot'
    listRule = [
        '1. `Create` method should be generated directly after `ResourceType` method.',
        '2. Timeout should be 30 mins.',
        '3. For `Optional` properties without `Default` behavior, check if properties are set before assigning to `param` structure.',
        '4. For `Optional` `TypeInt` properties, use `metadata.ResourceDiff.GetRawConfig` method to check if properties are not null before assigning to `param` structure.',
        '5. Use `client.CreateOrUpdate` method with polling when possible.',
        '6. `expand` should be methods instead of functions.',
        '7. `expand` methods should be generated at the end of codes.',
        '8. `expand` methods should only be created when assigning more than 1 child property to a Go SDK parent property.',
        '9. Do not expand Go SDK root level `Properties` structure.',
        '10. Do not have to check if `Required` `TypeList` or `TypeSet` properties are empty in `expand` methods.',
        '11. Use `pointer.To` to convert properties to pointers.',
        f"12. Use `pointer.ToEnum` to convert `string` properties to pointers for properties with `enum` field in [specification]({dictConfig['specification']})."
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'PreGenerateSdkOutput.json'),
        os.path.join(attachmentPath, 'GenerateReplaceDirectiveOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `Create` method in [{resourceFile}]({resourcePath}) according to `sdkPackage` in attached files and rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': 'GenerateUpdate'
    }

    # Seems to not generate codes for all relevant properties
    step = 'GenerateUpdate'
    stepType = 'copilot'
    listRule = [
        '1. `Update` method should be generated directly after `Create` method.',
        '2. Timeout should be 30 mins.',
        '3. Instead of initialize `param` structure in `Update` method, use the model obtained from `client.Get` method.',
        '4. Do not include properties with `ForceNew` behavior in `Update` method.',
        '5. Only assign properties to `param` structure if `metadata.HasChange` method returns true for the properties in `Update` method.',
        '6. Use `client.CreateOrUpdate` method instead of `client.Update` in `Update` method.',
        '7. Use `client.CreateOrUpdate` method with polling when possible.',
        '8. Apply `sdk.ResourceWithUpdate` interface if `Update` method is implemented.',
        '9. Use existing `expand` methods when possible.',
        '10. Use `pointer.To` to convert properties to pointers.',
        f"11. Use `pointer.ToEnum` to convert `string` properties to pointers for properties with `enum` field in [specification]({dictConfig['specification']})."
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'PreGenerateSdkOutput.json'),
        os.path.join(attachmentPath, 'GenerateReplaceDirectiveOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `Update` method in [{resourceFile}]({resourcePath}) according to `sdkPackage` in attached files and the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': 'GenerateRead'
    }

    step = 'GenerateRead'
    stepType = 'copilot'
    listRule = [
        '1. `Read` methods should be generated directly after `Update` method.',
        '2. Timeout should be 5 mins.',
        '3. For `Optional` properties with `Default` behavior, only assign properties to `state` structure if the properties are returned by `client.Get` method in `Read` method.',
        '4. `flatten` should be methods instead of functions.',
        '5. `flatten` methods should only be created to return a Terraform parent property in type of `interface` with more than 1 child property.',
        '6. Use `pointer.From` to convert pointers to properties.',
        f"7. Use `pointer.FromEnum` to convert pointers to `string` for properties with `enum` field in [specification]({dictConfig['specification']})."
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'PreGenerateSdkOutput.json'),
        os.path.join(attachmentPath, 'GenerateReplaceDirectiveOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `Read` method in [{resourceFile}]({resourcePath}) according to `sdkPackage` in attached files and the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': 'GenerateDelete'
    }

    step = 'GenerateDelete'
    stepType = 'copilot'
    listRule = [
        '1. `Delete` methods should be generated directly after `Read` method.',
        '2. Timeout should be 30 mins.'
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'PreGenerateSdkOutput.json'),
        os.path.join(attachmentPath, 'GenerateReplaceDirectiveOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `Delete` method in [{resourceFile}]({resourcePath}) according to `sdkPackage` in attached files and the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            }
        ],
        'nextStep': 'GenerateResourceIdentity'
    }

    step = 'GenerateResourceIdentity'
    stepType = 'copilot'
    listRule = [
        '1. Apply `sdk.ResourceWithIdentity` interface.',
        '2. Use `pluginsdk.SetResourceIdentityData` method before `return` statement in `Create` and `Read` methods.',
        '3. Add comment after `import` statement to generate resource identity test.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate resource identity in [{resourceFile}]({resourcePath}) according to the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'RefactorFlatten'
    }

    step = 'RefactorFlatten'
    stepType = 'copilot'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Wrap part of `Read` method in [{resourceFile}]({resourcePath}) from `state` initialization to `metadata.Encode` method (inclusive) in a separate `flatten` method. The `flatten` method should be located directly after `IDValidationFunc` method."
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'GenerateBasicTest'
    }

    step = 'GenerateBasicTest'
    stepType = 'copilot'
    existingTestPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], f"*_resource_test.go")
    listRule = [
        f"Refer to [specification]({dictConfig['specification']}) to understand the properties.",
        f"Refer to existing tests in [*_resource_test.go]({existingTestPath}) for prerequisite resources to create {dictConfig['resource']} if applicable.",
        'Refer to web for any relevant information.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `TestAcc{pascalCaseResource}_basic` in [{testFile}]({testPath}). The test should create {dictConfig['resource']} with only `Required` properties according to the rules: {' '.join(listRule)} {testRule}"
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': ''
    }

    return dictStepConfig

def addInitializeHttpProxy(dictStepConfig, nextStep):
    stepWrapper.addService(dictStepConfig, 'InitializeHttpProxyListener', 'InitializeHttpProxy')
    stepWrapper.addService(dictStepConfig, 'InitializeHttpProxy', nextStep)

    return

def configureRunBasicTest(dictStepConfig):
    step = 'ConfigureRunBasicTest'
    nextStep = flowControl.generateIndex(dictStepConfig[step], step, 10)

    return nextStep

def addRunTest(dictStepConfig, step, nextStep, testName):
    stepType = 'command'
    outputSavePath = os.path.join(attachmentPath, f'{step}TerminalLog.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'command': [
                ['make', 'fmt'],
                ['make', 'testacc'],
                ['curl', f"http://localhost:{dictConfig['port']['httpProxy'][0]['listener']}/saveHttpLog?savePath={step}HttpLog.json"]
            ],
            'env': {
                'TEST': f"./{dictConfig['path']['services']}",
                'TESTARGS': f'-test.parallel 1 -test.run={testName}',
                'TESTTIMEOUT': '1440m',
                'http_proxy': f"http://localhost:{dictConfig['port']['httpProxy'][0]['sender']}",
                'https_proxy': f"http://localhost:{dictConfig['port']['httpProxy'][0]['sender']}"
            }
        },
        'outputSavePath': outputSavePath,
        'bKeepSaveFile': True,
        'nextStep': nextStep
    }

    return

def getBasicTestFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'InitializeHttpProxyListener'
    }

    addInitializeHttpProxy(dictStepConfig, 'ConfigureRunBasicTest')
    stepWrapper.addControlFlow(dictStepConfig, 'ConfigureRunBasicTest', 'RunBasicTest', '')
    addRunTest(dictStepConfig, 'RunBasicTest', 'EvaluateBasicTest', f'TestAcc{pascalCaseResource}_basic')

    step = 'EvaluateBasicTest'
    stepType = 'copilot'
    listRule = [
        f"1. Check [{resourceFile}]({resourcePath}), [specification]({dictConfig['specification']}), and any relevant information from web to find the solution.",
        f"2. Add only 1 of the missing properties stated in the logs to [{resourceFile}]({resourcePath}) and `TestAcc{pascalCaseResource}_basic` according to [specification]({dictConfig['specification']}) if necessary, and do not do so if it is not necessary.",
        f"3. If parent property is added according to rule 2, only add the required child properties under the parent property according to [specification]({dictConfig['specification']}). If there is no required child property, add any 1 of the child properties.",
        '4. If a property or both parent and child properties are added according to rule 2, apply `Required` behavior to the properties.',
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'RunBasicTestHttpLog.json'),
        os.path.join(attachmentPath, 'RunBasicTestTerminalLog.json')
    ]
    outputSavePath = os.path.join(attachmentPath, 'EvaluateBasicTestOutput.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Based on the attached test terminal and HTTP logs, determine if `TestAcc{pascalCaseResource}_basic` in [{testFile}]({testPath}) passes. If the test fails, fix the test according to the logs and the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'model': 'claude-opus-4.8',
        'outputSavePath': outputSavePath,
        'nextStep': {
            'bPass': {
                True: '',
                False: 'ConfigureRunBasicTest'
            }
        }
    }

    return dictStepConfig

def configureRunCompleteTest(dictStepConfig):
    step = 'ConfigureRunCompleteTest'
    nextStep = flowControl.generateIndex(dictStepConfig['step'][step], step, 10)

    return nextStep

def getCompleteTestFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateCompleteTest'
    }

    step = 'GenerateCompleteTest'
    stepType = 'copilot'
    listRule = [
        f'1. Use `TestAcc{pascalCaseResource}_basic` as reference.',
        f'2. `TestAcc{pascalCaseResource}_complete` should contain all properties from `Arguments` method in [{resourceFile}]({resourcePath}).'
        f'3. For properties with `Default` behavior, set the properties to non-default value if possible.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}) if have not done so according to the rules: {' '.join(listRule)} {testRule}"
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': 'ConfigureRunCompleteTest'
    }

    addInitializeHttpProxy(dictStepConfig, 'ConfigureRunCompleteTest')
    stepWrapper.addControlFlow(dictStepConfig, 'ConfigureRunCompleteTest', 'RunCompleteTest', '')
    addRunTest(dictStepConfig, 'RunCompleteTest', 'EvaluateCompleteTest', f'TestAcc{pascalCaseResource}_complete')

    step = 'EvaluateCompleteTest'
    stepType = 'copilot'
    listRule = [
        f"1. Check [{resourceFile}]({resourcePath}), [specification]({dictConfig['specification']}), and any relevant information from web to find the solution.",
        f"2. Add only 1 of the missing properties stated in the logs to [{resourceFile}]({resourcePath}) and `TestAcc{pascalCaseResource}_complete` according to [specification]({dictConfig['specification']}) if necessary, and do not do so if it is not necessary."
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'RunCompleteTestHttpLog.json'),
        os.path.join(attachmentPath, 'RunCompleteTestTerminalLog.json')
    ]
    outputSavePath = os.path.join(attachmentPath, 'EvaluateCompleteTestOutput.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Based on the attached test terminal and HTTP logs, determine if `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}) passes. If the test fails, fix the test according to the logs and the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'model': 'claude-opus-4.8',
        'outputSavePath': outputSavePath,
        'nextStep': {
            'bPass': {
                True: '',
                False: 'ConfigureRunCompleteTest'
            }
        }
    }

    return dictStepConfig

def configureGenerateValidateFuncTest(dictStepConfig):
    step = 'ConfigureGenerateValidateFuncTest'

    with open(os.path.join(attachmentPath, 'GetPropertyWithoutValidateFuncOutput.json')) as f:
        listPropertyType = json.load(f)['listPropertyWithoutValidateFunc']

    nextStep = flowControl.generateIndex(dictStepConfig['step'][step], step, len(listPropertyType))

    if nextStep == 'GenerateValidateFuncTest':
        propertyName = listPropertyType[flowControl.dictIndex[step]][0]
        propertyType = listPropertyType[flowControl.dictIndex[step]][1]

        match propertyType:
            case 'TypeFloat' | 'TypeInt':
                listTestName =  ['negative', 'zero', 'digit2', 'digit3', 'digit4', 'uint16', 'int32', 'uint32']
                listTestValue = [-1, 0, 64, 128, 1024, 65535, 2147483647, 4294967295] if propertyType == 'TypeInt' else [-0.1, 0, 64.1, 128.1, 1024.1, 65535.1, 2147483647.1, 4294967295.1]
            case 'TypeString':
                listTestName = ['emojiSpecialChar', 'maxLength']
                listTestValue = ['🙂\\/"[]:|<>+=;,?*@&', 'a' * 256]

        listRule = [
            f'1. Refer to [`TestAcc{pascalCaseResource}_complete`]({testPath}) to generate the test.',
            '2. Do not use `ExpectError` and `PlanOnly` in the test.'
        ]
        listInput = []
        for testName, testValue in zip(listTestName, listTestValue):
            listInput.append({
                'prompt': f"Generate `TestAcc{pascalCaseResource}_vf_{propertyName}_{testName}` in [{validateFuncTestFile}]({validateFuncTestPath}) which contains `{propertyName}` property with `{testValue}` value if have not done so according to the rules: {' '.join(listRule)} {testRule} Do not change [{testFile}]({testPath}).",
            })

        dictStepConfig['step'][nextStep] = {
            'type': 'copilot',
            'input': listInput,
            'model': 'claude-opus-4.8',
            'nextStep': 'ConfigureGenerateValidateFuncTest'
        }

    return nextStep

def getValidateFuncFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GetPropertyWithoutValidateFunc'
    }

    step = 'GetPropertyWithoutValidateFunc'
    stepType = 'copilot'
    outputSavePath = os.path.join(attachmentPath, f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"List `TypeFloat`, `TypeInt`, and `TypeString` properties in `Arguments` method of [{resourceFile}]({resourcePath}) that do not have `ValidateFunc`. {checkPropertyRule}"
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'outputSavePath': outputSavePath,
        'nextStep': 'ConfigureGenerateValidateFuncTest'
    }

    stepWrapper.addControlFlow(dictStepConfig, 'ConfigureGenerateValidateFuncTest', 'GenerateValidateFuncTest', '')

    return dictStepConfig

def configureGenerateMaxItemsTest(dictStepConfig):
    step = 'ConfigureGenerateMaxItemsTest'

    with open(os.path.join(attachmentPath, 'GetParentPropertyWithoutMaxItemsOutput.json')) as f:
        listProperty = json.load(f)['listParentPropertyWithoutMaxItems']

    nextStep = flowControl.generateIndex(dictStepConfig['step'][step], step, len(listProperty))

    if nextStep == 'GenerateMaxItemsTest':
        propertyName = listProperty[flowControl.dictIndex[step]]
        testName = f'TestAcc{pascalCaseResource}_mi_{propertyName}'
        listRule = [
            '1. Use `count`, `for_each`, or `dynamic` block when applicable.',
            '2. Other resources which the property depends on should be created according to the number of the property elements when necessary.'
        ]
        dictStepConfig['step'][nextStep] = {
            'type': 'copilot',
            'input': [
                {
                    'prompt': f"Generate `{testName}` in [{maxItemsTestFile}]({maxItemsTestPath}) which contains `{propertyName}` property with 64 elements if have not done so according to the rules: {' '.join(listRule)} {testRule} Do not change [{testFile}]({testPath})."
                }
            ],
            'model': 'claude-opus-4.8',
            'nextStep': 'ConfigureGenerateMaxItemsTest'
        }

    return nextStep

def getMaxItemsFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GetParentPropertyWithoutMaxItems'
    }

    step = 'GetParentPropertyWithoutMaxItems'
    stepType = 'copilot'
    outputSavePath = os.path.join(attachmentPath, f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"List `TypeList` and `TypeSet` properties that do not have `MaxItems` behavior in `Arguments` method of [{resourceFile}]({resourcePath}). {checkPropertyRule}"
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'outputSavePath': outputSavePath,
        'nextStep': 'ConfigureGenerateMaxItemsTest'
    }

    stepWrapper.addControlFlow(dictStepConfig, 'ConfigureGenerateMaxItemsTest', 'GenerateMaxItemsTest', '')

    return dictStepConfig

def configureGenerateForceNewTest(dictStepConfig):
    step = 'ConfigureGenerateForceNewTest'

    with open(os.path.join(attachmentPath, 'GetPropertyWithoutForceNewOutput.json')) as f:
        listPropertyBehavior = json.load(f)['listPropertyWithoutForceNew']

    nextStep = flowControl.generateIndex(dictStepConfig['step'][step], step, len(listPropertyBehavior))

    if nextStep == 'GenerateForceNewTest':
        propertyName = listPropertyBehavior[flowControl.dictIndex[step]][0]
        propertyType = listPropertyBehavior[flowControl.dictIndex[step]][1]
        bRequired = listPropertyBehavior[flowControl.dictIndex[step]][2]
        bDefault = listPropertyBehavior[flowControl.dictIndex[step]][3]
        maxItems = listPropertyBehavior[flowControl.dictIndex[step]][4]
        bElemResource = listPropertyBehavior[flowControl.dictIndex[step]][5]

        testName = f'TestAcc{pascalCaseResource}_fn_{propertyName}'
        listStep = None

        if (propertyType == 'TypeList' or propertyType == 'TypeMap' or propertyType == 'TypeSet') and bRequired and (maxItems == 0 or maxItems > 1) and bElemResource:
            listStep = [
                f"1. Create `{dictConfig['resource']}` which contains `{propertyName}` with 1 element that has only `Required` child properties by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to add second element to `{propertyName}`."
                f"3. Update `{dictConfig['resource']}` to remove the second element of `{propertyName}`."
            ]
        elif (propertyType == 'TypeList' or propertyType == 'TypeMap' or propertyType == 'TypeSet') and bRequired and (maxItems == 0 or maxItems > 1) and not bElemResource:
            listStep = [
                f"1. Create `{dictConfig['resource']}` which contains `{propertyName}` with 1 element that has only `Required` child properties by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to change the `{propertyName}` element value to second value.",
                f"3. Update `{dictConfig['resource']}` to change the `{propertyName}` element value to first value.",
                f"4. Update `{dictConfig['resource']}` to add second element to `{propertyName}`."
                f"5. Update `{dictConfig['resource']}` to remove the second element of `{propertyName}`."
            ]
        elif propertyType == 'TypeList' and not bRequired and maxItems == 1:
            listStep = [
                f"1. Create `{dictConfig['resource']}` without `{propertyName}` by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to contain `{propertyName}` with 1 element that has only `Required` child properties.",
                f"3. Update `{dictConfig['resource']}` to remove `{propertyName}`."
            ]
        elif (propertyType == 'TypeList' or propertyType == 'TypeMap' or propertyType == 'TypeSet') and not bRequired and (maxItems == 0 or maxItems > 1) and bElemResource:
            listStep = [
                f"1. Create `{dictConfig['resource']}` without `{propertyName}` by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to contain `{propertyName}` with 1 element that has only `Required` child properties.",
                f"3. Update `{dictConfig['resource']}` to add second element to `{propertyName}`.",
                f"4. Update `{dictConfig['resource']}` to remove the second element of `{propertyName}`.",
                f"5. Update `{dictConfig['resource']}` to remove `{propertyName}`."
            ]
        elif (propertyType == 'TypeList' or propertyType == 'TypeMap' or propertyType == 'TypeSet') and not bRequired and (maxItems == 0 or maxItems > 1) and not bElemResource:
            listStep = [
                f"1. Create `{dictConfig['resource']}` without `{propertyName}` by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to contain `{propertyName}` with 1 element that has only `Required` child properties.",
                f"3. Update `{dictConfig['resource']}` to change the `{propertyName}` element value to second value.",
                f"4. Update `{dictConfig['resource']}` to change the `{propertyName}` element value to first value.",
                f"5. Update `{dictConfig['resource']}` to add second element to `{propertyName}`.",
                f"6. Update `{dictConfig['resource']}` to remove the second element of `{propertyName}`.",
                f"7. Update `{dictConfig['resource']}` to remove `{propertyName}`."
            ]
        elif bRequired:
            listStep = [
                f"1. Create `{dictConfig['resource']}` which contains `{propertyName}` with first value by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to change `{propertyName}` to second value."
                f"3. Update `{dictConfig['resource']}` to change `{propertyName}` to first value."
            ]
        elif bDefault:
            listStep = [
                f"1. Create `{dictConfig['resource']}` without `{propertyName}` by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to add `{propertyName}` with value different from `Default` value stated in [{resourceFile}]({resourcePath}).",
                f"3. Update `{dictConfig['resource']}` to remove `{propertyName}`."
            ]
        else:
            listStep = [
                f"1. Create `{dictConfig['resource']}` without `{propertyName}` by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to add `{propertyName}` with first value.",
                f"3. Update `{dictConfig['resource']}` to change `{propertyName}` to second value.",
                f"4. Update `{dictConfig['resource']}` to change `{propertyName}` to first value.",
                f"5. Update `{dictConfig['resource']}` to remove `{propertyName}`."
            ]

        dictStepConfig['step'][nextStep] = {
            'type': 'copilot',
            'input': [
                {
                    'prompt': f"Generate `{testName}` in [{forceNewTestFile}]({forceNewTestPath}) which updates only `{propertyName}` property if not not done so with the steps: {' '.join(listStep)} {testRule} Do not change [{testFile}]({testPath})."
                }
            ],
            'model': 'claude-opus-4.8',
            'nextStep': 'ConfigureGenerateForceNewTest'
        }

    return nextStep

def getForceNewFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GetPropertyWithoutForceNew'
    }

    step = 'GetPropertyWithoutForceNew'
    stepType = 'copilot'
    listRule = [
        '1. The properties `Type`, `Required`, `Optional`, `Default`, and `MaxItems` behaviors should be listed if applicable.',
        '2. For `TypeList`, `TypeMap`, and `TypeSet` properties, check if they have `Elem` behaviors with `pluginsdk.Resource` or `pluginsdk.Schema` methods.',
        '3. Consider both parent and child properties.',
        '4. Only include properties with name.'
    ]
    outputSavePath = os.path.join(attachmentPath, f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"List properties that do not have `ForceNew` behavior in `Arguments` method of [{resourceFile}]({resourcePath}) according to the rules: {' '.join(listRule)} {checkPropertyRule}"
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'model': 'claude-sonnet-4.6',
        'outputSavePath': outputSavePath,
        'nextStep': 'ConfigureGenerateForceNewTest'
    }

    stepWrapper.addControlFlow(dictStepConfig, 'ConfigureGenerateForceNewTest', 'GenerateForceNewTest', '')

    return dictStepConfig

def getRunParallelTestFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'InitializeHttpProxyListener'
    }

    addInitializeHttpProxy(dictStepConfig, 'RunParallelTest')

    step = 'RunParallelTest'
    stepType = 'callFunction'
    testPath = os.path.join(servicePath, f"{dictConfig['resource']}{dictConfig['testFileSuffix']}.go")
    testRegex = f"TestAcc{pascalCaseResource}{dictConfig['testRegex']}"
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'package': 'parallelTest',
            'function': 'runTest',
            'testPath': testPath,
            'testRegex': testRegex
        },
        'nextStep': ''
    }

    return dictStepConfig

def getPropertyName2ListResourceFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateListResourceTest'
    }

    step = 'ChangePropertyName'
    stepType = 'copilot'
    changedPropertyName = ', '.join([f'`{k}` to `{v}`' for k, v in dictConfig['propertyNameMap'].items()])
    listRule = [
        f'1. Change property names in `{pascalCaseResource}Model` structure accordingly.',
        '2. Change variable and function argument names which are assigned the properties mentioned in rule 1 accordingly.',
        '3. Change property names in error messages accordingly.',
        '4. Change property names in tests accordingly.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Change property names from {changedPropertyName} in `Arguments` and `Attributes` methods of [{resourceFile}]({resourcePath}). Edit [{resourceFile}]({resourcePath}) and [{testFile}]({testPath}) according to the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': 'RearrangeSchemaProperty'
    }

    step = 'RearrangeSchemaProperty'
    stepType = 'copilot'
    listRule = [
        '1. First 3 properties should be `name`, `resource_group_name`, and `location` in sequence if applicable.',
        '2. Last property should be `tags` if applicable.',
        '3. `Required` properties come before `Optional`.',
        '4. Within `Required`, `Optional`, and `Computed` properties, arrange the properties alphabetically.',
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Rearrange properties in `Arguments` and `Attributes` methods in [{resourceFile}]({resourcePath}) according to the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'RearrangeStructureProperty'
    }

    step = 'RearrangeStructureProperty'
    stepType = 'copilot'
    listRule = [
        '1. Properties correspond to that in `Arguments` method should comes first before that in `Attributes` method.',
        '2. Within properties correspond to `Arguments` and `Attributes` methods, arrange the properties according to the sequence in `Arguments` and `Attributes` methods respectively.',
        '3. Arrange the property assignment codes in `Create`, `Update`, `CustomizeDiff`, `expand*`, and `flatten*` methods according to the sequence specified in rule 1 and 2.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Rearrange properties of `{pascalCaseResource}Model` structure in [{resourceFile}]({resourcePath}) according to the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'RearrangeTestProperty'
    }

    step = 'RearrangeTestProperty'
    stepType = 'copilot'
    listRule = [
        '1. `count` comes before first property if applicable.',
        '2. First 3 properties should be `name`, `resource_group_name`, and `location` in sequence if applicable.',
        '3. Last property should be `tags` if applicable.',
        '4. Non-block properties come before block properties.',
        '5. Within non-block and block properties, `Required` properties come before `Optional`.',
        '6. Within `Required` and `Optional` properties, arrange the properties alphabetically.',
        '7. `depends_on` comes after last property if applicable.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Rearrange properties of all resources in [{testFile}]({testPath}) according to the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'GenerateListResource'
    }

    step = 'GenerateListResource'
    stepType = 'copilot'
    listPath = os.path.join(vendorSdkPath, pandoraServiceName.lower(), '*', '*', 'method_list*.go')
    listResourceFile = f"{dictConfig['resource']}_resource_list.go"
    listResourcePath = os.path.join(servicePath, listResourceFile)
    listRule0 = [
        '1. Generate `ResourceFunc`, `Metadata`, and `List` methods in sequence.',
        f"2. If there are `ListBy*` methods which accept arguments other than `commonids.Subscription` and `commonids.ResourceGroupId`, generate `{pascalCaseResource}ListModel` structure and `ListResourceConfigSchema`. Do not consider `context.Context` and `ListBy*OperationOptions` arguments.",
        "3. Apply `ctx.Deadline` and `context.WithDeadline` methods only when `context.Context` structure has to be passed into `flatten` method.",
        '4. Use `rmd` as name of variable to store result returned from `sdk.NewResourceMetadata` method.',
        f'5. Use `{pascalCaseResource}Result` as name of variable to store result returned from `range results`.',
        f'6. Add `{pascalCaseResource}ListResource` to {registrationPath}.'
    ]

    listResourceTestFile = f"{dictConfig['resource']}_resource_list_test.go"
    listResourceTestPath = os.path.join(servicePath, listResourceTestFile)
    listRule1 = [
        f'1. `TestAcc{pascalCaseResource}_list_basic` test should consist of 3 `resource.TestStep` with `Config` `basicList`, `basicQuery`, and `basicQueryByResourceGroupName`.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Check if there are [`ListBy*` methods]({listPath}) for {dictConfig['resource']}. If there is, generate [{listResourceFile}]({listResourcePath}) if have not done so according to the `ListBy*` methods and the rules: {' '.join(listRule0)} {testRule}"
            },
            {
                'prompt': f"Generate [{listResourceTestFile}]({listResourceTestPath}) if have not done so according to [{listResourceFile}]({listResourcePath}) and the rules: {' '.join(listRule1)} {testRule}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': 'GenerateListResourceTest'
    }

    step = 'GenerateListResourceTest'
    stepType = 'copilot'
    listResourceTestFile = f"{dictConfig['resource']}_resource_list_test.go"
    listResourceTestPath = os.path.join(servicePath, listResourceTestFile)
    listRule = [
        f'1. `TestAcc{pascalCaseResource}_list_basic` test should consist of 3 `resource.TestStep` with `Config` `basicList`, `basicQuery`, and `basicQueryByResourceGroupName`.',
        f'2. Refer to [`basic` method]({testPath}) to generate `basicList` method.',
        '3. In `basicQueryByResourceGroupName` method, use `azurerm_resource_group.test.name` as input for `resource_group_name` property.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate [{listResourceTestFile}]({listResourceTestPath}) to test list resource if have not done so according to [{listResourceFile}]({listResourcePath}) and the rules: {' '.join(listRule1)} {testRule}"
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': ''
    }

    return dictStepConfig

def getFlattenPropertyFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'FlattenPropertyManually'
    }

    step = 'FlattenPropertyManually'
    stepType = 'copilot'
    listRule = [
        '1. Flattening is done for only 1 level.',
        '2. If the flattened child property name is same as any existing property name, append the child property name to that of parent.',
        f'3. Edit [{resourceFile}]({resourcePath}) and [{testFile}]({testPath}) accordingly after flattening.',
        '4. If multiple `HasChange` methods are used in a `if else` statement, use `HasChanges` instead.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Flatten all child properties under `{dictConfig['flattenParentProperty']}` parent property in `Arguments` and `Attributes` methods of [{resourceFile}]({resourcePath}) if necessary according to the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    return dictStepConfig

def getProperty2RequiredFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'Property2RequiredManually'
    }

    step = 'Property2RequiredManually'
    stepType = 'copilot'
    requiredProperty = ', '.join([f'`{property}`' for property in dictConfig['requiredProperty']])
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Change {requiredProperty} properties behavior to `Required` in [{resourceFile}]({resourcePath}). Edit {resourceFile} and [{testFile}]({testPath}) accordingly."
            }
        ],
        'nextStep': ''
    }

    return dictStepConfig

def getPropertyFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GeneratePropertyManually'
    }

    step = 'GeneratePropertyManually'
    stepType = 'copilot'
    generatedProperty = ', '.join([f'`{property}`' for property in dictConfig['generatedProperty']])
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate {generatedProperty} properties to `Argument` method in [{resourceFile}]({resourcePath}) according to [specification]({dictConfig['specification']}). Edit {resourceFile} and [{testFile}]({testPath}) accordingly."
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    return dictStepConfig

def getAttributeFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateAttributeManually'
    }

    step = 'GenerateAttributeManually'
    stepType = 'copilot'
    generatedAttribute = ', '.join([f'`{attribute}`' for attribute in dictConfig['generatedAttribute']])
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate {generatedAttribute} properties to `Attributes` method in [{resourceFile}]({resourcePath}) according to [specification]({dictConfig['specification']}). Edit {resourceFile} accordingly."
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    return dictStepConfig

def getCustomizeDiffFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateCustomizeDiffManually'
    }

    step = 'GenerateCustomizeDiffManually'
    stepType = 'copilot'
    listRule = [
        '1. The `CustomizeDiff` method should be placed directly after `IDValidationFunc`.',
        '2. Timeout should be 5 mins.',
        '3. Apply `sdk.ResourceWithCustomizeDiff` interface.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate empty `CustomizeDiff` method in [{resourceFile}]({resourcePath}) if have not done so according to the rules: {' '.join(listRule)}"
            }
        ],
        'nextStep': ''
    }

    return dictStepConfig

def getFlow():
    dictStepConfig = None

    match dictConfig['flow']:
        case 'aiAssistedDevelopment2PortalProperty':
            dictStepConfig = getAiAssistedDevelopment2PortalPropertyFlow()
        case 'schema':
            dictStepConfig = getSchemaFlow()
        case 'crud2BasicTest':
            dictStepConfig = getCrud2BasicTestFlow()
        case 'basicTest':
            dictStepConfig = getBasicTestFlow()
        case 'completeTest':
            dictStepConfig = getCompleteTestFlow()
        case 'validateFunc':
            dictStepConfig = getValidateFuncFlow()
        case 'maxItems':
            dictStepConfig = getMaxItemsFlow()
        case 'forceNew':
            dictStepConfig = getForceNewFlow()
        case 'runParallelTest':
            dictStepConfig = getRunParallelTestFlow()
        case 'propertyName2ListResource':
            dictStepConfig = getPropertyName2ListResourceFlow()
        case 'flattenProperty':
            dictStepConfig = getFlattenPropertyFlow()
        case 'property2Required':
            dictStepConfig = getProperty2RequiredFlow()
        case 'property':
            dictStepConfig = getPropertyFlow()
        case 'attribute':
            dictStepConfig = getAttributeFlow()
        case 'customizeDiff':
            dictStepConfig = getCustomizeDiffFlow()

    return dictStepConfig

'''
step = 'Sleep'
stepType = 'command'
dictStepConfig['step'][step] = {
    'type': stepType,
    'input': {
        'command': [
            ['sleep', '600']
        ]
    },
    'nextStep': ''
}
'''