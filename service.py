import os
import subprocess
import yaml

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

def initializePandoraDataApi():
    process = subprocess.Popen(
        ['make', 'run'],
        cwd = os.path.join(dictConfig['path']['pandora'], 'tools', 'data-api'),
        env = os.environ.copy()
    )

    return process