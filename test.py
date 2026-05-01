import requests


def main():
    barcode = input("Please enter the GoUPC code and press Enter, or press Enter to quit: \n").strip()
    if not barcode:
        print("Exiting input mode.")
        return

    API_KEY = "your_api_key_here"

    response = requests.get(f"https://go-upc.com/api/v1/code/{barcode}?key={API_KEY}")  # Placeholder response

    print(f"Response from GoUPC API: {response.json()}")  # Placeholder for actual response handling

if __name__ == "__main__":
    main()