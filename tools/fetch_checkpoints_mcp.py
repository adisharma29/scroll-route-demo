
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
                out = {}
                for q in ["Tumakuru, Karnataka", "Chitradurga, Karnataka", "Hubballi, Karnataka", "Belagavi, Karnataka", "Calangute Beach, Goa"]:
                    res = await s.call_tool("vyntel_google_maps", {"action": "search", "query": q})
                    text = res.content[0].text if res.content else ""
                    data = json.loads(text)
                    inner = data.get("result")
                    if isinstance(inner, str): data = json.loads(inner)
                    places = (data.get("data") or {}).get("places") or (data.get("data") or {}).get("results") or []
                    if places:
                        p = places[0]
                        out[q] = {k: p.get(k) for k in ("name","lat","lng","ftid","formattedAddress")}
                open("/tmp/checkpoints.json","w").write(json.dumps(out, indent=1))
                print(json.dumps(out, indent=1)[:1200])
asyncio.run(main())
