import json
import langchain_core
import yaml

import dataStructure
import flowGenerator
import stepTool

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

try:
    dictStepConfig = flowGenerator.getFlow()
    step = dictStepConfig['firstStep']
    dictOutput = None

    while step:
        print('debug6')
        dictCurrentStepConfig = dictStepConfig['step'][step]

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

                step = stepTool.getNextStep(dictCurrentStepConfig, None if 'content' in dictOutput and not dictOutput['content'] else dictOutput)
                print('\n')
            case 'command':
                dictOutput = stepTool.runCommand(dictCurrentStepConfig['input'])
                step = stepTool.getNextStep(dictCurrentStepConfig)
                print('\n')
            case 'generateCode':
                stepTool.generateCode(step, dictCurrentStepConfig['input'])
                step = stepTool.getNextStep(dictCurrentStepConfig)
                print('\n')
            case 'service':
                stepTool.initializeService(step, dictCurrentStepConfig['input'])
                step = stepTool.getNextStep(dictCurrentStepConfig)
                print('\n')
            case 'controlFlow':
                step = stepTool.controlFlow(step, dictCurrentStepConfig)

        if 'outputSavePath' in dictCurrentStepConfig:
            with open(dictCurrentStepConfig['outputSavePath'], 'w', encoding = 'utf-8') as f:
                json.dump(dictOutput, f, indent = 4, ensure_ascii = False)
finally:
    if len(stepTool.listProcess) > 0:
        stepTool.terminateService()