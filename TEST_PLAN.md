# Verification checklist — multiple POS Profiles

This checklist is manual; GitHub code review is not a passing ERPNext integration test.

1. On an isolated ERPNext v15 site, install or upgrade the app, migrate, build and clear cache.
2. Assert the old `Bottle Return Settings` DocType was removed and no existing submitted Bottle Return records changed.
3. Configure POS Profile A with **Empty Bottles A**, Profile B with **Empty Bottles B**, both with the same company-currency loyalty programme.
4. Leave Profile C bottle returns disabled: it should not show a Return Bottles action.
5. Open POS A as a cashier; return 5 bottles for a real Customer. Confirm Stock Entry A +5 in Warehouse A only, 15 points, valid Journal Entry.
6. Open POS B as a second cashier; return 2 bottles. Confirm Stock Entry B +2 in Warehouse B only, 6 points, valid Journal Entry.
7. Verify the same customer has 21 unexpired points, redeemable in both A and B.
8. POS sale without redemption on either profile must award **zero** points for this programme.
9. Test idempotency with the same request UUID, different payload replay, negative/fractional/zero/huge quantities, and a non-permitted customer.
10. Disable a profile or close its POS Opening Entry; receiving bottles must be refused. A different profile/company must not be usable.
11. Cancel a return before redemption: its points, accounting and stock are reversed. Once its points have been redeemed, cancellation is blocked.
12. Verify POS Closing Entry, General Ledger, Stock Ledger and Loyalty Point Entry totals after sale and redemption.
13. Try changing a profile's destination warehouse after the first return. Historical receipts must remain in their originally recorded warehouse.
14. Verify single-tier loyalty settings, customer enrollment, company currency and optional non-zero stock valuation.
15. Check conflict with other apps overriding POS Invoice before enabling in a shared bench.
