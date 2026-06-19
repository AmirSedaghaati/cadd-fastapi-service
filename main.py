from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import time

app = FastAPI(
    title="CADD FastAPI Service",
    description="REST API wrapping a computational drug discovery screening pipeline.",
    version="0.1.0",
)

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

PROPERTIES = [
    "MolecularFormula",
    "MolecularWeight",
    "XLogP",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "TPSA",
    "RotatableBondCount",
    "InChIKey",
    "CanonicalSMILES",
]

REQUEST_DELAY_SECONDS = 0.5
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0


class CompoundRequest(BaseModel):
    compound_names: list[str]


def _request_with_retry(url, timeout=10):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code >= 500:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue
            return response
        except requests.exceptions.RequestException:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    return None


def fetch_cid_by_name(compound_name):
    url = f"{PUBCHEM_BASE}/compound/name/{requests.utils.quote(compound_name)}/cids/JSON"
    response = _request_with_retry(url)

    if response is None:
        return None
    if response.status_code == 200:
        cids = response.json().get("IdentifierList", {}).get("CID", [])
        return cids[0] if cids else None
    return None


def fetch_properties_by_cid(cid):
    props_str = ",".join(PROPERTIES)
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/{props_str}/JSON"
    response = _request_with_retry(url)

    if response is None:
        return {}
    if response.status_code == 200:
        prop_table = response.json().get("PropertyTable", {}).get("Properties", [])
        return prop_table[0] if prop_table else {}
    return {}


@app.get("/")
def root():
    return {"service": "CADD FastAPI Service", "status": "running"}


@app.post("/fetch-descriptors")
def fetch_descriptors(request: CompoundRequest):
    if not request.compound_names:
        raise HTTPException(status_code=400, detail="compound_names list cannot be empty.")

    results = []

    for name in request.compound_names:
        cid = fetch_cid_by_name(name)
        time.sleep(REQUEST_DELAY_SECONDS)

        if cid is None:
            results.append({"compound_name": name, "CID": None, "fetch_status": "not_found"})
            continue

        props = fetch_properties_by_cid(cid)
        time.sleep(REQUEST_DELAY_SECONDS)

        if not props:
            results.append({"compound_name": name, "CID": cid, "fetch_status": "property_error"})
            continue

        record = {"compound_name": name, "CID": cid, "fetch_status": "ok"}
        record.update(props)
        results.append(record)

    ok_count = sum(1 for r in results if r["fetch_status"] == "ok")

    return {
        "total_requested": len(request.compound_names),
        "total_resolved": ok_count,
        "results": results,
    }
