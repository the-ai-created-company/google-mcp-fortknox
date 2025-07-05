import urllib.request
import json
import os
import time

# Google Discovery API endpoint
DISCOVERY_URL = "https://www.googleapis.com/discovery/v1/apis"

def download_all_discovery_docs():
    """Download discovery documents for all Google Cloud APIs"""
    
    print("Fetching list of all Google APIs...")
    
    try:
        # Get the list of all APIs
        with urllib.request.urlopen(DISCOVERY_URL) as response:
            api_list = json.loads(response.read())
        
        print(f"Found {len(api_list['items'])} APIs")
        
        # Filter for Google Cloud APIs (excluding YouTube, etc.)
        cloud_apis = [
            api for api in api_list['items'] 
            if any(keyword in api['name'].lower() for keyword in [
                'cloud', 'compute', 'storage', 'sql', 'spanner', 'bigtable', 
                'datastore', 'firestore', 'pubsub', 'logging', 'monitoring',
                'container', 'kubernetes', 'run', 'functions', 'appengine',
                'dataflow', 'dataproc', 'bigquery', 'vision', 'translate',
                'speech', 'language', 'video', 'dialogflow', 'automl',
                'vertex', 'aiplatform', 'notebooks', 'workstations'
            ])
        ]
        
        print(f"Found {len(cloud_apis)} Google Cloud APIs")
        
        # Create discovery-docs directory if it doesn't exist
        discovery_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'discovery-docs')
        os.makedirs(discovery_dir, exist_ok=True)
        
        downloaded = 0
        failed = 0
        
        for api in cloud_apis:
            api_name = api['name']
            api_version = api['version']
            discovery_url = api['discoveryRestUrl']
            
            filename = f"{api_name}_{api_version}_discovery.json"
            filepath = os.path.join(discovery_dir, filename)
            
            print(f"\nDownloading {api_name} {api_version}...")
            print(f"  URL: {discovery_url}")
            
            try:
                with urllib.request.urlopen(discovery_url) as response:
                    data = response.read()
                    
                with open(filepath, 'wb') as f:
                    f.write(data)
                    
                print(f"  [OK] Saved to {filename} ({len(data):,} bytes)")
                downloaded += 1
                
                # Be nice to Google's servers
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  [FAIL] Failed: {e}")
                failed += 1
        
        print(f"\n{'='*60}")
        print(f"Download complete!")
        print(f"  Successfully downloaded: {downloaded}")
        print(f"  Failed: {failed}")
        print(f"  Total Cloud APIs: {len(cloud_apis)}")
        print(f"{'='*60}")
        
        # Create a master index
        index = {}
        for file in os.listdir(discovery_dir):
            if file.endswith('_discovery.json'):
                filepath = os.path.join(discovery_dir, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    try:
                        doc = json.load(f)
                        api_name = doc.get('name', file.replace('_discovery.json', ''))
                        index[api_name] = {
                            'file': file,
                            'version': doc.get('version', ''),
                            'title': doc.get('title', ''),
                            'description': doc.get('description', ''),
                            'baseUrl': doc.get('baseUrl', '')
                        }
                    except:
                        pass
        
        # Save the index
        index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_index.json')
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
        
        print(f"\nCreated API index with {len(index)} APIs at {index_path}")
        
    except Exception as e:
        print(f"Error fetching API list: {e}")

if __name__ == "__main__":
    download_all_discovery_docs()
