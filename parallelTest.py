import asyncio
import concurrent
import re
import yaml

import stepTool

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

def runTestCommand(httpProxyIndex, test):
    stepTool.runCommand({
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
    })

    return

def createTestTask(loop, pool, httpProxyIndex, test):
    task = asyncio.ensure_future(loop.run_in_executor(pool, runTestCommand, httpProxyIndex, test))

    return task

async def runTestAsync(dictInput):
    reTest = re.compile(dictInput['testRegex'])
    listTest = []

    with open(dictInput['testPath'], 'r') as f:
        for line in f:
            match = reTest.search(line)

            if match:
                listTest.append(match.group())

    loop = asyncio.get_running_loop()
    dictTask = {}

    with concurrent.futures.ThreadPoolExecutor() as pool:
        for i in range(dictConfig['nHttpProxy']):
            dictTask[createTestTask(loop, pool, i, listTest.pop(0))] = i

        while True:
            doneTask, _ = await asyncio.wait(dictTask.keys(), return_when = asyncio.FIRST_COMPLETED)
            doneTask = doneTask.pop()
            httpProxyIndex = dictTask[doneTask]
            del dictTask[doneTask]

            if len(listTest) > 0:
                dictTask[createTestTask(loop, pool, httpProxyIndex, listTest.pop(0))] = httpProxyIndex
            else:

                break

    return

def runTest(dictInput):
    asyncio.run(runTestAsync(dictInput))

    return