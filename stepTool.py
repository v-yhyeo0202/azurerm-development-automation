import asyncio
import glob
import copilot
import langchain_core
import langchain_core.language_models
import os
import re
import subprocess
import yaml

import codeGenerator
import flowGenerator
import service

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

class CopilotModel(langchain_core.language_models.chat_models.BaseChatModel):
    generation: str = ''
    reJson: re.Pattern = re.compile(r'```json\s*(\{(?:.|\s)*\})\s*```')
    bSchema: bool = False

    def __init__(self):
        super().__init__()

        return

    async def send(self, listInput, _model):
        self.generation = ''

        async with copilot.CopilotClient(
            copilot.SubprocessConfig(
                cwd = dictConfig['path']['azurerm']
            )
        ) as client:
            async with await client.create_session(
                model = _model,
                reasoning_effort = None if _model == 'claude-haiku-4.5' else 'High',
                on_permission_request = copilot.session.PermissionHandler.approve_all,
                streaming = True
            ) as session:
                doneEvent = asyncio.Event()

                def onEvent(event):
                    match event.data:
                        case copilot.generated.session_events.AssistantMessageDeltaData() | copilot.generated.session_events.AssistantReasoningDeltaData() as data:
                            delta = data.delta_content or ''
                            print(delta, end = '', flush = True)

                            if i == len(listInput) - 1:
                                self.generation += delta
                        case copilot.generated.session_events.SessionIdleData():
                            doneEvent.set()

                session.on(onEvent)
                
                for i, dictInput in enumerate(listInput):
                    print('Running Copilot with input:')
                    print(f"Input: {dictInput['prompt']}")
                    print()

                    await session.send(dictInput['prompt'], attachments = dictInput['attachments'] if 'attachments' in dictInput else None)
                    await doneEvent.wait()
                    doneEvent.clear()

        if self.bSchema:
            listGeneration = self.generation.split('\n\n')

            for i in range(len(listGeneration) - 1, -1, -1):
                if self.reJson.search(listGeneration[i]):
                    self.generation = listGeneration[i]

                    break
        else:
            self.generation = ''

        return self.generation

    def _generate(self, dummyMessage, stop = None, model = dictConfig['defaultModel'], listInput = None):
        listExpandedInput = []

        for dictInput in listInput:
            if 'attachments' in dictInput:
                listExpandedInput.append(
                    {
                        'prompt': dictInput['prompt'],
                        'attachments': [copilot.session.FileAttachment(type = 'file', path = j) for i in dictInput['attachments'] for j in glob.glob(i)]
                    }
                )
            else:
                listExpandedInput.append(dictInput)

        asyncio.run(self.send(listExpandedInput, model))
        chatResult = langchain_core.outputs.ChatResult(
            generations = [
                langchain_core.outputs.ChatGeneration(
                    message = langchain_core.messages.AIMessage(self.generation)
                )
            ]
        )

        return chatResult

    def with_structured_output(self, schema):
        self.bSchema = True
        llm = self.bind()
        outputParser = langchain_core.output_parsers.PydanticOutputParser(pydantic_object = schema)

        return llm | outputParser

    @property
    def _llm_type(self):

        return "copilot"

def runCommand(dictInput):
    print(f"Running command:")

    dictOutput = {
        'commandOutput': ''
    }

    for listSubCommand in dictInput['command']:
        if isinstance(listSubCommand, str):
            print(listSubCommand)
        else:
            print(' '.join(listSubCommand))

        dictEnvironment = os.environ.copy()

        if 'env' in dictInput:
            dictEnvironment.update(dictInput['env'])

        result = subprocess.run(
            listSubCommand,
            cwd = dictInput['cwd'] if 'cwd' in dictInput else dictConfig['path']['azurerm'],
            env = dictEnvironment,
            capture_output = True,
            text = True,
            shell = isinstance(listSubCommand, str)
        )

        print(result.stdout)
        print(result.stderr)
        dictOutput['commandOutput'] += f'{result.stdout}\n{result.stderr}\n'

    return dictOutput

def generateCode(dictInput, functionName):
    if os.path.exists(dictInput['path']):
        print(f"File {dictInput['path']} already exists, skipping code generation")

        return

    print(f'Generating code or config with {functionName}')

    functionName = functionName[0].lower() + functionName[1:]
    code = getattr(codeGenerator, functionName)()
    directoryPath = os.path.dirname(dictInput['path'])
    os.makedirs(directoryPath, exist_ok = True)

    with open(dictInput['path'], 'w') as f:
        f.write(code)

    return

listProcess = []

def initializeService(dictInput, functionName):
    print(f'Initializing service with {functionName}')

    functionName = functionName[0].lower() + functionName[1:]
    listProcess.extend(getattr(service, functionName)(dictInput))

    return

def terminateService():
    print('Terminating services')

    for process in listProcess:
        process.terminate()
        process.wait()

    return

def callFunction(packageName, functionName, dictInput):
    print(f'Calling {functionName}')

    functionName = functionName[0].lower() + functionName[1:]
    getattr(packageName, functionName)(dictInput)

    return

def controlFlow(dictStepConfig, step):
    print(f'Controlling flow with {step}')

    functionName = step[0].lower() + step[1:]
    nextStep = getattr(flowGenerator, functionName)(dictStepConfig)

    return nextStep

def getNextStep(dictCurrentStepConfig, dictOutput = None):
    if 'nextStep' not in dictCurrentStepConfig:

        return None

    if dictOutput and isinstance(dictCurrentStepConfig['nextStep'], dict):
        key = list(dictCurrentStepConfig['nextStep'])[0]
        nextStep = dictCurrentStepConfig['nextStep'][key][dictOutput[key]]
    else:
        nextStep = dictCurrentStepConfig['nextStep']

    return nextStep