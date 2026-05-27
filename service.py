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

    return process

def initializeHttpProxy(dictInput):
    process = subprocess.Popen(
        f"source {venvPath}; mitmdump -s {os.path.join(dictConfig['path']['main'], dictConfig['path']['code'], 'proxy2FastApi.py')} -p {dictConfig['port']['httpProxy']}",
        env = dictEnvironment,
        executable = '/bin/bash',
        shell = True
    )

    return process

def initializeHttpProxyListener(dictInput):
    process = subprocess.Popen(
        f'source {venvPath}; python httpProxyListener.py',
        env = dictEnvironment,
        executable = '/bin/bash',
        shell = True
    )

    return process