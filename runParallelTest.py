import asyncio
import json
import yaml

import stepTool

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

def createTestTask(httpProxyIndex, test):
    task = asyncio.create_task(stepTool.runCommand({
        'command': [
            ['make', 'testacc'],
            ['curl', f"http://localhost:{dictConfig['port']['httpProxy'][httpProxyIndex]['listener']}/saveHttpLog?savePath=httpLog_{test}.json"]
        ],
        'env': {
            'TEST': f"./{dictConfig['path']['services']}",
            'TESTARGS': f'-test.parallel 1 -test.run={test}',
            'TESTTIMEOUT': '1440m',
            'http_proxy': f"http://localhost:{dictConfig['port']['httpProxy'][httpProxyIndex]['sender']}",
            'https_proxy': f"http://localhost:{dictConfig['port']['httpProxy'][httpProxyIndex]['sender']}"
        }
    }))

    return task

def runParallelTest(dictInput):
    with open(dictInput['testListPath'], 'r') as f:
        listTest = json.load(f)['listTest']

    dictTask = {}

    for i in range(dictConfig['nHttpProxy']):
        dictTask[createTestTask(i, listTest.pop(0))] = i

    while True:
        doneTask, _ = asyncio.run(asyncio.wait(dictTask.keys(), return_when = asyncio.FIRST_COMPLETED))
        httpProxyIndex = dictTask[doneTask[0]]
        del dictTask[doneTask[0]]

        if len(listTest) > 0:
            dictTask[createTestTask(httpProxyIndex, listTest.pop(0))] = httpProxyIndex
        else:

            break

    return