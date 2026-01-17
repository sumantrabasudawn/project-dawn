# Project DAWN v0.1

Project DAWN ingests event data from CSV files, normalizes it into a canonical schema, and surfaces insights in a Streamlit dashboard.

## Run in Replit

1. Add the dependencies in `requirements.txt` (already included in this repo).
2. In the Replit Shell, install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the Streamlit app:
   ```bash
   streamlit run app/streamlit_app.py
   ```
4. Open the web preview and interact with the dashboard.

## Use the CSV uploader

1. Prepare a CSV with columns like `company`, `published_at`, `publisher`, `title`, `url`, `text`, `theme`, `sentiment`, `impact_score`, and `is_trigger_event`.
2. Upload the CSV in the Streamlit sidebar, or place files in `data/raw/` and select them from the dropdown.
3. Click **Run Pipeline** to normalize, deduplicate, and write cleaned output to `data/clean/`.
4. Use the filters and charts to explore the events, then export the filtered CSV.
