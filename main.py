import json
import langchain_core
import yaml

import dataStructure
import generateFlow
import stepTool

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

generateFlow.generateFlow()

with open('flowConfig.yml') as f:
    dictStepConfig = yaml.load(f, Loader = yaml.FullLoader)

def getNextStep(dictCurrentStepConfig, dictOutput = None):
    if 'nextStep' not in dictCurrentStepConfig:

        return None

    if dictOutput and isinstance(dictCurrentStepConfig['nextStep'], dict):
        key = list(dictCurrentStepConfig['nextStep'])[0]
        nextStep = dictCurrentStepConfig['nextStep'][key][dictOutput[key]]
    else:
        nextStep = dictCurrentStepConfig['nextStep']

    return nextStep

step = dictStepConfig['firstStep']
dictPreviousOutput = None
dictOutput = None

while step:
    print('debug6')
    dictCurrentStepConfig = dictStepConfig['step'][step]

    if dictPreviousOutput:
        dictCurrentStepConfig['input'].update(dictPreviousOutput)
        dictPreviousOutput = None

    match dictCurrentStepConfig['type']:
        case 'copilot':
            copilotModel = stepTool.CopilotModel()
            outputDataStructure = f'{step}Output'

            if hasattr(dataStructure, outputDataStructure):
                copilotModel = copilotModel.with_structured_output(getattr(dataStructure, outputDataStructure))

            dictOutput = copilotModel.invoke(
                [langchain_core.messages.HumanMessage('')],
                model = dictConfig['defaultModel'] if 'model' not in dictCurrentStepConfig else dictCurrentStepConfig['model'],
                listInput = dictCurrentStepConfig['input']
            ).model_dump()

            step = getNextStep(dictCurrentStepConfig, None if 'content' in dictOutput and not dictOutput['content'] else dictOutput)

            print('\n')
        case 'command':
            stepTool.runCommand(dictCurrentStepConfig['input']['command'])
            step = getNextStep(dictCurrentStepConfig)
            print('\n')
        case 'generateCode':
            stepTool.generateCode(step, dictCurrentStepConfig['input'])
            step = getNextStep(dictCurrentStepConfig)
            print('\n')

    if 'bOutput2NextStep' in dictCurrentStepConfig and dictCurrentStepConfig['bOutput2NextStep']:
        dictPreviousOutput = dictOutput

    if 'outputSavePath' in dictCurrentStepConfig:
        with open(dictCurrentStepConfig['outputSavePath'], 'w', encoding = 'utf-8') as f:
            json.dump(dictOutput, f, indent = 4, ensure_ascii = False)