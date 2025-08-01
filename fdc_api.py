import os
import requests
import time
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json

class FDCApi:
    """USDA FoodData Central API integration for nutrient enrichment"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize FDC API client"""
        self.api_key = api_key or os.environ.get("FDC_API_KEY")
        if not self.api_key:
            raise ValueError("FDC API key required. Set FDC_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Nutrigenomic-Day-Planner/1.0'
        })
    
    def search_foods(self, query: str, page_size: int = 5, data_types: Tuple[str, ...] = ("Foundation", "SR Legacy")) -> Dict:
        """Search for foods in FDC database"""
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "dataType": ",".join(data_types)
        }
        
        try:
            response = self.session.get(f"{self.base_url}/foods/search", params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"FDC search error for query '{query}': {e}")
            return {"foods": []}
    
    def get_food_details(self, fdc_id: int) -> Optional[Dict]:
        """Get detailed nutrient information for a specific food"""
        params = {"api_key": self.api_key}
        
        try:
            response = self.session.get(f"{self.base_url}/food/{fdc_id}", params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"FDC food details error for fdc_id {fdc_id}: {e}")
            return None
    
    def extract_nutrients(self, food_json: Dict, wanted_names: set) -> Dict[str, Tuple[float, str]]:
        """Extract specific nutrients from FDC food data"""
        nutrients = {}
        
        for nutrient in food_json.get("foodNutrients", []):
            name = (nutrient.get("nutrientName") or "").strip().lower()
            if name in wanted_names:
                value = nutrient.get("value")
                unit = nutrient.get("unitName", "")
                if value is not None:
                    nutrients[name] = (float(value), unit)
        
        return nutrients
    
    def find_best_match(self, food_description: str, category: str = "") -> Optional[int]:
        """Find the best FDC match for a food description"""
        query = f"{food_description} {category}".strip()
        search_results = self.search_foods(query, page_size=3)
        
        foods = search_results.get("foods", [])
        if not foods:
            return None
        
        # Return the first (highest scoring) match
        return foods[0].get("fdcId")
    
    def enrich_food_data(self, food_df: pd.DataFrame, cache_file: str = "fdc_cache.json") -> pd.DataFrame:
        """Enrich food dataframe with FDC nutrients"""
        
        # Load existing cache
        cache = self._load_cache(cache_file)
        
        enriched_rows = []
        total_foods = len(food_df)
        
        for idx, row in food_df.iterrows():
            print(f"Processing food {idx + 1}/{total_foods}: {row['Description']}")
            
            # Check cache first
            cache_key = f"{row['Description']}_{row.get('Category', '')}"
            if cache_key in cache:
                fdc_id = cache[cache_key]
                print(f"  Using cached FDC ID: {fdc_id}")
            else:
                # Find best match
                fdc_id = self.find_best_match(row['Description'], row.get('Category', ''))
                if fdc_id:
                    cache[cache_key] = fdc_id
                    print(f"  Found new FDC ID: {fdc_id}")
                else:
                    print(f"  No FDC match found")
            
            # Create enriched row
            enriched_row = row.copy()
            enriched_row['fdcId'] = fdc_id
            
            # Get nutrient details if we have an FDC ID
            if fdc_id:
                details = self.get_food_details(fdc_id)
                if details:
                    wanted_nutrients = {"folate, dfe", "20:5 n-3 (epa)", "22:6 n-3 (dha)"}
                    nutrients = self.extract_nutrients(details, wanted_nutrients)
                    
                    # Add nutrient columns
                    enriched_row['Folate_DFE_ug'] = nutrients.get("folate, dfe", (None, None))[0]
                    enriched_row['EPA_g'] = nutrients.get("20:5 n-3 (epa)", (None, None))[0]
                    enriched_row['DHA_g'] = nutrients.get("22:6 n-3 (dha)", (None, None))[0]
                    enriched_row['FDC_Source'] = details.get('dataType', 'Unknown')
                else:
                    enriched_row['Folate_DFE_ug'] = None
                    enriched_row['EPA_g'] = None
                    enriched_row['DHA_g'] = None
                    enriched_row['FDC_Source'] = None
            else:
                enriched_row['Folate_DFE_ug'] = None
                enriched_row['EPA_g'] = None
                enriched_row['DHA_g'] = None
                enriched_row['FDC_Source'] = None
            
            enriched_rows.append(enriched_row)
            
            # Be nice to the API
            time.sleep(0.1)
            
            # Save cache periodically
            if (idx + 1) % 100 == 0:
                self._save_cache(cache, cache_file)
        
        # Save final cache
        self._save_cache(cache, cache_file)
        
        return pd.DataFrame(enriched_rows)
    
    def _load_cache(self, cache_file: str) -> Dict:
        """Load FDC ID cache from file"""
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_cache(self, cache: Dict, cache_file: str):
        """Save FDC ID cache to file"""
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

def test_fdc_api():
    """Test the FDC API functionality"""
    try:
        api = FDCApi()
        
        # Test search
        print("Testing FDC search...")
        results = api.search_foods("salmon", page_size=3)
        print(f"Found {len(results.get('foods', []))} salmon foods")
        
        # Test food details
        if results.get('foods'):
            fdc_id = results['foods'][0]['fdcId']
            print(f"Getting details for FDC ID: {fdc_id}")
            details = api.get_food_details(fdc_id)
            if details:
                wanted = {"folate, dfe", "20:5 n-3 (epa)", "22:6 n-3 (dha)"}
                nutrients = api.extract_nutrients(details, wanted)
                print(f"Extracted nutrients: {nutrients}")
        
        print("FDC API test completed successfully!")
        
    except Exception as e:
        print(f"FDC API test failed: {e}")
        print("Make sure FDC_API_KEY environment variable is set")

if __name__ == "__main__":
    test_fdc_api() 