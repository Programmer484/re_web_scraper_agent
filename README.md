## Overview

This project is a Python-based MVP agent that queries **RentCast's ****`/rental-listings`**** API** to find rental properties matching hard-coded search criteria. It normalizes the data into a clean JSON structure suitable for use in a future web backend or agent chain.

---

## Project Structure

```
project_root/
│  README.md               # This file
│  .env                    # Stores RENTCAST_API_KEY (not committed)
│  requirements.txt        # Python dependencies
└─ src/
   ├─ main.py              # Entrypoint: orchestrates the flow using Graphite
   ├─ config.py            # Configuration constants, API key loading
   ├─ models.py            # Pydantic models: SearchQuery, Listing
   └─ nodes/
      ├─ profile_builder.py # Builds hard-coded SearchQuery
      ├─ rentcast_node.py   # Calls RentCast API and retrieves raw listings
      └─ normalizer.py      # Converts raw listings to unified Listing models
```

---

## Logic Flow

### 1️⃣ Input Preparation (`nodes/profile_builder.py`)

* Defines a `SearchQuery` dataclass (e.g. `city`, `state`, `max_price`, `beds`, `baths`, `amenities`).
* Returns a hard-coded instance of `SearchQuery` for this MVP.

### 2️⃣ API Request (`nodes/rentcast_node.py`)

* Loads `RENTCAST_API_KEY` from `.env`.
* Builds query parameters from `SearchQuery`.
* Sends GET request to RentCast's `/rental-listings` endpoint using `httpx`.
* Returns raw listing JSON (array of properties).

### 3️⃣ Normalization (`nodes/normalizer.py`)

* Maps raw RentCast listing fields to a unified `Listing` Pydantic model:

  * `price`
  * `address`
  * `beds`
  * `baths`
  * `amenities`
  * `source_url`
  * `timestamp`
* Deduplicates and validates data.

### 4️⃣ Orchestration (`src/main.py`)

* Wires together the flow using **Graphite**:

  * Calls profile builder → rentcast node → normalizer.
* Outputs final listings as JSON to stdout (or optionally writes to `results.json`).

---

## Dependencies

* `httpx` — async HTTP client
* `pydantic` — data validation
* `python-dotenv` — load API keys from `.env`
* `graphite-ai` — node orchestration

Install:

```bash
pip install -r requirements.txt
```

---

## Running the Agent

1. Activate environment:

   ```bash
   source .venv/bin/activate
   ```
2. Run:

   ```bash
   python src/main.py
   ```
3. View results:

   * Listings will print to console as JSON.
   * Modify `main.py` to save output to a file if desired.

---

## Future Enhancements

* Replace hard-coded query with dynamic input (CLI args, JSON payload, API call)
* Add caching (e.g. Redis) to avoid repeat API calls
* Store results in a database (e.g. Postgres)
* Integrate into a web API or agent chain (FastAPI + Uvicorn wrapper)
* Add cost tracking for API usage
* Introduce fallback (search + scraping) if RentCast data gaps are discovered

---

## Notes

* This agent currently relies solely on RentCast. No scraping or search engine fallback is included at this stage.
* The project is structured to make future embedding in a larger system easy (clean input/output, modular nodes).

---

**End of README** — This document reflects the current RentCast-only logic flow and filenames.
