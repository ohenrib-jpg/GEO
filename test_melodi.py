# test_melodi.py
import requests

# Test des datasets
datasets = [
    "DS-PIB-TRIM-NATIONAL",
    "DS-TAUX-CHOMAGE-TRIM-NATIONAL", 
    "DS-INEGALITES-REVENU-ANNUAL-NATIONAL"
]

for dataset in datasets:
    url = f"https://api.insee.fr/melodi/data/{dataset}?GEO=FE"
    try:
        response = requests.get(url, verify=False, timeout=10)
        print(f"📊 {dataset}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   📈 Observations: {len(data.get('observations', []))}")
            if data.get('observations'):
                obs = data['observations'][0]
                print(f"   🕐 Dernière période: {obs.get('dimensions', {}).get('TIME_PERIOD', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    print()
