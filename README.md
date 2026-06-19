# CADD FastAPI Service

A deployable REST API that wraps a computational drug discovery 
screening pipeline. Compound descriptor retrieval, Lipinski 
filtering, and docking result parsing, each exposed as an 
independent HTTP endpoint, containerised with Docker, and 
ready to integrate with any automation layer (n8n, Airflow, 
or a direct HTTP call from your lab's data system).

---

## Why this exists

Most CADD pipelines are local scripts. They work on the machine 
that built them and nowhere else. When a wet-lab team needs 
results, someone has to run the script manually, export a CSV, 
and send it by email.

This service removes that bottleneck. Each pipeline stage is an 
API endpoint. Your automation tool calls the endpoint, gets 
structured JSON back, and passes it to the next step — no manual 
intervention, no environment setup on the client side.

---

## Endpoints

### POST /fetch-descriptors
Accepts a list of compound names. Queries the PubChem REST API 
in batch. Returns molecular weight, XLogP, TPSA, H-bond donor 
and acceptor counts, and canonical SMILES for each compound. 
Compounds that cannot be resolved are flagged explicitly — 
nothing disappears silently from your dataset.

### POST /screen-library
Accepts a compound library as JSON. Applies Lipinski Rule of 
Five filtering via RDKit. Returns the filtered, ranked compound 
list. Affinity threshold is configurable per request.

### POST /parse-docking-results
Accepts AutoDock Vina output as JSON. Parses binding affinities. 
Applies a configurable hit threshold. Returns ranked hits with 
pass/fail flags as structured JSON ready for database insertion 
or downstream reporting.

---

## Tech stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Containerisation | Docker + Docker Compose |
| Cheminformatics | RDKit |
| Database | PostgreSQL |
| External data | PubChem REST API |
| Language | Python 3.11 |

---

## Run locally

```bash
git clone https://github.com/AmirSedaghaati/cadd-fastapi-service
cd cadd-fastapi-service
docker-compose up --build
```

API will be live at http://localhost:8000
Interactive docs at http://localhost:8000/docs

---

## Project status

Under active development. Endpoints are being built and tested 
against the same compound libraries used in published screening 
work (Biochemical and Biophysical Reports, 2025 — 
doi.org/10.1016/j.bbrep.2025.102171).

Current progress:
- [x] Repository structure and API skeleton
- [x] /fetch-descriptors endpoint
- [ ] /screen-library endpoint (in progress)
- [ ] /parse-docking-results endpoint
- [ ] Docker Compose full stack with PostgreSQL
- [ ] Integration test suite

---

## Related repositories

- [pubchem-metabolite-descriptor-fetcher](https://github.com/AmirSedaghaati/pubchem-metabolite-descriptor-fetcher) — batch descriptor retrieval pipeline (Python + R)
- [vina-docking-pipeline](https://github.com/AmirSedaghaati/vina-docking-pipeline) — AutoDock Vina result parser and hit ranker

---

## Contact

Amir Sedaghati  
aamirsedaghati@gmail.com  
linkedin.com/in/amir-sedaghati  
ORCID: 0009-0002-6445-0329
