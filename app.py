from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import joblib, os, hashlib, json, sqlite3, datetime
from urllib.parse import quote
from urllib.request import Request, urlopen

app = Flask(__name__)
app.secret_key = "women-safe-ai-demo-secret"
MODEL_PATH="model/safety_model.pkl"
ENCODER_PATH="model/label_encoder.pkl"
DATA_PATH="dataset/crime_data.csv"
DB_PATH="womensafe.db"

def init_db():
    con=sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS safety_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT NOT NULL,
        description TEXT NOT NULL, city TEXT, area TEXT, created_at TEXT NOT NULL)""")
    con.commit(); con.close()

init_db()

if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
    raise FileNotFoundError("Run python train_model.py first.")
model=joblib.load(MODEL_PATH)
encoder=joblib.load(ENCODER_PATH)
data=pd.read_csv(DATA_PATH)
FEATURES=["crime_frequency","night_crime_rate","harassment_cases","assault_cases","police_proximity"]

SERVICES=[
 {"name":"Emergency Response","type":"Emergency","lat":26.8467,"lng":80.9462,"phone":"112"},
 {"name":"Women Helpline","type":"Women Help","lat":26.8500,"lng":80.9490,"phone":"181"},
 {"name":"Demo Police Support Point","type":"Police","lat":26.8310,"lng":80.9200,"phone":"112"},
 {"name":"Demo Hospital Point","type":"Hospital","lat":26.8520,"lng":81.0000,"phone":"112"}
]

# This is only a convenience list for the city dropdown. Any Indian city can also
# be searched through the live India geocoder below, so the app is not limited to
# this list.
INDIAN_CITIES = sorted(set([
"Agra","Ahmedabad","Ajmer","Aligarh","Allahabad","Amritsar","Asansol","Aurangabad",
"Bengaluru","Bareilly","Belagavi","Bhopal","Bhubaneswar","Bikaner","Bilaspur","Bokaro",
"Chandigarh","Chennai","Coimbatore","Cuttack","Dehradun","Delhi","Deoria","Dhanbad",
"Dharwad","Durgapur","Faridabad","Firozabad","Gandhinagar","Ghaziabad","Gorakhpur",
"Greater Noida","Gurugram","Guwahati","Gwalior","Haridwar","Hisar","Hubballi","Hyderabad",
"Imphal","Indore","Jabalpur","Jaipur","Jalandhar","Jammu","Jamshedpur","Jhansi",
"Jodhpur","Kanpur","Kochi","Kolkata","Kota","Kozhikode","Latur","Lucknow","Ludhiana",
"Madurai","Mangalore","Meerut","Moradabad","Mumbai","Mysuru","Nagpur","Nashik","Navi Mumbai",
"New Delhi","Noida","Patna","Prayagraj","Pune","Raipur","Rajkot","Ranchi","Rourkela",
"Salem","Saharanpur","Sangli","Shillong","Shimla","Siliguri","Srinagar","Surat",
"Thane","Thiruvananthapuram","Tiruchirappalli","Udaipur","Ujjain","Vadodara","Varanasi",
"Vasai-Virar","Vellore","Vijayawada","Visakhapatnam","Warangal"
]))


STATE_CITIES = {
"Andhra Pradesh":["Visakhapatnam","Vijayawada","Guntur","Tirupati","Nellore","Kurnool","Rajahmundry","Kakinada"],
"Arunachal Pradesh":["Itanagar","Naharlagun","Pasighat","Tawang"],
"Assam":["Guwahati","Dibrugarh","Silchar","Jorhat","Tezpur"],
"Bihar":["Patna","Gaya","Muzaffarpur","Bhagalpur","Darbhanga","Purnia"],
"Chhattisgarh":["Raipur","Bhilai","Bilaspur","Korba","Durg","Jagdalpur"],
"Goa":["Panaji","Margao","Vasco da Gama","Mapusa"],
"Gujarat":["Ahmedabad","Surat","Vadodara","Rajkot","Gandhinagar","Bhavnagar","Jamnagar","Junagadh"],
"Haryana":["Gurugram","Faridabad","Panipat","Ambala","Hisar","Rohtak","Karnal","Sonipat"],
"Himachal Pradesh":["Shimla","Dharamshala","Mandi","Solan","Kullu","Manali"],
"Jharkhand":["Ranchi","Jamshedpur","Dhanbad","Bokaro","Deoghar","Hazaribagh"],
"Karnataka":["Bengaluru","Mysuru","Mangaluru","Hubballi","Dharwad","Belagavi","Shivamogga","Udupi"],
"Kerala":["Thiruvananthapuram","Kochi","Kozhikode","Thrissur","Kollam","Kannur","Alappuzha"],
"Madhya Pradesh":["Bhopal","Indore","Jabalpur","Gwalior","Ujjain","Sagar","Rewa","Satna"],
"Maharashtra":["Mumbai","Pune","Nagpur","Nashik","Thane","Navi Mumbai","Aurangabad","Kolhapur","Solapur","Amravati"],
"Manipur":["Imphal","Thoubal","Churachandpur"],
"Meghalaya":["Shillong","Tura","Jowai"],
"Mizoram":["Aizawl","Lunglei","Champhai"],
"Nagaland":["Kohima","Dimapur","Mokokchung"],
"Odisha":["Bhubaneswar","Cuttack","Rourkela","Berhampur","Sambalpur","Puri","Balasore"],
"Punjab":["Amritsar","Ludhiana","Jalandhar","Patiala","Bathinda","Mohali","Pathankot"],
"Rajasthan":["Jaipur","Jodhpur","Udaipur","Kota","Ajmer","Bikaner","Alwar","Bharatpur"],
"Sikkim":["Gangtok","Namchi","Gyalshing"],
"Tamil Nadu":["Chennai","Coimbatore","Madurai","Tiruchirappalli","Salem","Tirunelveli","Vellore","Erode","Thoothukudi"],
"Telangana":["Hyderabad","Warangal","Nizamabad","Karimnagar","Khammam","Ramagundam"],
"Tripura":["Agartala","Udaipur","Dharmanagar"],
"Uttar Pradesh":["Lucknow","Kanpur","Agra","Varanasi","Prayagraj","Gorakhpur","Ghaziabad","Noida","Meerut","Bareilly","Moradabad","Aligarh","Saharanpur","Jhansi","Mathura","Ayodhya","Deoria"],
"Uttarakhand":["Dehradun","Haridwar","Haldwani","Nainital","Rishikesh","Roorkee","Rudrapur"],
"West Bengal":["Kolkata","Siliguri","Durgapur","Asansol","Howrah","Kharagpur","Darjeeling"],
"Andaman and Nicobar Islands":["Port Blair"],
"Chandigarh":["Chandigarh"],
"Dadra and Nagar Haveli and Daman and Diu":["Daman","Diu","Silvassa"],
"Delhi":["New Delhi","Delhi"],
"Jammu and Kashmir":["Srinagar","Jammu","Anantnag","Baramulla","Udhampur"],
"Ladakh":["Leh","Kargil"],
"Lakshadweep":["Kavaratti","Agatti"],
"Puducherry":["Puducherry","Karaikal","Mahe","Yanam"]
}
INDIAN_STATES = list(STATE_CITIES.keys())

OFFICIAL_DATA_SOURCES = {
    "ncrb_2024": "https://data.gov.in/ministrydepartment/National%20Crime%20Records%20Bureau%20%28NCRB%29",
    "cii_2023_women": "https://www.data.gov.in/resource/crime-head-wise-and-stateut-wise-indian-penal-code-ipc-crimes-and-special-and-local-laws",
    "cii_2023_city_women": "https://up.data.gov.in/resource/crime-head-wise-and-city-wise-indian-penal-code-ipc-crimes-and-special-and-local-laws-sll",
}

CITY_TO_STATE = {city: state for state, cities in STATE_CITIES.items() for city in cities}

def predict_row(row):
    return encoder.inverse_transform(model.predict([[row[f] for f in FEATURES]]))[0]

def score(row):
    weighted=(row["crime_frequency"]*2 + row["night_crime_rate"]*2 + row["harassment_cases"]*2 + row["assault_cases"]*3 + row["police_proximity"])
    maxw=(data["crime_frequency"].max()*2 + data["night_crime_rate"].max()*2 + data["harassment_cases"].max()*2 + data["assault_cases"].max()*3 + data["police_proximity"].max())
    return int(round(max(0,min(100,100-(weighted/maxw)*100))))

def records():
    result=[]
    for _,r in data.iterrows():
        risk=predict_row(r)
        result.append({"area":r.area,"city":r.city,"risk":risk,"score":score(r),"lat":float(r.latitude),"lng":float(r.longitude)})
    return result

def suggestions(risk):
    return {
      "Low":["Prefer well-lit routes at night.","Keep emergency contacts accessible.","Share your travel plan when traveling late."],
      "Medium":["Prefer populated and well-lit routes.","Share your travel plan with a trusted person.","Avoid isolated places, especially at night."],
      "High":["Avoid isolated routes whenever possible.","Consider traveling with a trusted person.","Keep emergency contacts ready and use official emergency services in an emergency."]
    }[risk]

def geocode_india(query):
    """Find an Indian city/locality using OpenStreetMap Nominatim.
    Results are location lookup only; they are NOT crime/safety data."""
    q=query.strip()
    if not q: return []
    url="https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&countrycodes=in&addressdetails=1&q="+quote(q)
    req=Request(url,headers={"User-Agent":"WomenSafeAI-Academic-Project/1.0"})
    try:
        with urlopen(req,timeout=8) as response:
            raw=json.loads(response.read().decode("utf-8"))
        return [{"display_name":x.get("display_name",""),"lat":float(x["lat"]),"lng":float(x["lon"]),"type":x.get("type",""),"address":x.get("address",{})} for x in raw]
    except Exception:
        return []

def demo_features(seed_text):
    """Create deterministic academic-demo features for locations without verified crime data.
    These values are synthetic and must never be presented as real crime statistics."""
    h=hashlib.sha256(seed_text.lower().encode()).digest()
    nums=[b for b in h[:5]]
    return {
        "crime_frequency": int(3 + nums[0] % 18),
        "night_crime_rate": int(1 + nums[1] % 12),
        "harassment_cases": int(2 + nums[2] % 10),
        "assault_cases": int(1 + nums[3] % 7),
        "police_proximity": int(1 + nums[4] % 8),
    }

def normalize_location_details(g, fallback_area="", fallback_city="", fallback_state=""):
    a=g.get("address",{}) or {}
    state=a.get("state") or fallback_state or ""
    district=a.get("state_district") or a.get("district") or a.get("county") or ""
    town=a.get("city") or a.get("town") or a.get("municipality") or a.get("city_district") or fallback_city or ""
    village=a.get("village") or a.get("suburb") or a.get("neighbourhood") or a.get("quarter") or ""
    area=a.get("neighbourhood") or a.get("suburb") or a.get("quarter") or fallback_area or ""
    postcode=a.get("postcode") or ""
    county=a.get("county") or ""
    country=a.get("country") or "India"
    return {"state":state,"district":district,"town":town,"village":village,"area":area,"postcode":postcode,"county":county,"country":country,"display_name":g.get("display_name","")}

def nearby_services(lat, lng, radius=5000):
    """Fetch nearby public-safety/medical POIs from OpenStreetMap via Overpass.
    This is location data only, not crime/safety evidence.
    """
    query = f"""
    [out:json][timeout:12];
    (
      nwr[amenity=police](around:{radius},{lat},{lng});
      nwr[amenity=hospital](around:{radius},{lat},{lng});
      nwr[amenity=clinic](around:{radius},{lat},{lng});
      nwr[amenity=fire_station](around:{radius},{lat},{lng});
    );
    out center tags;"""
    req = Request(
        "https://overpass-api.de/api/interpreter",
        data=query.encode("utf-8"),
        headers={"User-Agent":"WomenSafeAI-Academic-Project/1.0", "Content-Type":"application/x-www-form-urlencoded"}
    )
    try:
        with urlopen(req, timeout=15) as response:
            raw=json.loads(response.read().decode("utf-8"))
        items=[]
        for e in raw.get("elements", []):
            tags=e.get("tags", {})
            center=e.get("center", {})
            elat=e.get("lat", center.get("lat")); elng=e.get("lon", center.get("lon"))
            if elat is None or elng is None: continue
            amenity=tags.get("amenity", "")
            typ={"police":"Police Station","hospital":"Hospital","clinic":"Clinic","fire_station":"Fire Station"}.get(amenity, amenity.title())
            name=tags.get("name") or typ
            items.append({"name":name,"type":typ,"lat":float(elat),"lng":float(elng),"phone":tags.get("phone") or tags.get("contact:phone") or ""})
        # Keep the closest few of each category.
        def dist(x):
            return ((x["lat"]-lat)*111)**2 + ((x["lng"]-lng)*111)**2
        out=[]
        for typ in ["Police Station","Hospital","Clinic","Fire Station"]:
            group=sorted([x for x in items if x["type"]==typ], key=dist)[:5]
            out.extend(group)
        return out
    except Exception:
        return []

def predict_location(area, city, lat, lng):
    row=demo_features(f"{area}|{city}|{lat:.5f}|{lng:.5f}")
    risk=predict_row(row)
    # Score against the model's academic training range.
    weighted=(row["crime_frequency"]*2 + row["night_crime_rate"]*2 + row["harassment_cases"]*2 + row["assault_cases"]*3 + row["police_proximity"])
    maxw=(data["crime_frequency"].max()*2 + data["night_crime_rate"].max()*2 + data["harassment_cases"].max()*2 + data["assault_cases"].max()*3 + data["police_proximity"].max())
    safety=int(round(max(0,min(100,100-(weighted/maxw)*100))))
    return {"area":area,"city":city,"risk":risk,"score":safety,"lat":lat,"lng":lng,**row,"demo":True}

@app.route("/")
def home():
    rec=records()
    return render_template("index.html", cities=INDIAN_CITIES, states=INDIAN_STATES, state_cities=STATE_CITIES, city_to_state=CITY_TO_STATE, areas=sorted(data.area.unique()), map_data=rec)

@app.route("/predict",methods=["POST"])
def predict():
    area=request.form.get("area","").strip()
    city=request.form.get("city","").strip()
    match=data[(data.area.str.lower()==area.lower()) & (data.city.str.lower()==city.lower())]
    if not match.empty:
        r=match.iloc[0]; risk=predict_row(r)
        # Location fields must be resolved before they are used.
        # Dataset rows do not contain state/district columns, so derive state
        # from the city mapping and leave district blank when unavailable.
        match_state = request.form.get("state", "").strip() or CITY_TO_STATE.get(r.city, "")
        match_district = request.form.get("district", "").strip()
        return render_template("index.html", cities=INDIAN_CITIES, states=INDIAN_STATES, state_cities=STATE_CITIES, city_to_state=CITY_TO_STATE, areas=sorted(data.area.unique()), map_data=records(), result=True, area=r.area, city=r.city, risk_level=risk, safety_score=score(r), crime_frequency=int(r.crime_frequency), night_crime_rate=int(r.night_crime_rate), harassment_cases=int(r.harassment_cases), assault_cases=int(r.assault_cases), recommendations=suggestions(risk), verified_demo=False, crime_detail=crime_detail_profile(r.area,r.city,match_state,match_district,row=r.to_dict(),demo=True))
    # For any Indian city/locality found by the geocoder, return a clearly labelled academic demo estimate.
    state=request.form.get("state","").strip()
    district=request.form.get("district","").strip()
    town=request.form.get("town","").strip() or city
    village=request.form.get("village","").strip()
    postcode=request.form.get("postcode","").strip()
    query_parts=[x for x in [area,village,town,district,state,"India"] if x]
    geo=geocode_india(", ".join(query_parts))
    if not geo: return redirect(url_for("home"))
    g=geo[0]
    loc=normalize_location_details(g, area, town or city, state)
    display_area=loc["area"] or area or g["display_name"].split(",")[0]
    display_city=loc["town"] or city
    p=predict_location(display_area,display_city,g["lat"],g["lng"])
    loc["district"]=loc["district"] or district
    loc["postcode"]=loc["postcode"] or postcode
    return render_template("index.html", cities=INDIAN_CITIES, states=INDIAN_STATES, state_cities=STATE_CITIES, city_to_state=CITY_TO_STATE, areas=sorted(data.area.unique()), map_data=records(), result=True, area=p["area"], city=p["city"], risk_level=p["risk"], safety_score=p["score"], crime_frequency=p["crime_frequency"], night_crime_rate=p["night_crime_rate"], harassment_cases=p["harassment_cases"], assault_cases=p["assault_cases"], recommendations=suggestions(p["risk"]), verified_demo=True, lat=p["lat"], lng=p["lng"], location_details=loc, crime_detail=crime_detail_profile(p["area"],p["city"],loc.get("state",""),loc.get("district",""),row=p,demo=True))

def crime_detail_profile(area, city, state="", district="", row=None, demo=True):
    """Detailed safety/crime panel.

    The academic model only contains a small set of training indicators.
    Categories that are not separately represented are intentionally marked
    as unavailable rather than inventing locality-level crime counts.
    Official NCRB sources are linked for state/city-level verification.
    """
    if row is None:
        f=demo_features(f"{area}|{city}")
        row=f
    cf=int(row.get("crime_frequency",0))
    nr=int(row.get("night_crime_rate",0))
    har=int(row.get("harassment_cases",0))
    ass=int(row.get("assault_cases",0))
    prox=int(row.get("police_proximity",0))
    def level(v, low, med):
        return "High" if v>=med else ("Medium" if v>=low else "Low")
    categories=[
      {"name":"Rape / sexual violence","icon":"🛑","value":None,"unit":"cases","status":"Not separately available at exact locality level","risk":"Data unavailable","source":"NCRB CII 2024 / 2023 city-state tables"},
      {"name":"Kidnapping & abduction","icon":"🚨","value":None,"unit":"cases","status":"Not separately available at exact locality level","risk":"Data unavailable","source":"NCRB CII 2024 / 2023 tables"},
      {"name":"Harassment / sexual misconduct signal","icon":"⚠️","value":har,"unit":"model indicator","status":"Academic model indicator","risk":level(har,4,8),"source":"Project training dataset"},
      {"name":"Assault / physical violence signal","icon":"🥊","value":ass,"unit":"model indicator","status":"Academic model indicator","risk":level(ass,3,5),"source":"Project training dataset"},
      {"name":"Night-time crime exposure","icon":"🌙","value":nr,"unit":"night-rate indicator","status":"Academic model indicator","risk":level(nr,5,9),"source":"Project training dataset"},
      {"name":"Overall crime-frequency signal","icon":"📊","value":cf,"unit":"model indicator","status":"Academic model indicator","risk":level(cf,8,14),"source":"Project training dataset"},
      {"name":"Police accessibility signal","icon":"🚔","value":prox,"unit":"proximity indicator","status":"Academic model indicator","risk":("Higher response gap" if prox>=6 else "Moderate" if prox>=4 else "Better access"),"source":"Project training dataset"},
      {"name":"Dowry deaths","icon":"💔","value":None,"unit":"cases","status":"Not separately available at exact locality level","risk":"Data unavailable","source":"NCRB CII 2024 / 2023 tables"},
      {"name":"Cruelty by husband/relatives","icon":"🏠","value":None,"unit":"cases","status":"Not separately available at exact locality level","risk":"Data unavailable","source":"NCRB CII 2024 / 2023 tables"},
      {"name":"Theft / robbery","icon":"🔐","value":None,"unit":"cases","status":"Not separately available at exact locality level","risk":"Data unavailable","source":"NCRB CII 2024 / 2023 tables"},
      {"name":"Cybercrime","icon":"💻","value":None,"unit":"cases","status":"Not separately available at exact locality level","risk":"Data unavailable","source":"NCRB CII 2024 / 2023 tables"},
      {"name":"Road / public-space safety","icon":"🚦","value":None,"unit":"cases","status":"No verified locality feed connected","risk":"Data unavailable","source":"Local civic data source required"},
    ]
    source_note=(
      "NCRB's Crime in India 2024 catalog includes crimes against women, rape victims, kidnapping/abduction, violent crime and other crime categories. "
      "However, official statistics are not guaranteed at every neighbourhood/locality. This page therefore never fabricates an area-level rape/crime count; "
      "where exact locality data is unavailable it shows that limitation and keeps the ML indicators clearly labelled as academic/demo signals."
    )
    return {"state":state,"district":district,"city":city,"area":area,"categories":categories,
            "official_year":"2024","sources":OFFICIAL_DATA_SOURCES,"source_note":source_note,
            "demo":demo}

def time_risk_profile(night_rate):
    """Academic-demo time-of-day profile. It uses the model's night_crime_rate
    as one feature; it is not an official hourly crime statistic."""
    nr=float(night_rate or 0)
    # Base weights represent a demo temporal pattern, then are scaled by the area's night rate.
    bands=[
      ("00:00–05:00",0.95,"High"),
      ("05:00–08:00",0.45,"Medium"),
      ("08:00–12:00",0.20,"Low"),
      ("12:00–17:00",0.18,"Low"),
      ("17:00–20:00",0.45,"Medium"),
      ("20:00–23:00",0.75,"High"),
      ("23:00–00:00",0.90,"High")]
    # Higher night_crime_rate raises the nighttime demo risk, but never represents real hourly counts.
    factor=max(0.0,min(1.0,nr/15.0))
    result=[]
    for label,base,_ in bands:
        v=round((base*0.65 + factor*0.35)*100)
        level="High" if v>=70 else ("Medium" if v>=40 else "Low")
        result.append({"time":label,"risk":level,"risk_percent":v})
    peak=max(result,key=lambda x:x["risk_percent"])
    return {"bands":result,"peak_time":peak["time"],"peak_risk":peak["risk"],"peak_percent":peak["risk_percent"],"demo":True}

@app.route("/api/crime-detail")
def api_crime_detail():
    area=request.args.get("area","").strip(); city=request.args.get("city","").strip(); state=request.args.get("state","").strip(); district=request.args.get("district","").strip()
    if not area and not city: return jsonify({"error":"Area or city is required."}),400
    match=data[(data.area.str.lower()==area.lower()) & (data.city.str.lower()==city.lower())]
    row=match.iloc[0].to_dict() if not match.empty else demo_features(f"{area}|{city}")
    return jsonify(crime_detail_profile(area,city,state,district,row=row,demo=match.empty or True))

@app.route("/api/time-risk")
def api_time_risk():
    area=request.args.get("area","").strip(); city=request.args.get("city","").strip()
    nr=request.args.get("night_rate", type=float)
    if nr is None:
        match=data[(data.area.str.lower()==area.lower()) & (data.city.str.lower()==city.lower())]
        if not match.empty: nr=float(match.iloc[0].night_crime_rate)
        else: nr=float(demo_features(f"{area}|{city}")["night_crime_rate"])
    return jsonify(time_risk_profile(nr))

@app.route("/api/assistant", methods=["POST"])
def assistant():
    payload=request.get_json(silent=True) or {}
    message=(payload.get("message") or "").strip()
    text=message.lower()
    risk=(payload.get("risk") or "").strip().title()
    area=payload.get("area") or "your area"
    city=payload.get("city") or "your city"

    if not text:
        return jsonify({"reply":"Hi! I am WomenSafe AI Assistant 🤖. Ask me about your area risk, night travel, emergency help, nearby support, reporting an issue, or safety tips.","quick":["Explain my risk","Night travel tips","Emergency help","Nearby police","Report a safety issue"]})

    emergency_words=["emergency","danger","help me","attack","unsafe now","112","ambulance","police help","आपात","खतरा","मदद","112 नंबर"]
    night_words=["night","late","dark","रात","रात में","अंधेरा"]
    risk_words=["risk","score","safe","safety","danger level","जोखिम","सुरक्षित","सेफ","स्कोर"]
    nearby_words=["police","hospital","fire","nearby","पास","नजदीक","अस्पताल","पुलिस","फायर"]
    report_words=["report","complaint","issue","street light","road","शिकायत","रिपोर्ट","लाइट","सड़क","समस्या"]
    travel_words=["route","travel","journey","go to","traveling","यात्रा","रास्ता","जाना"]
    tips_words=["tips","protect","precaution","safety tips","बचाव","सावधानी","टिप्स"]

    if any(k in text for k in emergency_words):
        reply=("🚨 If you are in immediate danger, call India's emergency number 112 and move toward a populated/safe place. "
               "If possible, share your live location with a trusted person. This project is only an academic assistant and cannot replace police, medical or emergency services.")
    elif any(k in text for k in risk_words):
        if risk:
            reply=(f"📊 For {area}, {city}, the project currently shows **{risk} risk**. "
                   "The displayed score is an academic/demo estimate unless verified official crime data is available. "
                   "Use the map and nearby-support section for additional context.")
        else:
            reply="First search an area using City + Area/Locality. Then I can explain the displayed safety score and risk level."
    elif any(k in text for k in night_words):
        reply=("🌙 For night travel: choose well-lit and populated roads, avoid isolated shortcuts, keep your phone charged, "
               "share your route/arrival time with a trusted contact, keep 112 accessible, and use official transport where possible.")
    elif any(k in text for k in nearby_words):
        reply=("📍 After searching an area, the result page can load nearby police stations, hospitals/clinics and fire stations "
               "from OpenStreetMap. Open the Safety Map for a wider view. Always verify official contact details before relying on them.")
    elif any(k in text for k in report_words):
        reply=("📝 You can use the 'Report a Safety / Civic Issue' form on this page. Choose a category, add the city/area and describe the issue. "
               "The report is saved in the academic admin dashboard for demonstration.")
    elif any(k in text for k in travel_words):
        reply=("🧭 For safer travel, prefer well-lit populated routes, avoid isolated shortcuts, share your expected arrival time, "
               "keep emergency contacts ready, and check the map for nearby support points. This project does not guarantee that any route is safe.")
    elif any(k in text for k in tips_words):
        reply=("🛡️ Quick safety checklist: keep your phone charged, enable location sharing when appropriate, stay in populated areas, "
               "avoid isolated shortcuts, save trusted contacts, and call 112 in an immediate emergency.")
    elif any(k in text for k in ["hello","hi","hey","namaste","नमस्ते","हाय"]):
        reply="Namaste! 👋 I’m WomenSafe AI Assistant. I can explain your area risk, give travel/night-safety tips, find nearby-support guidance, or help you report an issue."
    else:
        reply=("I can help with: 📊 risk explanation, 🌙 night-travel safety, 🚨 emergency guidance, "
               "📍 nearby police/hospital/fire support, 📝 safety-issue reporting, and 🛡️ general safety tips. "
               "Try asking one of these topics.")
    return jsonify({"reply":reply,"quick":["Explain my risk","Night travel tips","Emergency help","Nearby police","Report a safety issue"]})

@app.route("/report-issue", methods=["POST"])
def report_issue():
    category=request.form.get("category", "Other").strip()
    description=request.form.get("description", "").strip()
    city=request.form.get("city", "").strip()
    area=request.form.get("area", "").strip()
    name=request.form.get("name", "Anonymous").strip() or "Anonymous"
    if not description:
        return redirect(url_for("home"))
    con=sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO safety_reports(name,category,description,city,area,created_at) VALUES(?,?,?,?,?,?)",(name,category,description,city,area,datetime.datetime.now().isoformat(timespec="seconds")))
    con.commit(); con.close()
    return redirect(url_for("home", reported="1"))

@app.route("/api/search-location")
def search_location():
    q=request.args.get("q","").strip()
    return jsonify(geocode_india(q))

@app.route("/api/predict-location",methods=["POST"])
def api_predict_location():
    payload=request.get_json(force=True)
    area=payload.get("area","").strip(); city=payload.get("city","").strip()
    lat=float(payload.get("lat")); lng=float(payload.get("lng"))
    if not area or not city: return jsonify({"error":"Area and city are required."}),400
    return jsonify(predict_location(area,city,lat,lng))

@app.route("/api/nearby")
def api_nearby():
    try:
        lat=float(request.args.get("lat")); lng=float(request.args.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"error":"Valid latitude and longitude are required."}),400
    return jsonify({"services":nearby_services(lat,lng)})

@app.route("/map")
def safety_map(): return render_template("map.html",map_data=records(),services=SERVICES)
@app.route("/analytics")
def analytics():
    rec=records(); counts={k:sum(x["risk"]==k for x in rec) for k in ["Low","Medium","High"]}; city_stats={}
    for city in sorted(data.city.unique()):
        rr=[x for x in rec if x["city"]==city]; city_stats[city]={k:sum(x["risk"]==k for x in ["Low","Medium","High"] for x in rr)}
    return render_template("analytics.html",records=rec,counts=counts,city_stats=city_stats)
@app.route("/emergency")
def emergency(): return render_template("emergency.html")
@app.route("/login",methods=["GET","POST"])
def login():
    error=None
    if request.method=="POST":
        if request.form.get("email")=="admin@womensafe.ai" and request.form.get("password")=="admin123": session["admin"]=True; return redirect(url_for("admin"))
        error="Invalid demo credentials."
    return render_template("login.html",error=error)
@app.route("/admin")
def admin():
    if not session.get("admin"): return redirect(url_for("login"))
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row
    reports=[dict(r) for r in con.execute("SELECT * FROM safety_reports ORDER BY id DESC LIMIT 100").fetchall()]
    con.close()
    return render_template("admin.html",records=records(),reports=reports)
@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("home"))
@app.route("/api/map-data")
def api_map_data(): return jsonify(records())
@app.route("/api/services")
def api_services(): return jsonify(SERVICES)

if __name__=="__main__": app.run(debug=True)
