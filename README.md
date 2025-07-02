# Google MCP Fort Knox

A robust extractor for Google Cloud API documentation. Converts Google Discovery documents into structured JSON for easy consumption by MCP (Model Context Protocol) tools.

## Why Fort Knox?

Because your API documentation should be as secure and reliable as Fort Knox! This tool ensures you get consistent, well-structured data every time.

## Features

- Fast & Efficient: Extracts hundreds of endpoints in seconds
- Structured Output: Creates 4 organized JSON files per service
- Complete Schemas: Includes full request/response schemas
- Robust Parsing: Handles complex nested API structures
- Cost Effective: No need for expensive AI API calls

## Directory Structure

```
google-mcp-fortknox/
├── discovery-docs/       # Original Google Discovery documents
├── extracted-data/       # Processed API documentation
│   └── storage/         # Storage API endpoints
├── scripts/             # Extraction scripts
├── docs/               # Additional documentation
└── master_index.json   # Index of all processed services
```

## Quick Start

1. Download a discovery document:
```bash
python scripts/download_discovery.py
```

2. Extract the API documentation:
```bash
python scripts/build_storage_docs_final_v2.py
```

## Output Files

Each service generates 4 files:

- **api_endpoints.json**: All endpoints with complete schemas
- **resource_types.json**: What operations each resource supports
- **capabilities.json**: Operations grouped by function
- **parameters_schema.json**: Global parameters

## Extracted Services

- [x] Storage API (81 endpoints)
- [ ] Compute API
- [ ] BigQuery API
- [ ] Cloud Run API
- [ ] And many more...

## Contributing

Feel free to add more Google services! The script is designed to work with any Google Discovery document.

## License

This project is for extracting public API documentation. The extracted data remains subject to Google's API Terms of Service.
