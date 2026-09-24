---
# Reference spec that uses every role. Not rendered by default:
#   mockups/render.sh mockups/specs/examples/roles.md
cols: 104
rows: 40
app: acme
cwd: ~/src/acme-app
branch: fix-checkout
model: default model
status_right: session 4
tabs: Chat
tab_list: Chat, History, Settings
mode: auto
prompt: fix the flaky test{muted} (typed, not sent)
---
user: why does checkout.spec fail in CI? >> 22:26
skill: skill(test-runner)
assistant: I'll look at the test and the CI logs first.
tool: MD | Read | tests/checkout.spec.ts 212 lines read >> 3s
tool: / | Search | "api/tax" in src 4 files found
tool: $ | Shell | Run checkout spec 20 times 38 lines… >> 41s
detail: for i in $(seq 20); do npm test -- checkout; done
thought: The failure only happens when the tax call is slow, so this looks like a race.
diff: src/cart/Total.tsx
diff-: const total = subtotal + tax;
diff+: const total = subtotal + (await taxReady);
success: Tests pass | 20 of 20 runs green
warning: Auto mode will open a pull request when done
box: Confirm edit
  Allow acme to edit {code}src/cart/Total.tsx{/}?
  {accent}❯ 1. Yes{/}   2. No (Esc)
menu*: /resume | Resume a previous session
menu: /context | Show context window usage
session: *fix-checkout | ⎇ fix-checkout · 2d ago
text: plain {b}bold{/} {accent}accent{/} {muted}muted{/} {ok}ok{/} {warn}warn{/} {err}err{/} {code}code{/} {s}struck{/} >> right
