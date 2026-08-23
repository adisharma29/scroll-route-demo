
import asyncio, json, re, os, yaml
import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

cfg = yaml.safe_load(open(os.path.expanduser("~/.hermes/config.yaml")))
server = (cfg.get("mcp_servers") or {}).get("vyntel") or {}
url, hdrs = server.get("url"), server.get("headers") or {}

def repl(m): return os.environ.get(m.group(1), "")
headers = {str(k): re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, str(v)) for k, v in hdrs.items()}

async def main():
    async with httpx2.AsyncClient(headers=headers, timeout=120) as hc:
        async with streamable_http_client(url, http_client=hc) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()
                res = await s.call_tool("vyntel_google_maps", {
                    "action": "routes",
                    "from": "Whitefield, Bengaluru",
                    "to": "Calangute, Goa",
                    "polyline": True,
                })
                text = res.content[0].text if res.content else ""
                print("RAW TEXT:", text[:500])
                try:
                    data = json.loads(text)
                    inner = data.get("result")
                    if isinstance(inner, str):
                        data = json.loads(inner)
                except Exception as e:
                    print("parse err:", e); data = {}
                open("/tmp/route_raw.json", "w").write(json.dumps(data))
                print(type(data), str(data)[:400])
                if isinstance(data, dict):
                    open("/tmp/route_raw.json", "w").write(json.dumps(data))
                d = (data or {}).get("data") or {}
                print("routes:", d.get("count"))
                print("polyline points:", len(d.get("polyline") or []))

asyncio.run(main())
