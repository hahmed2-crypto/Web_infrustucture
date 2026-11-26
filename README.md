# Rwanda Healthcare Locator & Public Health Insights

A data-driven web application that helps residents, students, and visitors in Rwanda locate nearby hospitals, clinics, and pharmacies while viewing national public health indicators.

- **Demo Video:** [Watch Demo Video on YouTube](YOUR_YOUTUBE_LINK_HERE)
- **Live Load Balancer URL:** http://35.179.97.207

---

## Features & Practical Value
- **Location-Based Facility Search:** Select from preset Rwandan districts and neighborhoods (Kigali City, Kimironko, Nyarugenge, Bumbogo/ALU Area, Huye, Musanze, Rubavu) or search any custom town across Rwanda.
- **Category Filtering:** Filter healthcare providers by **All Facilities**, **Hospitals**, **Clinics**, or **Pharmacies**.
- **Interactive Client-Side Search & Sorting:** Filter loaded results in real time by facility name, street, or district, and sort by **Nearest Distance (`km`)** or alphabetically (**A–Z** / **Z–A**) with live category counts.
- **National Public Health Context:** Displays Rwandan public health metrics (Malaria incidence, Life expectancy at birth, and Measles immunization coverage) from the World Bank Open Data API.
- **Load Balancer Verification:** Exposes the active backend server (`Web01` / `Web02`) via the custom `X-Served-By` HTTP response header and UI badge.
- **Graceful Error Handling:** Provides clear user feedback for empty inputs, locations not found in Rwanda (`404`), API rate limits (`429`), gateway errors (`502`), and upstream timeouts (`504`).

---

## External APIs & Credits
1. **[Geoapify Places & Geocoding API](https://geoapify.com)**
   - **Forward Geocoding (`/v1/geocode/search`):** Resolves custom Rwandan towns/districts into coordinates restricted to `countrycode:rw`.
   - **Places API (`/v2/places`):** Queries nearby `healthcare.hospital`, `healthcare.clinic_or_praxis`, and `healthcare.pharmacy` facilities within a 12 km radius.
2. **[World Bank Open Data API](https://worldbank.org)**
   - **Indicators Endpoint (`/v2/country/RWA/indicator/{code}`):** Retrieves public health statistics for Rwanda (`SH.MLR.INCD.P3`, `SP.DYN.LE00.IN`, and `SH.IMM.MEAS`).
3. **Libraries & Infrastructure:** Python 3, Flask, Requests, Python-Dotenv, Gunicorn, Nginx, and HAProxy.

---

## Local Setup & Execution
1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd Web_infrustructure
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   Copy `env.example` to `.env` and add your Geoapify API key:
   ```env
   GEOAPIFY_API_KEY=72ff48238ae14c829e20fa4408fd8397
   SERVER_NAME=Local-Server
   ```
5. **Run the application locally:**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

---

## Deployment & Load Balancer Configuration

### 1. Application Servers (`7236-web-01` & `7236-web-02`)
- **Web01 IP:** `18.171.241.16` | **Web02 IP:** `18.171.176.7`
- Deployed the Flask application to `/var/www/healthcare-locator` with server-specific `.env` files (`SERVER_NAME=Web01` on Web01 and `SERVER_NAME=Web02` on Web02).
- Configured a Systemd unit (`/etc/systemd/system/healthcare.service`) running **Gunicorn** with 3 workers bound to `127.0.0.1:8000`.
- Configured **Nginx** (`/etc/nginx/sites-available/healthcare`) listening on port `80` as a reverse proxy forwarding requests to `http://127.0.0.1:8000`.

### 2. Load Balancer (`7236-lb-01`: `35.179.97.207`)
- Configured **HAProxy** (`/etc/haproxy/haproxy.cfg`) listening on `*:80` using `balance roundrobin` across backend servers `18.171.241.16:80` (`web01`) and `18.171.176.7:80` (`web02`) with active health checks (`check`).

---

## Challenges & Solutions
- **Dynamic Rwandan Town Lookup:** Added a fallback to the Geoapify Forward Geocoding API restricted to `countrycode:rw` so users can search smaller Rwandan towns beyond preset coordinates.
- **Cross-Environment Dependency Versions:** Resolved package version mismatches between Windows development (`blinker==1.9.0`) and Ubuntu server environments by installing compatible unpinned versions inside each server's virtual environment.
- **Load Balancer Traffic Verification:** Injected an `X-Served-By` HTTP response header via Flask's `@app.after_request` hook alongside a UI badge driven by `.env`, allowing verification of round-robin routing via `curl` and browser refreshes.

## Development Tracking & CodeVibe Disclosure
- **Cumulative Authorship & Ownership:** Overall AI-assisted authorship across the project is **19.8%** (within the 20% requirement) with a **100/100** code ownership score, and all files have been manually reviewed and verified.
- **Daily Trend Spike:** A single-day spike appears on Wednesday because several files created or modified earlier (including `style.css`) remained unsaved overnight and were batch-saved the following day alongside restoring the workspace directory.
- **Workspace Sync & Idle Window Logs:** During early development, the workspace resided in a OneDrive-synced directory before being migrated to `C:\Projects\Web_infrastructure`. Background OneDrive synchronization, directory migration, and SSH/server deployment sessions outside VS Code generated automated external-edit and idle-window entries in the activity log. The signed verification report (`ebba69c1ab72`) is stored in `codevibe/`.
