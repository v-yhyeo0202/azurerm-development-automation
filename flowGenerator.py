import functools
import os
import yaml

import flowControl

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

def formatMultilineCommand(inputString):
    outputString = inputString.replace('  ', '').strip('\n').replace('\n', '; ')

    return outputString

outputFormatPrompt = functools.partial(
    'UNDER ANY CIRCUMSTANCES, GENERATE LAST OUTPUT IN JSON FORMAT ACCORDING TO [`{_step}Output` CLASS]({dataStructurePath})!'.format,
    dataStructurePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['code'], 'dataStructure.py')
)
vendorSdkPath = os.path.join(dictConfig['path']['azurerm'], 'vendor', 'github.com', 'hashicorp', 'go-azure-sdk')
pandoraServiceName = dictConfig['pandoraServiceName'] if dictConfig['pandoraServiceName'] else dictConfig['serviceName'].replace(' ', '')
resourceFile = f"{dictConfig['resource']}_resource.go"
resourcePath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], resourceFile)
testFile = f"{dictConfig['resource']}_resource_test.go"
testPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], testFile)
pascalCaseResource = ''.join([i.capitalize() for i in dictConfig['resource'].split('_')])

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
                'prompt': f"Get list of {dictConfig['resource']} properties which are present in attached portal screenshots according to [specification]({dictConfig['specification']}) and the rules: {' '.join(listRule)} {outputFormatPrompt(_step = step)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-opus-4.7',
        'outputSavePath': outputSavePath,
        'nextStep': ''
    }

    return dictStepConfig

def getSchemaFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateBehavior'
    }

    step = 'GenerateSchema'
    stepType = 'copilot'
    commonSchemaPath = os.path.join(dictConfig['path']['azurerm'], 'vendor', 'github.com', 'hashicorp', 'go-azure-helpers', 'resourcemanager', 'commonschema')
    listRule = [
        '1. Generate resource schema (`Arguments`), `Attributes` (can be empty if not applicable), `ModelObject`, `ResourceType`, and `IDValidationFunc` methods in sequence and other relevant codes.',
        '2. Do not generate CRUD methods.',
        '3. Only the properties listed in attached file should be included.',
        '4. Generate typed resource.',
        '5. Do not apply any behaviors except `Type` and `Elem` to all properties.',
        f'6. Apply [common schema]({commonSchemaPath}) to `resource_group_name`, `location`, `tags`, `identity`, and `zone` if they exist in attached file.',
        '7. Model structure name should contain `Model` suffix, not `ResourceModel` suffix.'
    ]
    listAttachmentPath = [
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'GetPortalPropertyOutput.json')
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
        f"5. Apply `ValidateFunc` behavior to `TypeString` properties which their regular expression patterns or date formats are listed in specification.",
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
                'prompt': f"Flatten child properties in schema of [{resourceFile}]({resourcePath}) if necessary. If the flattened child property name is same as any existing resource name, append the child property name to that of parent. These apply recursively to: {' '.join(listRule)} Carry out any necessary modifications after flattening."
            }
        ],
        'model': 'claude-sonnet-4.6',
        'nextStep': ''
    }

    return dictStepConfig

def getCrud2BasicTestFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateCrud'
    }

    step = 'GenerateCrud'
    stepType = 'copilot'
    listRule = [
        '1. CRUD methods should be generated between `ResourceType` and `IDValidationFunc` methods.',
        '2. `Update` method should come directly after `Create` method.',
        '3. Timeout should be 30 mins for `Create`, `Update`, and `Delete` methods and 5 mins for `Read` method.',
        '4. For `Optional` properties, check if properties are set before assigning to `param` structure in `Create` method.',
        '5. For `Optional` `TypeInt` properties, use `metadata.ResourceDiff.GetRawConfig` method to check if properties are not null before assigning to `param` structure.',
        # '6. For `Optional` `TypeBool` properties with `Default`, assign the `Default` value to the properties in `Read` method if the properties are not returned by `client.Get` method',
        '6. Instead of initialize `param` structure in `Update` method, use the model obtained from `client.Get` method.',
        '7. Do not include properties with `ForceNew` behavior in `Update` method.',
        '8. Only assign properties to `param` structure if `metadata.HasChange` method returns true for the properties in `Update` method.',
        '9. Use `client.CreateOrUpdate` method instead of `client.Update` in `Update` method.',
        '10. For `Optional` properties, only assign properties to `state` structure if the properties are returned by `client.Get` method in `Read` method.',
        '11. Use `client` methods with polling whenever possible.',
        '12. `expand` method should only be created when assigning more than 1 child property to a Go SDK parent property.',
        '13. Do not expand Go SDK root level `Properties` structure.',
        '14. `flatten` method should only be created to return a Terraform parent property in type of `interface` and more than 1 child property.'
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
        'nextStep': 'GenerateResourceIdentity'
    }

    step = 'GenerateResourceIdentity'
    stepType = 'copilot'
    listRule = [
        '1. `sdk.ResourceWithIdentity` interface should be applied.',
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
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `TestAcc{pascalCaseResource}_basic` in [{testFile}]({testPath}). The test should create {dictConfig['resource']} with only `Required` properties."
            }
        ],
        'model': 'claude-opus-4.7',
        'nextStep': ''
    }

    return dictStepConfig

def addRunTest(dictStepConfig, step, testName, nextStep):
    stepType = 'command'
    outputSavePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], f'{step}TerminalLog.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'command': [
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
        'nextStep': nextStep
    }

    return

def configureRunBasicTest(step, dictStepConfig):
    step = flowControl.generateIndex(step, dictStepConfig, 10)

    return step

def getBasicTestFlow():
    dictStepConfig = {
        'step': {},
        'firstStep': 'GenerateBasicTest'
    }

    step = 'GenerateBasicTest'
    stepType = 'copilot'
    existingTestPath = os.path.join(dictConfig['path']['azurerm'], dictConfig['path']['services'], f"*_resource_test.go")
    listRule = [
        f"Refer to [specification]({dictConfig['specification']}) to understand the properties.",
        f"Refer to existing tests in [*_resource_test.go]({existingTestPath}) for prerequisite resources to create {dictConfig['resource']} if applicable."
    ]
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Generate `TestAcc{pascalCaseResource}_basic` in [{testFile}]({testPath}). The test should create {dictConfig['resource']} with only `Required` properties according to the rules: {' '.join(listRule)}"
            }
        ],
        'model': 'claude-opus-4.7',
        'nextStep': 'InitializeHttpProxyListener'
    }

    step = 'InitializeHttpProxyListener'
    stepType = 'service'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {},
        'nextStep': 'InitializeHttpProxy'
    }

    step = 'InitializeHttpProxy'
    stepType = 'service'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {},
        'nextStep': 'ConfigureRunBasicTest'
    }

    step = 'ConfigureRunBasicTest'
    stepType = 'controlFlow'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'packageName': 'flowGenerator'
        },
        'nextStep': 'RunBasicTest'
    }

    addRunTest(dictStepConfig, 'RunBasicTest', f'TestAcc{pascalCaseResource}_basic', 'EvaluateBasicTest')

    step = 'EvaluateBasicTest'
    stepType = 'copilot'
    listRule = [
        f"1. Check [{resourceFile}]({resourcePath}) and [specification]({dictConfig['specification']}) to find the solution.",
        f'2. Add only one of the missing properties stated in the logs to [{resourceFile}]({resourcePath}) and `TestAcc{pascalCaseResource}_basic` according to [specification]({dictConfig["specification"]}) if necessary, and do not do so if it is not necessary.',
        f'3. If parent property is applied according to rule 1, only add the required child properties under the parent property according to [specification]({dictConfig["specification"]}). If there is no required child property, add any one of the child properties.'
    ]
    listAttachmentPath = [
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'RunBasicTestHttpLog.json'),
        os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'RunBasicTestTerminalLog.json')
    ]
    outputSavePath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], 'EvaluateBasicTestOutput.json')
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': [
            {
                'prompt': f"Based on the attached test terminal and HTTP logs, determine if `TestAcc{pascalCaseResource}_basic` in [{testFile}]({testPath}) passes or fails. If the test fails, fix the test according to the logs and the rules: {' '.join(listRule)} {outputFormatPrompt(_step = step)}",
                'attachments': listAttachmentPath
            }
        ],
        'model': 'claude-opus-4.7',
        'outputSavePath': outputSavePath,
        'nextStep': {
            'bPass': {
                True: '',
                False: 'ConfigureRunBasicTest'
            }
        }
    }

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
    '''
    with open('flowConfig.yml', 'w') as f:
        yaml.dump(dictStepConfig, f)
    '''
    return dictStepConfig