import requests
import pdfplumber
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

PDF_URL = "https://drive.google.com/uc?id=13ROKUMKBYahGXjU5XkvjPYprMrmpAGOR"

def extract_outage_schedule(zone, neighborhood):
    response = requests.get(PDF_URL)
    response.raise_for_status()

    with open("schedule.pdf", "wb") as file:
        file.write(response.content)

    schedule_data = []
    found_date = None
    found_time_range = None

    with pdfplumber.open("schedule.pdf") as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            # Debug: Print each page’s text to verify the structure
            print("Extracted Text:", text)

            # Case-insensitive, fuzzy matching for zone and neighborhood
            pattern = rf"(?i){zone}.*?{neighborhood}.*?\n([\s\S]+?)(?=\n\n|Ministerio|Lunes)"
            matches = re.findall(pattern, text)

            if matches:
                for match in matches:
                    cleaned_text = re.sub(r"\s+", " ", match.strip())
                    schedule_data.append(cleaned_text)

            # Enhanced date pattern
            if not found_date:
                date_match = re.search(
                    r"(Lunes\s*\d{1,2}\s*y\s*martes\s*\d{1,2}\s*de\s*\w+\s*de\s*\d{4})", text, re.IGNORECASE
                )
                found_date = date_match.group() if date_match else None

            if not found_time_range:
                time_range_match = re.search(r"\d{2}:\d{2} - \d{2}:\d{2} / \d{2}:\d{2} - \d{2}:\d{2}", text)
                found_time_range = time_range_match.group() if time_range_match else None

    if schedule_data:
        return {
            "date": found_date or "Date not found",
            "time_range": found_time_range or "Time range not found",
            "schedule": schedule_data
        }

    return None

@app.route('/outage', methods=['GET'])
def get_outage_schedule():
    zone = request.args.get('zone')
    neighborhood = request.args.get('neighborhood')
    schedule = extract_outage_schedule(zone, neighborhood)

    if schedule:
        return jsonify({
            "zone": zone,
            "neighborhood": neighborhood,
            "date": schedule["date"],
            "time_range": schedule["time_range"]
        })
    else:
        return jsonify({"error": "No schedule found for the specified zone and neighborhood."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
