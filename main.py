import datetime
import json
import langchain_core
import os
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
        print(f'Step: {step}')
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
            case 'command':
                dictOutput = stepTool.runCommand(dictCurrentStepConfig['input'])
                step = stepTool.getNextStep(dictCurrentStepConfig)
            case 'generateCode':
                stepTool.generateCode(dictCurrentStepConfig['input'], step)
                step = stepTool.getNextStep(dictCurrentStepConfig)
            case 'service':
                stepTool.initializeService(dictCurrentStepConfig['input'], step)
                step = stepTool.getNextStep(dictCurrentStepConfig)
            case 'controlFlow':
                step = stepTool.controlFlow(dictStepConfig, step)

        print('\n')

        if 'outputSavePath' in dictCurrentStepConfig:
            if 'bKeepSaveFile' in dictCurrentStepConfig and dictCurrentStepConfig['bKeepSaveFile'] and os.path.exists(dictCurrentStepConfig['outputSavePath']):
                renamedFile = f"{dictCurrentStepConfig['outputSavePath'].split('.')[0]}_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.{dictCurrentStepConfig['outputSavePath'].split('.')[1]}"
                renamedPath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], renamedFile)
                os.rename(dictCurrentStepConfig['outputSavePath'], renamedPath)

            with open(dictCurrentStepConfig['outputSavePath'], 'w', encoding = 'utf-8') as f:
                json.dump(dictOutput, f, indent = 4, ensure_ascii = False)
finally:
    if len(stepTool.listProcess) > 0:
        stepTool.terminateService()