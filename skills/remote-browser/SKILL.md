# Skill: `remote-browser`

## Purpose

`remote-browser` provides Hermes agents with the ability to control a remote
Brave browser running on the user's workstation via Chrome DevTools Protocol
(CDP) on `localhost:9222`.

It is a **browser automation skill** — it handles navigation, clicking, typing,
screenshots, PDFs, JavaScript execution, and network inspection.

The skill never launches or restarts a browser. The browser is assumed to be
running already with a persistent reverse SSH tunnel exposing port 9222.

---

# Connection

The CDP endpoint is always:

```
http://127.0.0.1:9222
```

## Pre-flight Check

Before every task:

1. Fetch version info:
   ```
   GET http://127.0.0.1:9222/json/version
   ```
2. Extract the `webSocketDebuggerUrl` from the response.
3. Connect to the WebSocket debugger URL to send CDP commands.

**Never SSH into another machine.** The tunnel already exists.

## Pre-flight script

Run this to verify the browser is reachable before starting a task:

```bash
curl -s http://127.0.0.1:9222/json/version | python3 -m json.tool 2>/dev/null && echo "Browser reachable" || echo "Browser NOT reachable — check SSH tunnel"
```

---

# Browser Lifecycle

- The browser is **already running** on the workstation.
- The reverse tunnel **already exists**.
- The browser profile should be **reused** — cookies, sessions, and extensions
  remain intact.
- **Never launch another browser** unless the user explicitly requests it.

---

# Capabilities

## Navigation

| Action | CDP Method | Notes |
|--------|-----------|-------|
| Open URL | `Page.navigate` | `url` param |
| Reload | `Page.reload` | |
| Get current URL | `Page.getFrameTree` | |
| Get page title | `Runtime.evaluate` | `document.title` |
| Wait for navigation | `Page.loadEventFired` | Bind once before navigate |

## DOM Interaction

| Action | CDP Method / Approach | Notes |
|--------|----------------------|-------|
| Click element | `Runtime.evaluate` | `el.click()` |
| Type text | `Runtime.evaluate` | `el.value = ''; el.value = text;` + dispatch `input` |
| Get innerText | `Runtime.evaluate` | `el.innerText` |
| Get innerHTML | `Runtime.evaluate` | `el.innerHTML` |
| Get attribute | `Runtime.evaluate` | `el.getAttribute(name)` |
| Scroll into view | `Runtime.evaluate` | `el.scrollIntoView({block:'center'})` |
| Wait for element | `Runtime.evaluate` | Poll `document.querySelector(sel)` until truthy |
| Find all matching | `Runtime.evaluate` | `document.querySelectorAll(sel)` + map |

## Screenshots

```python
result = await page.send_command("Page.captureScreenshot", {
    "format": "png",
    "captureBeyondViewport": True  # full page
})
```

## PDF Generation

```python
result = await page.send_command("Page.printToPDF", {
    "printBackground": True
})
```

## Tab Management

| Action | Endpoint |
|--------|----------|
| List tabs | `GET /json` |
| Open new tab | `PUT /json/new?url=...` |
| Switch to tab | Connect to its WS URL |
| Close tab | `GET /json/close/{id}` |
| Activate tab | `GET /json/activate/{id}` |

**Reuse existing tabs whenever practical.** Prefer navigating an existing tab
over opening new ones.

## Network Inspection

```python
await page.send_command("Network.enable")
# Listen for Network.requestWillBeSent, Network.responseReceived, etc.

# Get response body
body = await page.send_command("Network.getResponseBody", {
    "requestId": request_id
})
```

## Console Logs

```python
await page.send_command("Console.enable")
# Or capture via Runtime.consoleAPICalled events
```

## File Uploads

```python
await page.send_command("DOM.setFileInputFiles", {
    "files": ["/path/to/file.pdf"],
    "objectId": file_input_node_id
})
```

---

# Python Recipe (Standalone)

Use this pattern for one-off browser automation tasks:

```python
#!/usr/bin/env python3
import asyncio
import json
import httpx
import websockets

async def get_ws_url():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://127.0.0.1:9222/json/version")
        return resp.json()["webSocketDebuggerUrl"]

async def send_cmd(ws, method, params=None):
    if params is None:
        params = {}
    cmd_id = int(asyncio.get_running_loop().time() * 1000)
    payload = {"id": cmd_id, "method": method, "params": params}
    await ws.send(json.dumps(payload))
    while True:
        resp = json.loads(await ws.recv())
        if resp.get("id") == cmd_id:
            return resp.get("result")

async def main():
    ws_url = await get_ws_url()
    async with websockets.connect(ws_url) as ws:
        await send_cmd(ws, "Page.enable")
        await send_cmd(ws, "Page.navigate", {"url": "https://example.com"})

        # Wait for load
        async for msg in ws:
            data = json.loads(msg)
            if data.get("method") == "Page.loadEventFired":
                break

        result = await send_cmd(ws, "Runtime.evaluate", {
            "expression": "document.title",
            "returnByValue": True
        })
        print(f"Title: {result['result']['value']}")

asyncio.run(main())
```

---

# Responsibilities

The skill may:

- Navigate to URLs
- Click, type, scroll, and interact with page elements
- Extract text, attributes, and HTML from the page
- Take screenshots and generate PDFs
- Inspect network requests and responses
- Read console logs
- Open, switch, and close tabs
- Execute arbitrary JavaScript in the page context
- Upload files through file input elements

The skill may NOT:

- Launch or restart the browser
- Clear browser data (cookies, cache, local storage)
- Log out of any website
- Install or remove extensions
- Change browser settings (homepage, search engine, etc.)
- Modify the browser profile
- Recreate the SSH tunnel
- Close unrelated tabs without explicit instruction

---

# Recovery

If the CDP WebSocket connection fails:

1. **Retry** up to 3 times with a 2-second delay between attempts.
2. **Verify** that `http://127.0.0.1:9222/json/version` is reachable via HTTP.
3. **Reconnect** by fetching a fresh `webSocketDebuggerUrl`.
4. **Report** the problem clearly if the endpoint remains unavailable after 3 retries.

**Do not attempt to restart Brave or recreate the SSH tunnel.** That is the
user's responsibility.

---

# Common Pitfalls

1. **Trying to launch a local browser.** The browser is on the user's
   workstation, not this server. Never run `brave`, `google-chrome`, or any
   browser binary.

2. **Not checking the pre-flight.** Always verify `localhost:9222` responds
   before starting a task.

3. **State loss on reconnect.** CDP WebSocket connections are stateless. After
   reconnecting, re-enable any domains you need (`Page.enable`,
   `Network.enable`, `Console.enable`, `Runtime.enable`).

4. **Not dispatching synthetic events after setting values.** When typing via
   `el.value = text`, also dispatch an `input` event so the page's JS framework
   picks up the change.

5. **Forgetting to await `loadEventFired`.** Navigate, then wait for the page
   to load before interacting.

6. **Assuming tab 0 is the target.** List tabs with `GET /json` and select the
   right one by URL or title.

---

# Verification Checklist

- [ ] `http://127.0.0.1:9222/json/version` responds with browser info
- [ ] `webSocketDebuggerUrl` extracted and connectable
- [ ] `Runtime.evaluate` executes JS and returns results
- [ ] `Page.navigate` loads a URL and fires `Page.loadEventFired`
- [ ] Screenshots and PDFs produced when requested
- [ ] Existing tabs reused (prefer navigation over new tab creation)
- [ ] Recovery: 3 retry attempts before reporting failure
- [ ] Safety: no browser settings, data, or extensions touched without
      explicit instruction