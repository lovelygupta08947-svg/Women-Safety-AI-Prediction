# WomenSafe AI — All India Area Search

A B.Tech academic project demonstrating women-safety area prediction with Flask, Random Forest, Leaflet and OpenStreetMap.

## What is new
- Search **any Indian city** instead of only six fixed cities.
- Search **any area/locality** using OpenStreetMap Nominatim geocoding.
- City and area can be typed directly; common cities/areas are also offered as autocomplete suggestions.
- Existing academic training areas use the project's sample dataset.
- Unknown locations can still demonstrate the ML workflow using **synthetic academic-demo features**. These are clearly labelled and are NOT official crime statistics.
- Map continues to show the sample dataset and can be extended with geocoded locations.

## Run
```powershell
pip install -r requirements.txt
python train_model.py
python app.py
```
Open `http://127.0.0.1:5000` in Chrome.

## Important limitation
There is no single official public database containing real-time crime/safety scores for every Indian locality. This project therefore does **not** fabricate real crime statistics. For a college demonstration, unknown areas use deterministic synthetic features only to demonstrate the Random Forest prediction pipeline. For real deployment, replace those features with verified police/crime/open-government data.

## Location search
The app uses OpenStreetMap Nominatim for location lookup. Internet access is required for searching an arbitrary locality that is not already in the local sample dataset. Nominatim usage should respect its public service policy and rate limits.

## Demo admin
- Email: `admin@womensafe.ai`
- Password: `admin123`

## Safety disclaimer
This is an academic demonstration and must not be treated as a real-world guarantee of safety. In an emergency, use official emergency services and verify local information.


## New Smart Features
- AI Safety Assistant: contextual safety guidance through a lightweight server-side assistant API.
- Emergency SOS confirmation and official 112 call shortcut.
- Share Safety Plan using the browser Web Share API (clipboard fallback).
- Browser location helper.
- Community Safety/Civic Issue reporting form.
- SQLite persistence for submitted reports.
- Admin dashboard section for reviewing submitted reports.
- Premium responsive UI cards and interactive assistant panel.

### Important
The assistant is an academic/demo safety assistant, not a substitute for emergency services or professional advice. Risk features for geocoded locations without verified crime data are synthetic demo values and are clearly labelled.

## Detailed crime intelligence and current-data policy

The result page now includes a detailed **Crime & Safety Intelligence** panel. It separates:

- **Academic model indicators**: crime-frequency signal, night-time exposure, harassment signal, assault signal, and police-accessibility signal.
- **Government-data categories**: rape/sexual violence, kidnapping & abduction, dowry deaths, cruelty by husband/relatives, theft/robbery, cybercrime, etc.

The project does **not invent locality-level rape or crime counts** when a verified source does not publish them. The UI shows **Not available** for those exact-locality fields and links to official NCRB/Open Government Data sources for state/city-level verification.

Current official reference: the NCRB **Crime in India (CII) - 2024** catalog on data.gov.in, which covers crimes against women, rape victims, kidnapping/abduction, violent crimes, and other crime heads. Official datasets are annual and their geographic granularity varies; exact neighbourhood-level figures are not guaranteed.
