#!/usr/bin/env python3
import requests
import json

# Írd be a felhasználói tokent
user_token = "EAATyHi6i9p8BO8y3K0krZBr6skzvIwHt1r7Gp0iPh387sNYVWHdq27YHYYE5VWBKdjbMBt6397BHo2hwnTOTyO1qyOZC6hxLTbSZB1bKClF8uTMtOchJAfiZATizdJ6Ylvx5J3sUj7ZCKGFj88GDlOtuD1AvRGHPj9Rt8ZASD7bGIoZBMZAZBsiJW2g3eAOEJyO0TtYP7e9WgZDZD"

# 1. Lépés: Lekérjük a felhasználóhoz tartozó oldalak listáját
print("Felhasználóhoz tartozó oldalak lekérése...")
url = "https://graph.facebook.com/v22.0/me/accounts"
params = {
    "access_token": user_token
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    pages_data = response.json()
    
    if "data" not in pages_data or len(pages_data["data"]) == 0:
        print("Nem találhatóak oldalak a felhasználó fiókjához.")
        exit(1)
    
    print(f"{len(pages_data['data'])} oldal található.")
    print("\nRendelkezésre álló oldalak:")
    
    # Kilistázzuk az elérhető oldalakat
    for i, page in enumerate(pages_data["data"]):
        print(f"{i+1}. {page.get('name')} (ID: {page.get('id')})")
    
    # Ha csak egy oldal van, automatikusan kiválasztjuk
    if len(pages_data["data"]) == 1:
        selected_page = pages_data["data"][0]
        print(f"\nAutomatikusan kiválasztva: {selected_page.get('name')}")
    else:
        # Különben bekérjük a felhasználótól, melyik oldalt akarja használni
        while True:
            try:
                choice = int(input("\nAdd meg a használni kívánt oldal számát: "))
                if 1 <= choice <= len(pages_data["data"]):
                    selected_page = pages_data["data"][choice-1]
                    break
                else:
                    print("Érvénytelen szám. Próbáld újra.")
            except ValueError:
                print("Kérlek, egy számot adj meg.")
    
    # Kiírjuk az oldal tokenét
    page_id = selected_page.get("id")
    page_name = selected_page.get("name")
    page_token = selected_page.get("access_token")
    
    print("\n" + "="*50)
    print(f"Oldal név: {page_name}")
    print(f"Oldal ID: {page_id}")
    print(f"Page Access Token: {page_token}")
    print("="*50)
    
    print("\nEzt a tokent és oldal ID-t használd a Facebook Post Importálóhoz.")
    print("Példa a használatra:")
    print(f"python facebook_importer.py -t \"{page_token}\" -p \"{page_id}\" -n 5")
    
except requests.exceptions.RequestException as e:
    print(f"Hiba történt az API kérés során: {e}")
    if hasattr(e, 'response') and e.response:
        try:
            error_data = e.response.json()
            print("API hibaüzenet:", json.dumps(error_data, indent=2))
        except:
            print("Nem sikerült a hibaüzenet értelmezése.")
    exit(1)