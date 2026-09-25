---
# Plain mockup: a coding agent in the Pronto web repo (the made-up food-delivery app), then one short exchange.
cols: 110
fit: rows
app: agent
version: 1.4.0
tagline: Coding agent || in the pronto-web repo
cwd: ~/src/pronto-web
branch: main
model: default model
status_right: 2 open PRs
---
welcome:
tip: /plan | Draft a plan before changing any files.
user: add a "Reorder your usual" button to the home screen >> 10:42
assistant: I'll look at the home page and the orders API first.
tool: MD | Read | src/pages/home.tsx 212 lines read >> 1s
tool: / | Search | "lastOrder" in src 4 files found
tool: $ | Shell | npm test -- home 18 passed >> 6s
success: Button added | reorders the usual in one tap
