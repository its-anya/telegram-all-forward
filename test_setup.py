import os
from settings import API_ID, API_HASH, STRING_SESSION, forwards

print("Environment variables check:")
print(f"API_ID: {'SET' if API_ID else 'NOT SET'}")
print(f"API_HASH: {'SET' if API_HASH else 'NOT SET'}")
print(f"STRING_SESSION: {'SET' if STRING_SESSION else 'NOT SET'}")

print("\nConfig.ini check:")
print(f"Forwarding sections found: {len(forwards)}")
for section in forwards:
    print(f"  - {section}")

print("\nSetup verification complete.")
print("To use this tool:")
print("1. Edit the .env file with your actual api_id and api_hash")
print("2. Edit config.ini with your actual chat identifiers")
print("3. Run: python forwarder.py")