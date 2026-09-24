---
# Web-app mockup: the Overview page of Acme Deploy, a made-up product used as the example app in the deck.
kind: web
app: Acme Deploy
url: deploy.acme.dev/acme-app
tab: Overview · acme-app
nav: Overview*, Deploys (3), Environments, Settings
user: Alex Kim
---
title: acme-app | main · 3 environments · last deploy 12 min ago
button: Docs
button*: New deploy
stats: Deploys today | 14 | 2 more than yesterday ¦ Success rate | 96% | last 7 days ¦ Median deploy time | 4m 10s | was 20 min last month ¦ Failed | 1 | caught by a dry run
table: Deploy ¦ Branch ¦ Environment ¦ Status
row: #482 ¦ fix-totals ¦ production ¦ {ok}Live
row: #481 ¦ dry-run-flag ¦ staging ¦ {ok}Live
row: #480 ¦ cart-tax ¦ staging ¦ {err}Failed
row: #479 ¦ main ¦ production ¦ {muted}Rolled back
chart: Deploy time this week (min) | Mon 20, Tue 14, Wed 9, Thu 6, Fri 4
toast: #482 is live on production
