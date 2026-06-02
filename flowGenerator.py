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
forceNewTestFile = f"{dictConfig['resource']}_resource_fn_test.go"
forceNewTestPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], forceNewTestFile)
maxItemsTestFile = f"{dictConfig['resource']}_resource_mi_test.go"
maxItemsTestPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], maxItemsTestFile)

listTestRule = [
    f'1. Always use `Standard_F1als_v7` size when virtual machine is used.'
]
testRule = f"Additional rules: {' '.join(listTestRule)}"

def getRegistration2PortalPropertyFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateEmptyRegistration'
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
    listRule = [
        '1. Apply `Required` behavior to properties according to specification. Otherwise, apply `Optional` behavior.',
        f'2. Apply `ForceNew` behavior to properties which are absent from [`Update` method argument of Go Azure SDK]({updatePath}).',
        f'3. Apply `ValidateFunc` behavior to ID properties using [Go Azure SDK validation methods]({vendorSdkPath}).',
        f'4. Apply `ValidateFunc` behavior to properties which have `enum` field in specification using `validation.StringInSlice` method with [possible value slice method from Go Azure SDK]({vendorSdkPath}).',
        '5. Do not apply `Sensitive` behaviors.',
        '6. Apply `MaxItems: 1` to `TypeList` property that corresponds to specification parent properties which are not `array` type.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate behaviors to properties in [{resourceFile}]({resourcePath}) according to [specification]({dictConfig['specification']}) and the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-sonnet-4.6',
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
    '''
    step = 'GenerateCrud'
    stepType = 'copilot'
    listRule = [
        '1. CRUD methods should be generated between `ResourceType` and `IDValidationFunc` methods.',
        '2. `Update` method should come directly after `Create` method.',
        '3. Timeout should be 30 mins for `Create`, `Update`, and `Delete` methods and 5 mins for `Read` method.',
        '4. For `Optional` properties without `Default` behavior, check if properties are set before assigning to `param` structure in `Create` method.',
        '5. For `Optional` `TypeInt` properties, use `metadata.ResourceDiff.GetRawConfig` method to check if properties are not null before assigning to `param` structure.',
        # '6. For `Optional` `TypeBool` properties with `Default`, assign the `Default` value to the properties in `Read` method if the properties are not returned by `client.Get` method',
        '6. Instead of initialize `param` structure in `Update` method, use the model obtained from `client.Get` method.',
        '7. Do not include properties with `ForceNew` behavior in `Update` method.',
        '8. Only assign properties to `param` structure if `metadata.HasChange` method returns true for the properties in `Update` method.',
        '9. Use `client.CreateOrUpdate` method instead of `client.Update` in `Update` method.',
        "10. Apply `sdk.ResourceWithUpdate` interface if `Update` method is implemented.",
        '11. For `Optional` properties, only assign properties to `state` structure if the properties are returned by `client.Get` method in `Read` method.',
        '12. Use `client` methods with polling whenever possible.',
        '13. `expand` method should only be created when assigning more than 1 child property to a Go SDK parent property.',
        '14. Do not expand Go SDK root level `Properties` structure.',
        '15. `flatten` method should only be created to return a Terraform parent property in type of `interface` and more than 1 child property.',
        f"16. Use `pointer.ToEnum` to convert `string` to pointer for properties with `enum` field in [specification]({dictConfig['specification']}).",
        f"17. Use `pointer.FromEnum` to convert pointer to `string` for properties with `enum` field in [specification]({dictConfig['specification']})."
    ]
    listAttachmentPath = [
        os.path.join(attachmentPath, 'PreGenerateSdkOutput.json'),
        os.path.join(attachmentPath, 'GenerateReplaceDirectiveOutput.json')
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate CRUD methods in [{resourceFile}]({resourcePath}) according to `sdkPackage` in attached files and the rules: {' '.join(listRule)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-opus-4.8',
        'nextStep': 'GenerateResourceIdentity'
    }
    '''
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
        f"12. Use `pointer.ToEnum` to convert `string` properties to pointers for properties with `enum` field in [specification]({dictConfig['specification']}).",
        '13. Do not use `SkipImportCheckOnCreateAndAllowOverwritingExistingResources` method.'
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
                ['curl', f"http://localhost:{dictConfig['port']['httpProxyListener']}/saveHttpLog?savePath={step}HttpLog.json"]
            ],
            'env': {
                'TEST': f"./{dictConfig['path']['services']}",
                'TESTARGS': f'-test.parallel 1 -test.run={testName}',
                'TESTTIMEOUT': '1440m',
                'http_proxy': f"http://localhost:{dictConfig['port']['httpProxy']}",
                'https_proxy': f"http://localhost:{dictConfig['port']['httpProxy']}"
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
        'firstStep': 'InitializeHttpProxyListener'
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
                'prompt': f"Generate `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}) accorrding to the rules: {' '.join(listRule)} {testRule}"
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
                listTestName = ['emojiSpecialChar']
                listTestValue = ['🙂\\/"[]:|<>+=;,?*@&']

        listRule = [
            f'1. Refer to [`TestAcc{pascalCaseResource}_complete`]({testPath}) to generate the test.',
            '2. Do not use `ExpectError` and `PlanOnly` in the test.'
        ]
        listInput = []
        for testName, testValue in zip(listTestName, listTestValue):
            listInput.append({
                'prompt': f"Generate `TestAcc{pascalCaseResource}_vf_{propertyName}_{testName}` in [{validateFuncTestFile}]({validateFuncTestPath}) which contains `{propertyName}` property with `{testValue}` value according to the rules: {' '.join(listRule)} {testRule}",
            })

        next2Step = 'ConfigureRunValidateFuncTest'
        dictStepConfig['step'][nextStep] = {
            'type': 'copilot',
            'input': listInput,
            'model': 'claude-opus-4.8',
            'nextStep': next2Step
        }

        dictTestName = {
            'listValidateFuncTest': [f'TestAcc{pascalCaseResource}_vf_{propertyName}_{testName}' for testName in listTestName]
        }

        with open(os.path.join(attachmentPath, 'validateFuncTest.json'), 'w') as f:
            json.dump(dictTestName, f, indent = 4)

        if next2Step in flowControl.dictIndex:
            del flowControl.dictIndex[next2Step]

    return nextStep

def configureRunValidateFuncTest(dictStepConfig):
    step = 'ConfigureRunValidateFuncTest'

    with open(os.path.join(attachmentPath, 'validateFuncTest.json'), 'r') as f:
        listTestName = json.load(f)['listValidateFuncTest']

    nextStep = flowControl.generateIndex(dictStepConfig['step'][step], step, len(listTestName))

    if nextStep == 'RunValidateFuncTest':
        testName = listTestName[flowControl.dictIndex[step]]
        addRunTest(dictStepConfig, 'RunValidateFuncTest', 'EvaluateValidateFuncTest', testName)

        step = 'EvaluateValidateFuncTest'
        stepType = 'copilot'
        validationPath = os.path.join(dictConfig['path']['azurerm'], 'vendor', 'github.com', 'terraform-provider-azurerm', 'internal', 'tf', 'validation')
        listRule = [
            '1. Do not add `ValidateFunc` if the test fails due to other reasons.',
            f'2. Apply function from [validation package]({validationPath}) if applicable.'
        ]
        listAttachmentPath = [
            os.path.join(attachmentPath, 'RunValidateFuncTestHttpLog.json'),
            os.path.join(attachmentPath, 'RunValidateFuncTestTerminalLog.json')
        ]
        dictStepConfig['step'][step] = {
            'type': stepType,
            'input': [
                {
                    'prompt': f"Check if `{testName}` in [{validateFuncTestFile}]({validateFuncTestPath}) passes according to the test terminal and HTTP logs. If the test fails due to the invalid value of tested property and the valid value format is returned in error message, add `ValidateFunc` to the tested property in `Arguments` method of [{resourceFile}]({resourcePath}) according to the valid value format in the error message. Follow the rules: {' '.join(listRule)}",
                    'attachments': listAttachmentPath
                },
                {
                    'prompt': outputFormatPrompt(_step = step)
                }
            ],
            'model': 'claude-opus-4.8',
            'nextStep': {
                'bAddValidateFunc': {
                    True: 'ConfigureGenerateValidateFuncTest',
                    False: 'ConfigureRunValidateFuncTest'
                }
            }
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
                'prompt': f"List `TypeFloat`, `TypeInt`, and `TypeString` properties in `Arguments` method of [{resourceFile}]({resourcePath}) that do not have `ValidateFunc`."
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'outputSavePath': outputSavePath,
        'nextStep': 'InitializeHttpProxyListener'
    }

    addInitializeHttpProxy(dictStepConfig, 'ConfigureGenerateValidateFuncTest')
    stepWrapper.addControlFlow(dictStepConfig, 'ConfigureGenerateValidateFuncTest', 'GenerateValidateFuncTest', 'GenerateDefaultValidateFunc')
    stepWrapper.addControlFlow(dictStepConfig, 'ConfigureRunValidateFuncTest', 'RunValidateFuncTest', 'ConfigureGenerateValidateFuncTest')

    step = 'GenerateDefaultValidateFunc'
    stepType = 'copilot'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `ValidateFunc` behaviors with `validation.StringIsNotEmpty` for the `TypeString` properties without `ValidateFunc` in [{resourceFile}]({resourcePath})."
            }
        ],
        'nextStep': ''
    }

    return dictStepConfig

def configureGenerateMaxItemsTest(dictStepConfig):
    step = 'ConfigureGenerateMaxItemsTest'

    with open(os.path.join(attachmentPath, 'GetPropertyWithoutMaxItemsOutput.json')) as f:
        listProperty = json.load(f)['listPropertyWithoutMaxItems']

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
                    'prompt': f"Generate `{testName}` in [{maxItemsTestFile}]({maxItemsTestPath}) which contains `{propertyName}` property with 64 elements according to the rules: {' '.join(listRule)} {testRule}"
                }
            ],
            'model': 'claude-opus-4.8',
            'nextStep': 'RunMaxItemsTest'
        }

        addRunTest(dictStepConfig, 'RunMaxItemsTest', 'EvaluateMaxItemsTest', testName)

        step = 'EvaluateMaxItemsTest'
        stepType = 'copilot'
        listRule = [
            '1. Do not add `MaxItems` if the test fails due to other reasons.'
        ]
        listAttachmentPath = [
            os.path.join(attachmentPath, 'RunMaxItemsTestHttpLog.json'),
            os.path.join(attachmentPath, 'RunMaxItemsTestTerminalLog.json')
        ]
        dictStepConfig['step'][step] = {
            'type': stepType,
            'input': [
                {
                    'prompt': f"Check if `{testName}` in [{maxItemsTestFile}]({maxItemsTestPath}) passes according to the test terminal and HTTP logs. If the test fails due to exceeded number of tested property elements and the maximum number is returned in error message, add `MaxItems` behavior to the tested property in `Arguments` method of [{resourceFile}]({resourcePath}) according to the maximum number in the error message. Follow the rules: {' '.join(listRule)}",
                    'attachments': listAttachmentPath
                },
                {
                    'prompt': outputFormatPrompt(_step = step)
                }
            ],
            'model': 'claude-opus-4.8',
            'nextStep': 'ConfigureGenerateMaxItemsTest'
        }

    return

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
                'prompt': f"List `TypeList` and `TypeSet` properties that do not have `MaxItems` behavior in `Arguments` method of [{resourceFile}]({resourcePath})."
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'outputSavePath': outputSavePath,
        'nextStep': 'InitializeHttpProxyListener'
    }

    addInitializeHttpProxy(dictStepConfig, 'ConfigureGenerateMaxItemsTest')
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
        maxItems = listPropertyBehavior[flowControl.dictIndex[step]][3]

        testName = f'TestAcc{pascalCaseResource}_update_{propertyName}'
        listStep = None

        if (propertyType == 'TypeList' or propertyType == 'TypeSet') and bRequired and (maxItems == 0 or maxItems > 1):
            listStep = [
                f"1. Create `{dictConfig['resource']}` which contains `{propertyName}` with 1 element that has only `Required` child properties by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to add second element to `{propertyName}`."
                f"3. Update `{dictConfig['resource']}` to remove the second element of `{propertyName}`."
            ]
        elif propertyType == 'TypeList' and not bRequired and maxItems == 1:
            listStep = [
                f"1. Create `{dictConfig['resource']}` without `{propertyName}` by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to contain `{propertyName}` with 1 element that has only `Required` child properties.",
                f"3. Update `{dictConfig['resource']}` to remove `{propertyName}`."
            ]
        elif (propertyType == 'TypeList' or propertyType == 'TypeSet') and not bRequired and (maxItems == 0 or maxItems > 1):
            listStep = [
                f"1. Create `{dictConfig['resource']}` without `{propertyName}` by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to contain `{propertyName}` with 1 element that has only `Required` child properties.",
                f"3. Update `{dictConfig['resource']}` to add second element to `{propertyName}`.",
                f"4. Update `{dictConfig['resource']}` to remove the second element of `{propertyName}`.",
                f"5. Update `{dictConfig['resource']}` to remove `{propertyName}`."
            ]
        elif bRequired:
            listStep = [
                f"1. Create `{dictConfig['resource']}` which contains `{propertyName}` with first value by referring to `TestAcc{pascalCaseResource}_complete` in [{testFile}]({testPath}).",
                f"2. Update `{dictConfig['resource']}` to change `{propertyName}` to second value."
                f"3. Update `{dictConfig['resource']}` to change `{propertyName}` to first value."
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
                    'prompt': f"Generate `{testName}` in [{forceNewTestFile}]({forceNewTestPath}) which updates only `{propertyName}` property with the steps: {' '.join(listStep)} {testRule}"
                }
            ],
            'model': 'claude-opus-4.8',
            'nextStep': 'RunForceNewTest'
        }

        addRunTest(dictStepConfig, 'RunForceNewTest', 'EvaluateForceNewTest', testName)

        step = 'EvaluateForceNewTest'
        stepType = 'copilot'
        listAttachmentPath = [
            os.path.join(attachmentPath, 'RunForceNewTestHttpLog.json'),
            os.path.join(attachmentPath, 'RunForceNewTestTerminalLog.json')
        ]
        dictStepConfig['step'][step] = {
            'type': stepType,
            'input': [
                {
                    'prompt': f"Check if `{testName}` in [{forceNewTestFile}]({forceNewTestPath}) passes according to the test terminal and HTTP logs. If the test fails due to failure to update the `{propertyName}` property, add `ForceNew` behavior to the tested property in `Arguments` method of [{resourceFile}]({resourcePath})",
                    'attachments': listAttachmentPath
                },
                {
                    'prompt': outputFormatPrompt(_step = step)
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
    outputSavePath = os.path.join(attachmentPath, f'{step}Output.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"List properties that do not have `ForceNew` behavior in `Arguments` method of [{resourceFile}]({resourcePath}). Their `Type`, `Required`, `Optional`, and `MaxItems` behaviors should be listed if applicable. Consider both parent and child properties."
            },
            {
                'prompt': outputFormatPrompt(_step = step)
            }
        ],
        'outputSavePath': outputSavePath,
        'nextStep': 'InitializeHttpProxyListener'
    }

    addInitializeHttpProxy(dictStepConfig, 'ConfigureGenerateForceNewTest')
    stepWrapper.addControlFlow(dictStepConfig, 'ConfigureGenerateForceNewTest', 'GenerateForceNewTest', '')

    return dictStepConfig

def getFlattenPropertyFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'FlattenPropertyManually'
    }

    step = 'FlattenPropertyManually'
    stepType = 'copilot'
    parentProperty = 'package_application'
    listRule = [
        '1. Flattening is done for only 1 level.',
        '2. If the flattened child property name is same as any existing property name, append the child property name to that of parent.',
        f'3. Edit [{resourceFile}]({resourcePath}) and [{testFile}]({testPath}) accordingly after flattening.'
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Flatten all child properties under `{parentProperty}` parent property in schema of [{resourceFile}]({resourcePath}) if necessary according to the rules: {' '.join(listRule)}"
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
    listProperty = [
        ''
    ]
    listProperty = [f'`{property}`' for property in listProperty]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Change {', '.join(listProperty)} properties behavior to `Required` in [{resourceFile}]({resourcePath}). Edit {resourceFile} and [{testFile}]({testPath}) accordingly."
            }
        ],
        'nextStep': ''
    }

    return dictStepConfig

def getGeneratePropertyFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GeneratePropertyManually'
    }

    step = 'GeneratePropertyManually'
    stepType = 'copilot'
    listProperty = [
        'applicationType'
    ]
    listProperty = [f'`{i}`' for i in listProperty]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate {', '.join(listProperty)} properties to `Argument` method in [{resourceFile}]({resourcePath}) according to [specification]({dictConfig['specification']}). Edit {resourceFile} and [{testFile}]({testPath}) accordingly."
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    return dictStepConfig

def getGenerateAttributeFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateAttributeManually'
    }

    step = 'GenerateAttributeManually'
    stepType = 'copilot'
    listProperty = [
        'LastUpdated',
        'PackageFamilyName',
        'PackageName',
        'PackageRelativePath',
        'Version',
        'AppId',
        'AppUserModelID',
        'Description',
        'FriendlyName',
        'IconImageName',
        'RawIcon',
        'RawPng'
    ]
    listProperty = [f'`{i}`' for i in listProperty]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate {', '.join(listProperty)} properties to `Attributes` method in [{resourceFile}]({resourcePath}) according to [specification]({dictConfig['specification']}). Edit {resourceFile} accordingly."
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    return dictStepConfig

def getFlow():
    dictStepConfig = None

    match dictConfig['flow']:
        case 'registration2PortalProperty':
            dictStepConfig = getRegistration2PortalPropertyFlow()
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
        case 'flattenProperty':
            dictStepConfig = getFlattenPropertyFlow()
        case 'property2Required':
            dictStepConfig = getProperty2RequiredFlow()
        case 'generateProperty':
            dictStepConfig = getGeneratePropertyFlow()
        case 'generateAttribute':
            dictStepConfig = getGenerateAttributeFlow()

    return dictStepConfig