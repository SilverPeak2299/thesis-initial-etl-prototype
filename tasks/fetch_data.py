import requests
import json
import os

def fetch_data(file_path: str) -> None:
    headers = {"User-Agent": "daniel.dickerson@students.mq.edu.au"}
    

    companies = {
    "AAPL": "0000320193",  # Apple
    "MSFT": "0000789019",  # Microsoft
    "AMZN": "0001018724",  # Amazon
    "GOOG": "0001652044",  # Alphabet
    "TSLA": "0001318605",  # Tesla
    }
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    for company in companies:

        data = requests.get(
            url = f"https://data.sec.gov/submissions/CIK{companies[company]}.json",
            headers = headers
        )

        print(data.json()["filings"]["recent"].keys())

        full_file_path = file_path + f"_{company}.json"

        with open(full_file_path, 'w') as f:
            json.dump(data.json(), f)

if __name__ == "__main__":
    fetch_data("data/")