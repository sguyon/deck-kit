---
# Annotated mockup: a coding agent in the Pronto web repo proposing an edit.
# Renders review.png, review-annotated.png and review-zoom.png.
cols: 104
app: agent
version: 1.4.0
tagline: Coding agent
cwd: ~/src/pronto-web
branch: one-tap-reorder
mode: plan
prompt: looks good, apply it{muted} (typed, not sent)
---
user: why does reorder pick the wrong restaurant sometimes? >> 14:05
thought: It takes the most recent order, not the most frequent one.
blank:
diff: src/orders/usual.ts
diff-: const usual = orders[0];
diff+: const usual = mostFrequent(orders, { last: 10 });
blank:
tool: $ | Shell | npm test -- usual 9 passed >> 4s
annotate:
  frame: thought | Explains before editing | One sentence on the cause
  frame: diff#1 .. diff+#1 | Shows the exact change | A two-line diff, not a summary
  frame: tool | Tests first | Nothing ships until they pass
  crop: thought, diff+
  cols: 104
