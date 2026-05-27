import datetime
import fastapi
import json
import os
import threading
import uvicorn
import yaml

import dataStructure

with open('config.yml') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

listHttpLog = dataStructure.ListHttpLog(listHttpLog = [])
lock = threading.Lock()
app = fastapi.FastAPI()

@app.post('/logHttp')
async def logHttp(httpLog: dataStructure.HttpLog):
    lock.acquire()
    listHttpLog.listHttpLog.append(httpLog)
    lock.release()

    return

@app.get('/saveHttpLog')
async def saveHttpLog(savePath: str):
    logPath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], savePath)

    if os.path.exists(logPath):
        renamedFile = f"{savePath.split('.')[0]}_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.{savePath.split('.')[1]}"
        renamedPath = os.path.join(dictConfig['path']['main'], dictConfig['path']['attachment'], dictConfig['resource'], renamedFile)
        os.rename(logPath, renamedPath)

    lock.acquire()

    with open(logPath, 'w') as f:
        json.dump(listHttpLog.model_dump(), f, indent = 4, ensure_ascii = False)

    listHttpLog.listHttpLog.clear()
    lock.release()

    return

uvicorn.run(app, host = 'localhost', port = dictConfig['port']['httpProxyListener'])