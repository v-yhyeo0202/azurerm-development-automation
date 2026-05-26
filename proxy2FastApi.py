import asyncio
from mitmproxy import http
import requests
import yaml

import dataStructure

with open('config.yml', 'r') as f:
    dictConfig = yaml.load(f, Loader = yaml.FullLoader)

class HttpExtractor:
    def __init__(self):
        self.listHttpLog = dataStructure.ListHttpLog(listHttpLog =[])
        self.lock = asyncio.Lock()

        return
    
    async def request(self, flow: http.HTTPFlow):
        match flow.request.method:
            case 'PUT' | 'PATCH':
                async with self.lock:
                    self.listHttpLog.listHttpLog.append(dataStructure.HttpLog(
                        method = flow.request.method,
                        url = flow.request.url,
                        requestBody = flow.request.content.decode('utf-8')
                    ))
        
        return
    
    async def response(self, flow: http.HTTPFlow):
        async with self.lock:
            for i in range(len(self.listHttpLog.listHttpLog)):
                if self.listHttpLog.listHttpLog[i].url == flow.request.url and self.listHttpLog.listHttpLog[i].responseBody == '':
                    self.listHttpLog.listHttpLog[i].responseBody = flow.response.content.decode('utf-8')
                    requests.post(f'http://localhost:{dictConfig["port"]["httpProxyListener"]}/logHttp', json = self.listHttpLog.listHttpLog[i].model_dump())

                    del self.listHttpLog.listHttpLog[i]

                    break

        return

addons = [HttpExtractor()]