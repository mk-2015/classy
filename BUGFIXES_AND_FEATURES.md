# Bug Fixes:
- Fixed provider messaging queue buildup by adding a janitor task that trims up to 50 messages every 10 seconds.

# Patches During Development
- Added task in provider to cut 50 messages every 10 seconds so providers can talk to each other

# Features:
1. Adding authlib integration
2. JWT issuance and decoding support via authlib
3. Provider messaging queue maintenance for plugin communication
