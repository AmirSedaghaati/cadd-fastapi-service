import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist

app = FastAPI(title="CADD FastAPI Service", version="0.1.0")

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PROPERTIES = [
    "MolecularFormula", "MolecularWeight", "XLogP",
    "HBondDonorCount", "HBondAcceptorCount", "TPSA",
    "RotatableBondCount", "InChIKey", "CanonicalSMILES",
]
MAX_BATCH_SIZE = 50
REQUEST_DELAY_SECONDS = 0.5


class CompoundRequest(BaseModel):
    compound_names: conlist(str, min_length=1, max_length=MAX_BATCH_SIZE)


async def fetch_cid_by_name(client: httpx.AsyncClient, name: str) -> int | None:
    url = f"{PUBCHEM_BASE}/compound/name/{httpx.QueryParams({'_': name})['_']}/cids/JSON"
    response = await client.get(url, timeout=10)
    if response.status_code != 200:
        return None
    cids = response.json().get("IdentifierList", {}).get("CID", [])
    return cids[0] if cids else None


async def fetch_properties_by_cid(client: httpx.AsyncClient, cid: int) -> dict:
    props_str = ",".join(PROPERTIES)
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/{props_str}/JSON"
    response = await client.get(url, timeout=10)
    if response.status_code != 200:
        return {}
    table = response.json().get("PropertyTable", {}).get("Properties", [])
    return table[0] if table else {}


async def _resolve_one(client: httpx.AsyncClient, name: str, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        cid = await fetch_cid_by_name(client, name)
        await asyncio.sleep(REQUEST_DELAY_SECONDS)
        if cid is None:
            return {"compound_name": name, "CID": None, "fetch_status": "not_found"}
        props = await fetch_properties_by_cid(client, cid)
        await asyncio.sleep(REQUEST_DELAY_SECONDS)
        if not props:
            return {"compound_name": name, "CID": cid, "fetch_status": "property_error"}
        return {"compound_name": name, "CID": cid, "fetch_status": "ok", **props}


@app.get("/")
def root():
    return {"service": "CADD FastAPI Service", "status": "running"}


@app.post("/fetch-descriptors")
async def fetch_descriptors(request: CompoundRequest):
    semaphore = asyncio.Semaphore(5)  
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *(_resolve_one(client, name, semaphore) for name in request.compound_names)
        )
    ok_count = sum(1 for r in results if r["fetch_status"] == "ok")
    return {"total_requested": len(request.compound_names), "total_resolved": ok_count, "results": results}
