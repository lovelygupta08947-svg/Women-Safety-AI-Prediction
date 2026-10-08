# System Architecture

The application follows a layered web architecture:

1. **Presentation layer** — HTML/CSS/JavaScript and Flask templates.
2. **Application layer** — Flask routes and REST-style endpoints.
3. **ML layer** — feature preparation, Random Forest prediction and safety scoring.
4. **Geospatial layer** — OpenStreetMap/Nominatim/Leaflet for location and map features.
5. **Data layer** — CSV training dataset, model artifacts and SQLite runtime storage.
6. **Safety-assistance layer** — AI assistant, emergency guidance and nearby support lookup.

The GitHub README contains a Mermaid diagram showing the major flow.
