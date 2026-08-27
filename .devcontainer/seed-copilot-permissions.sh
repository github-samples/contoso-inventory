#!/usr/bin/env bash
# Pre-approve the local tools this course needs, so learners run plain `copilot`
# in the Codespace without approving every call — and WITHOUT YOLO.
#
# Runs from the devcontainer postCreateCommand, where $PWD is the workspace
# folder (/workspaces/<repo>), so the location key is resolved at build time and
# works no matter what the learner named their repo.
#
# Deliberately withheld (so they still prompt): git push, gh, curl/wget, and all
# URLs — i.e. anything that reaches the network or spends the learner's GitHub
# credentials. That is the line between "streamlined" and "YOLO".
set -euo pipefail

CONFIG_DIR="${HOME}/.copilot"
CONFIG_FILE="${CONFIG_DIR}/permissions-config.json"
LOCATION="${PWD}"

mkdir -p "${CONFIG_DIR}"

LOCATION="${LOCATION}" CONFIG_FILE="${CONFIG_FILE}" python3 - <<'PY'
import json, os

path = os.environ["CONFIG_FILE"]
location = os.environ["LOCATION"]

try:
    with open(path) as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    config = {}

approvals = [
    {"kind": "write"},
    {"kind": "commands", "commandIdentifiers": [
        "git add", "git commit", "git switch", "git checkout",
        "git status", "git diff", "git branch", "git restore",
        "npm install", "npm run", "npm test", "npx",
        "mvn", "./mvnw", "dotnet", "python3", "pip",
        "mkdir", "chmod", "cat", "jq",
    ]},
]

config.setdefault("locations", {})
config["locations"][location] = {"tool_approvals": approvals}

with open(path, "w") as f:
    json.dump(config, f, indent=2)
    f.write("\n")

print(f"Seeded Copilot tool approvals for {location}")
PY
