"""Capture screenshots of the running Streamlit app via the Chrome DevTools protocol.

    streamlit run app.py --server.port 8599   (in another terminal)
    python report/capture_screens.py
"""
import asyncio
import base64
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
APP = "http://localhost:8599/"
OUT = Path(__file__).resolve().parent / "figures"
PORT = 9333


class CDP:
    def __init__(self, ws):
        self.ws, self.n = ws, 0

    async def send(self, method, **params):
        self.n += 1
        mid = self.n
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(await self.ws.recv())
            if msg.get("id") == mid:
                return msg.get("result", {})

    async def js(self, expr):
        r = await self.send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        return r.get("result", {}).get("value")

    async def shot(self, name, height):
        await self.send("Emulation.setDeviceMetricsOverride", width=1400, height=height,
                        deviceScaleFactor=1, mobile=False)
        await asyncio.sleep(2)
        r = await self.send("Page.captureScreenshot", format="png")
        (OUT / name).write_bytes(base64.b64decode(r["data"]))
        print("saved", name)


CLICK_TEXT = """
(() => {
  const want = %s;
  const els = [...document.querySelectorAll('%s')];
  const el = els.find(e => e.innerText && e.innerText.trim() === want)
          || els.find(e => e.innerText && e.innerText.includes(want));
  if (!el) return 'not found: ' + want;
  el.click(); return 'clicked ' + want;
})()
"""


async def main():
    prof = tempfile.mkdtemp()
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                             f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}",
                             "--window-size=1400,1000", "about:blank"])
    try:
        for _ in range(30):
            try:
                tabs = json.loads(urllib.request.urlopen(f"http://localhost:{PORT}/json").read())
                break
            except OSError:
                time.sleep(0.5)
        ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
        async with websockets.connect(ws_url, max_size=50_000_000) as ws:
            cdp = CDP(ws)
            await cdp.send("Page.enable")
            await cdp.send("Emulation.setDeviceMetricsOverride", width=1400, height=1000,
                           deviceScaleFactor=1, mobile=False)
            await cdp.send("Page.navigate", url=APP)
            await asyncio.sleep(15)
            print(await cdp.js(CLICK_TEXT % (json.dumps("Try a sample"), "label")))
            await asyncio.sleep(4)
            await cdp.shot("webapp_home.png", 1000)
            print(await cdp.js(CLICK_TEXT % (json.dumps("Analyse crop"), "button")))
            await asyncio.sleep(12)
            await cdp.shot("webapp_result.png", 1520)
            print(await cdp.js(CLICK_TEXT % (json.dumps("How the AI reached this result"), "summary")))
            await asyncio.sleep(4)
            await cdp.js("window.scrollTo(0, 0)")
            h = await cdp.js("document.querySelector('details[open]').getBoundingClientRect().bottom + 20")
            await cdp.shot("webapp_explain_full.png", int(h or 2600))
            # Model performance tab
            await cdp.send("Emulation.setDeviceMetricsOverride", width=1400, height=1000,
                           deviceScaleFactor=1, mobile=False)
            await cdp.js("window.scrollTo(0,0)")
            print(await cdp.js(CLICK_TEXT % (json.dumps("Model performance"), "[role=tab]")))
            await asyncio.sleep(5)
            await cdp.shot("webapp_model.png", 1350)
    finally:
        proc.terminate()


asyncio.run(main())
