def addService(dictStepConfig, step, nextStep):
    stepType = 'service'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {},
        'nextStep': nextStep
    }

    return

def addControlFlow(dictStepConfig, step, loopStep, nextStep):
    stepType = 'controlFlow'
    dictStepConfig['step'][step] = {
        'type': stepType,
        'input': {
            'packageName': 'flowGenerator',
        },
        'loopStep': loopStep,
        'nextStep': nextStep
    }

    return