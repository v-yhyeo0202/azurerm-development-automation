dictIndex = {}

def generateIndex(step, dictStepConfig, endIndex):
    if step in dictIndex:
        dictIndex[step] += 1

        if dictIndex[step] == endIndex:

            return ''
    else:
        dictIndex[step] = 0

    return dictStepConfig['nextStep']