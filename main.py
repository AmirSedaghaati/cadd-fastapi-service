import logging
import asyncio
import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel, conlist
from rdkit import Chem
from rdkit.Chem import Descriptors
from slowapi import Limiter
from slowapi.util import get_remote_address

# logging Setting 
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Limiter Setting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="CADD FastAPI Service", version="0.1.0")
app.state.limiter = limiter

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

class ScreenLibraryRequest(BaseModel):
    compounds: conlist(dict, min_length=1, max_length=200)

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
            logger.info(f"Compound not found: {name}")
            return {"compound_name": name, "CID": None, "fetch_status": "not_found"}
        
        props = await fetch_properties_by_cid(client, cid)
        await asyncio.sleep(REQUEST_DELAY_SECONDS)
        
        if not props:
            logger.warning(f"Failed to fetch properties for CID: {cid} ({name})")
            return {"compound_name": name, "CID": cid, "fetch_status": "property_error"}
        
        logger.info(f"Successfully resolved: {name} (CID: {cid})")
        return {"compound_name": name, "CID": cid, "fetch_status": "ok", **props}

@app.get("/")
def root():
    return {"service": "CADD FastAPI Service", "status": "running"}

@app.post("/fetch-descriptors")
@limiter.limit("10/minute")
async def fetch_descriptors(request: Request, compound_data: CompoundRequest):
    logger.info(f"API Request: /fetch-descriptors for {len(compound_data.compound_names)} items")
    semaphore = asyncio.Semaphore(5)  
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *(_resolve_one(client, name, semaphore) for name in compound_data.compound_names)
        )
    ok_count = sum(1 for r in results if r["fetch_status"] == "ok")
    return {"total_requested": len(compound_data.compound_names), "total_resolved": ok_count, "results": results}

def _lipinski_check(smiles: str) -> dict:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"valid_smiles": False}
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    passes = mw <= 500 and logp <= 5 and hbd <= 5 and hba <= 10
    return {
        "valid_smiles": True,
        "molecular_weight": round(mw, 2),
        "logp": round(logp, 2),
        "hbd": hbd,
        "hba": hba,
        "passes_lipinski": passes,
    }

@app.post("/screen-library")
@limiter.limit("10/minute")
def screen_library(request: Request, library_data: ScreenLibraryRequest):
    logger.info(f"API Request: /screen-library for {len(library_data.compounds)} compounds")
    results = []
    for compound in library_data.compounds:
        name = compound.get("name", "unknown")
        smiles = compound.get("smiles", "")
        descriptors = _lipinski_check(smiles)
        results.append({"compound_name": name, "smiles": smiles, **descriptors})
    passed = sum(1 for r in results if r.get("passes_lipinski") is True)
    return {"total_screened": len(results), "total_passed": passed, "results": results}
