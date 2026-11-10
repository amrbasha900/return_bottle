# Test plan for the Bottle Return POS integration

These tests are intentionally a manually run checklist, not a claim of automated CI coverage.

1. Install on a disposable v15 site (not on a production/shared test site without approval).
2. Set up Bottle Return Settings exactly as in README.
3. Make one return of five bottles and verify all three linked records.
4. Make a POS Invoice without redemption and verify zero earned bottle points.
5. Redeem a subset and then the rest; verify point balances, no overdraft and POS Closing Entry.
6. Repeat the API request using the same request_id; verify idempotence.
7. Attempt an unauthorized API call, a foreign company POS profile, invalid customer and malformed quantity.
8. Attempt cancellation before and after redemption.
9. Compare Stock Ledger, General Ledger and Loyalty Point Entry balances.
