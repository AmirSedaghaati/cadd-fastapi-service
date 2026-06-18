# CADD FastAPI Service

A deployable REST API that wraps a computational drug discovery 
screening pipeline. Compound descriptor retrieval, Lipinski 
filtering, and docking result parsing are exposed as HTTP 
endpoints, making the pipeline callable from any automation 
tool, including n8n, without manual script execution.

## Why this exists

Most CADD pipelines live on one person's laptop. They work, 
but they are not usable by anyone else, not callable by 
automation workflows, and not deployable to a team environment. 
This project packages three core screening steps as a proper 
REST API so the pipeline can run as a service rather than a 
manual script.

## Endpoints

### POST /descriptors
Accepts a list of compound names. Queries the PubChem REST API, 
resolves names to CIDs, retrieves physicochemical descriptors 
(MW, XLogP, TPSA, HBD, HBA, CanonicalSMILES), and returns a 
structured JSON response. Unresolved compounds are flagged 
explicitly rather than silently dropped.

### POST /filter
Accepts descriptor data. Applies Lipinski Rule of Five filtering 
and a configurable TPSA threshold. Returns passing and failing 
compounds as separate lists with the applied thresholds recorded 
in the response.

### POST /parse-docking
Accepts AutoDock Vina docking results in CSV format. Ranks 
compounds by binding affinity, applies a configurable hit 
threshold, and returns a ranked hit list as structured JSON.

## Tech stack

| Component | Role |
|---|---|
| FastAPI | REST API framework |
| Python 3.11 | Core pipeline logic |
| pandas | Data manipulation |
| requests | PubChem API communication |
| RDKit | Lipinski filtering |
| Docker | Containerisation and deployment |
| PostgreSQL | Persistent storage of screening results |

## Status

Under active development. Endpoints are being built and 
tested in sequence. Core descriptor retrieval and Lipinski 
filtering are functional. Docking result parser and 
PostgreSQL integration are in progress.

## Run locally with Docker

```bash
docker build -t cadd-api .
docker run -p 8000:8000 cadd-api
```

API documentation available at http://localhost:8000/docs 
once the container is running.

## Related repositories

- [pubchem-metabolite-descriptor-fetcher](https://github.com/AmirSedaghaati/pubchem-metabolite-descriptor-fetcher) — batch descriptor retrieval pipeline this API is built around
- [vina-docking-pipeline](https://github.com/AmirSedaghaati/vina-docking-pipeline) — docking result parser this API exposes as an endpoint

## Author

Amir Sedaghati
[linkedin.com/in/amir-sedaghati](https://linkedin.com/in/amir-sedaghati) · 
[ORCID 0009-0002-6445-0329](https://orcid.org/0009-0002-6445-0329)
