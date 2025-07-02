import json, os, re, sys

BASE_DIR = os.path.join(os.path.dirname(__file__))
STORAGE_DISC = os.path.join(BASE_DIR, "storage_discovery.json")
OUT_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(OUT_DIR, exist_ok=True)

with open(STORAGE_DISC, "r", encoding="utf-8") as f:
    disc = json.load(f)

# ---- api_endpoints.json --------------------------------------------------
endpoints = []
base_url = disc.get("rootUrl", "").rstrip("/") + "/" + disc.get("servicePath", "").lstrip("/")
# traverse "methods" recursively
def walk_methods(obj, resource_name_prefix=""):
    for name, val in obj.get("methods", {}).items():
        body_ref = None
        body_schema = {}
        if "request" in val and "$ref" in val["request"]:
            body_ref = val["request"]["$ref"]
            body_schema = disc.get("schemas", {}).get(body_ref, {})
        endpoints.append({
            "operation_id": val.get("id"),
            "resource": resource_name_prefix.rstrip("."),
            "action": name,
            "http_method": val.get("httpMethod"),
            "path_template": val.get("path"),
            "description": val.get("description"),
            "required_params": [k for k, p in val.get("parameters", {}).items() if p.get("required")],
            "parameters": val.get("parameters", {}),
            "body_schema_ref": body_ref,
            "body_schema": body_schema,
            "scopes_required": val.get("scopes", []),
            "response_type": val.get("response", {}).get("$ref", "")
        })
    for sub_name, sub in obj.get("resources", {}).items():
        walk_methods(sub, f"{resource_name_prefix}{sub_name}.")

walk_methods(disc)

api_endpoints = {
    "service": "storage",
    "base_url": base_url,
    "total_endpoints": len(endpoints),
    "endpoints": endpoints
}
with open(os.path.join(OUT_DIR, "api_endpoints.json"), "w", encoding="utf-8") as f:
    json.dump(api_endpoints, f, indent=2)

# ---- parameters_schema.json ----------------------------------------------
with open(os.path.join(OUT_DIR, "parameters_schema.json"), "w", encoding="utf-8") as f:
    json.dump(disc.get("parameters", {}), f, indent=2)

# ---- resource_types.json & capabilities.json -----------------------------
resource_ops = {}
for ep in endpoints:
    res = ep["resource"].split(".")[-1] or "root"
    resource_ops.setdefault(res, []).append(ep)

resource_types = {}
capabilities = {}
def action_keyword(op_id):
    if not op_id:
        return ""
    return op_id.split(".")[-1]

for res, ops in resource_ops.items():
    actions = [action_keyword(e["operation_id"]) for e in ops]
    resource_types[res] = {
        "description": f"{res} resource",
        "operations_count": len(ops),
        "can_create": "insert" in actions,
        "can_delete": "delete" in actions,
        "can_list": "list" in actions,
        "can_update": any(a in actions for a in ("update","patch","set")),
        "special_operations": sorted(set(actions) - {"insert","delete","list","update","patch","set"})
    }
    # capabilities
    for op in ops:
        action = action_keyword(op["operation_id"])
        cap_group = f"{res}_management"
        capabilities.setdefault(cap_group, {})
        capabilities[cap_group].setdefault(f"{action}_{res}", []).append(op["operation_id"])

with open(os.path.join(OUT_DIR, "resource_types.json"), "w", encoding="utf-8") as f:
    json.dump(resource_types, f, indent=2)

with open(os.path.join(OUT_DIR, "capabilities.json"), "w", encoding="utf-8") as f:
    json.dump(capabilities, f, indent=2)

# ---- master_index.json ----------------------------------------------------
master_index_path = os.path.join(BASE_DIR, "master_index.json")
if os.path.exists(master_index_path):
    with open(master_index_path, "r", encoding="utf-8") as f:
        master = json.load(f)
else:
    master = {}
master["storage"] = {
    "base_url": base_url,
    "discovery_file": "storage_discovery.json",
    "endpoint_count": len(endpoints)
}
with open(master_index_path, "w", encoding="utf-8") as f:
    json.dump(master, f, indent=2)

print("Generated storage API documentation files.")
