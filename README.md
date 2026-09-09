# CADD FastAPI Service

A deployable REST API that wraps a computational drug discovery 
screening pipeline. Compound descriptor retrieval, Lipinski 
filtering, and docking result parsing, each exposed as an 
independent HTTP endpoint, containerised with Docker.

---

## Why this exists

Most CADD pipelines are local scripts. They work on the machine 
that built them and nowhere else. When a wet-lab team needs 
results, someone has to run the script manually, export a CSV, 
and send it by email.

Your automation tool calls the endpoint, gets 
structured JSON back, and passes it to the next step, no manual 
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
Five screening via RDKit to each compound. Returns the full 
list annotated with pass/fail status for each compound — 
nothing is removed from the response. Rule of Five thresholds 
are currently fixed, not configurable per request.

### POST /parse-docking-results *(planned — not yet implemented)*
Will accept AutoDock Vina output as JSON, parse binding affinities, apply a
configurable hit threshold, and return ranked hits as structured JSON. See
Project Status below for current progress.

---

## Tech stack

| Layer | Technology | Status |
|---|---|---|
| API framework | FastAPI | ✅ in use |
| Containerisation | Docker + Docker Compose | ✅ in use |
| External data | PubChem REST API | ✅ in use |
| Language | Python 3.11 | ✅ in use |
| Cheminformatics | RDKit | ✅ in use |
| Database | PostgreSQL | 🚧 planned for persistence layer |

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

Under active development. /fetch-descriptors and /screen-library are
implemented and working. /parse-docking-results is planned (see roadmap below).

This is an independent portfolio project. It was not used in, and is not
connected to, any of my published research.

Current progress:
- [x] Repository structure and API skeleton
- [x] /fetch-descriptors endpoint
- [x] /screen-library endpoint
- [ ] /parse-docking-results endpoint
- [ ] Docker Compose full stack with PostgreSQL
- [x] Integration test suite
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
