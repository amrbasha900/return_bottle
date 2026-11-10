# Return Bottle — ERPNext v15 POS

A lightweight Frappe app for receiving **empty glass bottles** at the standard ERPNext POS.
A cashier chooses a customer, enters the bottle count, and awards **3 loyalty points per bottle** (configurable).
Each point can be redeemed for **EGP 1** through ERPNext's existing loyalty redemption UI.

**No Sales Return** and **no points earned from normal POS sales** for the bottle programme.
No ERPNext core files are edited.

## Install / update

> Test on a separate site before production; this repository branch has not yet been run against a real ERPNext bench.

```bash
cd /home/frappe/frappe-bench
bench get-app https://github.com/amrbasha900/return_bottle.git --branch feat/bottle-return-pos-loyalty
bench --site YOUR_TEST_SITE install-app return_bottle
bench --site YOUR_TEST_SITE migrate
bench build --app return_bottle
bench --site YOUR_TEST_SITE clear-cache
bench restart
```

If the app is already present, use `git fetch` / `git checkout feat/bottle-return-pos-loyalty` inside `apps/return_bottle`, then run migration, build and cache clear. Do not install the app twice. Replace `YOUR_TEST_SITE` with the actual test site. On a shared bench, `bench restart` affects other sites; coordinate restarts.

## Initial setup (System Manager / Accounts Manager)

1. **Create a stock Item** `EMPTY-GLASS-BOTTLE`, with **Maintain Stock**, a stock UOM of `Nos`, and no serial/batch numbers.
2. **Create a receiving Warehouse**, e.g. `Empty Bottle Returns`, under the same Company.
3. **Create two company accounts**:
   - `Bottle Rewards Liability`: **Liability**, EGP, non-group.
   - `Bottle Rewards Expense`: **Expense**, EGP, non-group.
   - If the empty bottle has recoverable stock value, additionally create `Bottle Stock Clearing`: **Asset**, EGP, non-group, not Account Type Stock. Enable perpetual inventory. For zero book value, no clearing account is needed.
4. **Create Loyalty Program** `Bottle Return Rewards`:
   - Company = your EGP company; Type = Single Tier Program; From Date = today or earlier.
   - Add a tier `Bottle Return`, Minimum Total Spent = 0, Collection Factor = e.g. 1,000,000,000 (unused for POS invoices in this app).
   - Conversion Factor = **1**, expiry duration e.g. **365 days**.
   - **Expense Account = Bottle Rewards Liability**, not the expense account; this makes redemption debit the reward liability. Select a Cost Center.
   - Auto Opt In = off (the app enrolls customers at their first bottle return).
   - Do not use this loyalty programme for normal invoices or other sales channels that are not protected by this app.
5. Open **Bottle Return Settings**:
   - Enable Bottle Returns = checked.
   - Company, Loyalty Program, Empty Bottle Item, Return Warehouse.
   - Points per Bottle = **3**.
   - Stock Valuation per Bottle = **0** *only if the bottle's book/recoverable value is genuinely zero*; otherwise set its book value and a Stock Clearing Account.
   - Rewards Expense Account = `Bottle Rewards Expense`.
6. Give cashiers **Sales User** or **Sales Manager** permissions and ensure they can select/read the returning Customer. Configure an ERPNext **POS Profile** and open **POS Opening Entry**.
7. Hard refresh `/app/point-of-sale`. The button **Return Bottles** appears beside **Full Screen** in the page toolbar (also available in the page actions on narrow displays).

## Cashier instructions (Arabic)

1. افتح **Point of Sale** وسجّل **POS Opening Entry**.
2. اضغط زر **Return Bottles / استرجاع الزجاجات**.
3. اختار **العميل الحقيقي** (مش Walk-in المشترك). لو جديد، أنشئ Customer من النظام أولًا؛ رقم الموبايل مفيد للتعرف عليه بعد كده.
4. اكتب **عدد الزجاجات**. هتظهر النقاط تلقائيًا: كل زجاجة 3 نقاط.
5. اضغط **Confirm Bottle Return** مرة واحدة.
6. هتظهر رسالة برقم `Bottle Return` وعدد النقاط المكتسبة. النظام ينشئ **Stock Entry** و**Journal Entry** و**Loyalty Point Entry**.
7. عند الشراء، اختار نفس العميل في POS ثم استخدم **Redeem Loyalty Points** من شاشة الدفع القياسية. الـ15 نقطة تخصم 15 جنيه من إجمالي فاتورة الـPOS.

### Example

Five bottles received = **15 points**, worth **EGP 15**.
The next EGP 100 invoice is settled by EGP 15 loyalty redemption and EGP 85 payment.

### Accounting

For a zero-value empty bottle, 5 bottles at EGP 3 create:
- DR Bottle Rewards Expense: EGP 15
- CR Bottle Rewards Liability: EGP 15

For bottles worth EGP 2 each, the stock receipt debits inventory EGP 10 and credits Bottle Stock Clearing EGP 10. The reward journal debits clearing EGP 10 and reward expense EGP 5, and credits rewards liability EGP 15.

Redemption uses the standard ERPNext POS loyalty accounting, debiting **Bottle Rewards Liability** rather than recording expense a second time. Confirm the tax and valuation treatment with your accountant.

### Access controls and safety

- Requires a real Customer, enabled settings, a matching POS Profile and the logged-in user's open POS session.
- Captures a unique request ID to protect against duplicate submissions after network retries.
- The rate, company, item, warehouse, POS and accounting accounts are checked on the server, not trusted from the browser.
- Cancelling a return that has already been redeemed is blocked until the dependent redemptions are reversed.
- Only the **POS Invoice** controller is overridden to disable normal *earning* for this programme. ERPNext's original *redemption* behavior is preserved.
- The default POS loyalty balance may not immediately refresh while a sale is open: reselect the customer or create a new POS invoice.

## Manual validation checklist on an isolated test site

- [ ] POS button appears exactly once after page refresh / a new POS session.
- [ ] Cashier cannot submit without customer or for zero/negative/fractional quantities.
- [ ] A 5-bottle return produces one submitted Stock Entry (5 units), one Journal Entry, and one +15 Loyalty Point Entry.
- [ ] Retry the exact API request ID: returns the original document, not additional points/stock.
- [ ] A normal EGP 100 POS sale with no redemption awards **zero** bottle points.
- [ ] Redeem 15 points against a new EGP 100 sale. Validate cashier payments, points ledger and GL.
- [ ] Cancel an **unredeemed** return; stock, journal and earned loyalty entry reverse.
- [ ] Attempt to cancel a **redeemed** return: cancellation must be refused.
- [ ] Check balances after POS Closing Entry and run stock and General Ledger reports.
- [ ] Confirm multi-company restrictions and a non-permitted user cannot issue rewards.

## Limitations

- One EGP company and one bottle item per site for this minimal release (configured in the singleton settings).
- Needs a stock valuation/account policy approved by accounting.
- Depends on ERPNext version-15 POS page and POS Invoice class; verify compatibility with your installed patch version, other POS customizations and ERPNext updates before production.
- In particular, **override_doctype_class** cannot safely be composed automatically with a second app overriding POS Invoice. Merge or remove conflicting overrides.
- Existing separate customer Loyalty Programs are not overwritten; the cashier must resolve that customer configuration first.
- No background worker, separate frontend, cash payout or automatic creation of Customers.
