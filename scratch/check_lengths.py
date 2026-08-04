import json

msgs = [
    {"success": False, "message": "Account is not registered. Please register first."},
    {"success": False, "message": "Google verification failed: Invalid Value"},
    {"success": False, "message": "Failed to verify Google token: HTTP Error 400: Bad Request"},
    {"success": False, "message": "Failed to register Google account: UNIQUE constraint failed: users.phone"},
    {"success": False, "message": "Failed to register Google account: UNIQUE constraint failed: users.email"},
]

for msg in msgs:
    serialized = json.dumps(msg)
    print(f"Len: {len(serialized)} -> {serialized}")
