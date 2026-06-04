import os
import subprocess
import yaml

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

dictEnvironment = os.environ.copy()
venvPath = os.path.join(dictConfig['path']['main'], f"venv-{dictConfig['path']['code']}", 'bin', 'activate')

def initializePandoraDataApi(dictInput):
    process = subprocess.Popen(
        ['make', 'run'],
        cwd = os.path.join(dictConfig['path']['pandora'], 'tools', 'data-api'),
        env = dictEnvironment
    )

    return [process]

def initializeHttpProxy(dictInput):
    listProcess = []

    for i in range(dictConfig['nHttpProxy']):
        listProcess.append(subprocess.Popen(
            f"source {venvPath}; mitmdump -s {os.path.join(dictConfig['path']['main'], dictConfig['path']['code'], 'proxy2FastApi.py')} -p {dictConfig['port']['httpProxy'][i]['sender']} -q",
            env = dictEnvironment,
            executable = '/bin/bash',
            shell = True
        ))

    return listProcess

def initializeHttpProxyListener(dictInput):
    listProcess = []

    for i in range(dictConfig['nHttpProxy']):
        listProcess.append(subprocess.Popen(
            f'source {venvPath}; python httpProxyListener.py -p {dictConfig["port"]["httpProxy"][i]["listener"]}',
            env = dictEnvironment,
            executable = '/bin/bash',
            shell = True
        ))

    return listProcess