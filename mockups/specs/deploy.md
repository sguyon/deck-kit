---
# Web-app mockup: a dry-run plan page of Acme Deploy (the deck's made-up example app), with annotations.
kind: web
app: Acme Deploy
url: deploy.acme.dev/acme-app/deploys/483
tab: Deploy #483 · acme-app
nav: Overview, Deploys* (3), Environments, Settings
user: Alex Kim
---
title: Deploy #483 · dry run | fix-totals → production · planned 30 s ago · nothing has changed yet
button: Cancel
button*: Apply plan
stats: Files changed | 2 ¦ Services restarted | 1 | api ¦ Estimated time | 3m 40s ¦ Risk | Low | all checks passed
table: Check ¦ Result
row: Unit tests ¦ {ok}148 passed
row: Database migrations ¦ {ok}None
row: Rollback ¦ {ok}Ready
row: Owner approval ¦ {warn}Waiting
code: plan.diff
  ~ service api
  -   image: acme/api:2.3.0
  +   image: acme/api:2.3.1
  ~ config cart
  -   tax_after_discount: false
  +   tax_after_discount: true
  = 12 services unchanged
toast: Dry run finished in 41 s
annotate:
  frame: button#2 | Apply when ready | Nothing runs before you confirm
  frame: code | The exact change | The plan as a diff, not a summary
  frame: toast | Fast feedback | A dry run takes under a minute
