import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")

def main():
    barcode = input("Please enter the GoUPC code and press Enter, or press Enter to quit: \n").strip()
    if not barcode:
        print("Exiting input mode.")
        return

    response = requests.get(f"https://go-upc.com/api/v1/code/{barcode}?key={API_KEY}")  # Placeholder response

    print(f"Response from GoUPC API: {response.json()}")  # Placeholder for actual response handling

if __name__ == "__main__":
    main()