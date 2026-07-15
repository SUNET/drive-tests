import aiohttp
import asyncio
import os
import random
from datetime import datetime
import sunetnextcloud

drv = sunetnextcloud.TestTarget()

g_loadtestcalls = os.environ.get("NextcloudLoadtestCalls")
if g_loadtestcalls is None:
    g_loadtestcalls = 10000
else:
    g_loadtestcalls = int(g_loadtestcalls)

g_min_frontendserver = os.environ.get("NextcloudMinFrontendServers")
if g_min_frontendserver is None:
    g_min_frontendserver = 1
else:
    g_min_frontendserver = int(g_min_frontendserver)

g_max_frontendserver = os.environ.get("NextcloudMaxFrontendServers")
if g_max_frontendserver is None:
    g_max_frontendserver = 3
else:
    g_max_frontendserver = int(g_max_frontendserver)

async def make_request(session, url, serverid, ocsheaders):
    session.cookie_jar.update_cookies({"SERVERID": serverid})
    startTime = datetime.now()
    async with session.get(url, headers=ocsheaders) as response:
        await response.text()
    return(datetime.now() - startTime).total_seconds()

async def run_concurrent_calls(calls, url, ocsheaders, nodebaseurl):
    totalTime = 0
    async with aiohttp.ClientSession() as session:
        tasks = []
        for call in range(calls):
            fe = random.randint(g_min_frontendserver,g_max_frontendserver)
            serverid = f"node{fe}.{nodebaseurl}"
            task = make_request(session, url, serverid, ocsheaders)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        totalTime = sum(results)

    return totalTime

message = ""
for fullnode in drv.nodestotest:
    nodeuser = drv.get_ocsuser(fullnode)
    nodepwd = drv.get_ocsuserapppassword(fullnode)
    nodebaseurl = drv.get_node_base_url(fullnode)
    url = drv.get_users_url(fullnode)
    print(f'Testing {url} with {g_loadtestcalls} calls on fe{g_min_frontendserver} to fe{g_max_frontendserver}')
    url = url.replace("$USERNAME$", nodeuser)
    url = url.replace("$PASSWORD$", nodepwd)
    message += f"{g_loadtestcalls} calls to {nodebaseurl:<30}"

    totalTime = asyncio.run(run_concurrent_calls(g_loadtestcalls, url, drv.ocsheaders, nodebaseurl))
    message += f"Total: {totalTime:<3.1f}s - Per call: {totalTime/g_loadtestcalls:<3.1f}s \n"

print(f'{message}')
