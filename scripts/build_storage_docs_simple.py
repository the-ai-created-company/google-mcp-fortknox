import json
import os

def extract_endpoints(discovery_file, output_dir):
    with open(discovery_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    endpoints = []
    
    def process_methods(methods, resource_name):
        for method_name, method_details in methods.items():
            endpoint = {
                'operation_id': method_details.get('id'),
                'resource': resource_name,
                'action': method_name,
                'http_method': method_details.get('httpMethod'),
                'path_template': method_details.get('path'),
                'description': method_details.get('description'),
                'required_params': [p for p, d in method_details.get('parameters', {}).items() if d.get('required')],
                'parameters': method_details.get('parameters', {}),
                'scopes_required': method_details.get('scopes', []),
                'response_type': method_details.get('response', {}).get('$ref')
            }
            
            if 'request' in method_details:
                request_ref = method_details['request'].get('$ref')
                if request_ref and 'schemas' in data:
                    endpoint['body_schema'] = data['schemas'].get(request_ref, {})
            
            endpoints.append(endpoint)

    def find_resources(resources, parent_name=''):
        for name, details in resources.items():
            resource_name = f"{parent_name}.{name}" if parent_name else name
            if 'methods' in details:
                process_methods(details['methods'], resource_name)
            if 'resources' in details:
                find_resources(details['resources'], resource_name)

    if 'resources' in data:
        find_resources(data['resources'])

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Write api_endpoints.json
    with open(os.path.join(output_dir, 'api_endpoints.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'service': data.get('name'),
            'base_url': data.get('baseUrl'),
            'total_endpoints': len(endpoints),
            'endpoints': endpoints
        }, f, indent=2)

    # Write other files (simplified for now)
    with open(os.path.join(output_dir, 'parameters_schema.json'), 'w', encoding='utf-8') as f:
        json.dump(data.get('parameters', {}), f, indent=2)
        
    print(f"Generated {len(endpoints)} endpoints.")

if __name__ == '__main__':
    BASE_DIR = os.path.dirname(__file__)
    STORAGE_DISC = os.path.join(BASE_DIR, "storage_discovery.json")
    OUT_DIR = os.path.join(BASE_DIR, "storage")
    extract_endpoints(STORAGE_DISC, OUT_DIR)
