dictIndex = {}

def generateIndex(dictStepConfig, indexKey, endIndex):
    if indexKey in dictIndex:
        dictIndex[indexKey] += 1

        if dictIndex[indexKey] == endIndex:

            return dictStepConfig['nextStep']
    else:
        dictIndex[indexKey] = 0

    return dictStepConfig['loopStep']