---
# Annotated mockup: the acme CLI (same made-up app as the web mockups) proposing an edit.
# Renders review.png, review-annotated.png and review-zoom.png.
cols: 104
app: acme
version: 2.3.0
tagline: The Acme Deploy CLI
cwd: ~/src/acme-app
branch: fix-totals
mode: plan
prompt: looks good, apply it{muted} (typed, not sent)
---
user: why is the cart total wrong for discounts? >> 14:05
thought: The discount is applied after tax, so tax is charged on the full price.
blank:
diff: src/cart/total.ts
diff-: const total = (subtotal + tax) - discount;
diff+: const total = subtotal - discount + taxOn(subtotal - discount);
blank:
tool: $ | Shell | acme deploy --dry-run 2 files, 1 service >> 41s
annotate:
  frame: thought | Explains before editing | One sentence on the cause
  frame: diff#1 .. diff+#1 | Shows the exact change | A two-line diff, not a summary
  frame: tool | Dry run first | Nothing ships until you confirm
  crop: thought, diff+
  cols: 104
