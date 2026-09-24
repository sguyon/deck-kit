---
# Plain mockup: the start screen of the acme CLI (the deck's made-up example app), then one short exchange.
cols: 110
fit: rows
app: acme
version: 2.3.0
tagline: The Acme Deploy CLI || for the acme-app repo
cwd: ~/src/acme-app
branch: main
model: default model
status_right: 3 deploys today
---
welcome:
tip: /plan | Draft a plan before changing any files.
user: add a --dry-run flag to the deploy command >> 10:42
assistant: I'll read the deploy command and its tests first.
tool: MD | Read | src/cli/deploy.ts 148 lines read >> 1s
tool: / | Search | "runDeploy" in src 3 files found
tool: $ | Shell | npm test -- deploy 12 passed >> 6s
success: Flag added | deploy --dry-run prints the plan and exits
