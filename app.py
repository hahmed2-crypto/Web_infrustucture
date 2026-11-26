# In this file, I am writing most of the backend functions, that connects
# the web dashboard to the Geoapify places/Geocoding APIs, and world bank 
#open Data API to locate the healt faciliaties across Rwanda.


import os
import requests 
from flask import Flask, render_template, request, jsonify 
from dotenv import load_dotenv

load_dotenv() 

app= Flask(__name__)

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
SERVER_NAME= os.getenv("SERVER_NAME", "Local-Server")

Rwandan_cities={
    "kigali": {"lat": -1.9441, "lon": 30.0619, "label": "Kigali City"},
    "kimironko": {"lat": -1.9367, "lon": 30.1256, "label": "Kimironko, Kigali"},
    "nyarugenge": {"lat": -1.9536, "lon": 30.0588, "label": "Nyarugenge, Kigali"},
    "bumbogo": {"lat": -1.9114, "lon": 30.1456, "label": "Bumbogo(ALU Area)"},
    "huye": {"lat": -2.5967, "lon": 29.7394, "label": "Huye(Butare)"},
    "musanze": {"lat": -1.4998, "lon": 29.6349, "label": "Musanze"},
    "rubavu": {"lat": -1.6763, "lon": 29.2608, "label": "Rubavu(Gisenyi)"}
}

Category_map={
    "all": "healthcare.hospital,healthcare.clinic_or_praxis,healthcare.pharmacy",
    "hospital": "healthcare.hospital",
    "clinic": "healthcare.clinic_or_praxis",
    "pharmacy": "healthcare.pharmacy"
}

@app.after_request
def add_server_header(response):
    response.headers["X-Served-By"]= SERVER_NAME
    return response 

@app.route("/")
def index():
    return render_template("index.html", server_name=SERVER_NAME, cities=Rwandan_cities)  

@app.route("/api/facilities", methods=["GET"])
def get_facilites():
    if not GEOAPIFY_API_KEY:
        return jsonify({"error": "Server configuration error: Missing API Key"}), 500

    city_key= request.args.get("city", "kigali").strip().lower()
    facility_type= request.args.get("type", "all").strip().lower()

    if facility_type not in Category_map:
        return jsonify({"error": "Invalid facility type selected."}), 400

    #i am gonna write a code gets the city if it is alrady saved in local list so that the app can grab its cordinates.
    if city_key in Rwandan_cities:
        lat = Rwandan_cities[city_key]["lat"]
        lon= Rwandan_cities[city_key]["lon"]
        resolved_location= Rwandan_cities[city_key]["label"]

    else:
        try:
            geo_url= "https://api.geoapify.com/v1/geocode/search"
            geo_params={
                "text": f"{city_key}, Rwanda",
                "filter": "countrycode:rw",
                "limit": 1,
                "apiKey": GEOAPIFY_API_KEY
            }

            geo_res= requests.get(geo_url, params=geo_params, timeout=8)
            geo_res.raise_for_status()
            geo_data= geo_res.json()

            if not geo_data.get("features"):
                return jsonify({"error": f"No location found in Rwanda matching '{city_key}'."}), 404

            coords=geo_data["features"][0]["geometry"]["coordinates"]
            lon, lat= coords[0], coords[1]
            resolved_location= geo_data["features"][0]["properties"].get("formatted", city_key.title())
        except requests.exceptions.Timeout:
            return jsonify({"error": "Geocoding service timed out. Please try again."}), 504
        except requests.exceptions.RequestException:
            return jsonify({"error": "Unable to reach location service right now."}), 502

    # I will try to fetch nearby healthcare facilities via Geoapify places API
    try:
        places_url= "https://api.geoapify.com/v2/places"
        place_params={
            "categories": Category_map[facility_type],
            "filter": f"circle:{lon},{lat},12000",
            "bias": f"proximity:{lon},{lat}",
            "limit": 30,
            "apiKey": GEOAPIFY_API_KEY
        }
        places_res= requests.get(places_url, params=place_params, timeout=8)
        places_res.raise_for_status()
        places_data= places_res.json()

        facilities= []
        for item in places_data.get("features", []):
            props= item.get("properties", {})
            cats= props.get("categories", [])

            if "healthcare.hospital" in cats:
                clean_type= "Hospital"
            elif "healthcare.pharmacy" in cats:
                clean_type= "Pharmacy"
            else:
                clean_type= "Clinic"

            facilities.append({
                "name": props.get("name") or f"Unnamed {clean_type}",
                "type": clean_type,
                "address": props.get("formatted", "Address unavailable"),
                "district": props.get("suburb") or props.get("city") or "Rwanda",
                "distance_km": round(props.get("distance", 0)/1000, 2),
                "lat": props.get("lat"),
                "lon": props.get("lon")
            })

        return jsonify({
            "server": SERVER_NAME,
            "location": resolved_location,
            "count": len(facilities),
            "facilities": facilities 
        })
    except requests.exceptions.Timeout:
        return jsonify({"error": "Healthcare directory API timed out. Please retry."}), 504
    except requests.exceptions.HTTPError as err:
        if err.response is not None and err.response.status_code == 429: 
            return jsonify({"error": "API rate limit reached. Wait a moment and try agian."}), 429 
        return jsonify({"error": "External healthcare API returned an error."}), 502
    except requests.exceptions.RequestException:
        return jsonify({"error": "Network error while contacting healthcare API."}), 502

@app.route("/api/health-stats", methods=["GET"])
def get_health_stats(): 
    #fetching Rwandan public health indicators from World Bank Open Data APA
    indicators={
        "SH.MLR.INCD.P3": "Malaria Incidence(per 1,000 at risk)",
        "SP.DYN.LE00.IN": "Life Expectancy at Birth (years)",
        "SH.IMM.MEAS": "Measles Immunization (%of children 12-23 mos)"
    }

    results=[]

    try:
        for code, label in indicators.items():
            url= f"https://api.worldbank.org/v2/country/RWA/indicator{code}?format=json&per_page=5" 
            res= requests.get(url, timeout=8)
            res.raise_for_status()
            payload= res.json()

            if isinstance(payload, list) and len(payload)>1:
                valid_entry= next((entry for entry in payload[1] if entry.get("value") is not None), None)
                if valid_entry:
                    results.append({
                        "indicator": label,
                        "year": valid_entry.get("date"),
                        "value": round(float(valid_entry.get("value")), 1)
                    })
        return jsonify({"server": SERVER_NAME, "stats": results})
    except requests.exceptions.RequestException:
        return jsonify({"error": "Unable to load World Bank health statistics."}), 502

#I want use this function to monitor my endpoints.
@app.route("/api/health")
def health_check():
    #it should return the health metadata for load balancer monitoring
    return jsonify({
        "status":"healthy",
        "server": os.getenv("SERVER_NAME","Local-Server"),
        "preset_locations":len(Rwandan_cities)
    })

if __name__== "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)