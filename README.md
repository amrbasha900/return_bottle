# Return Bottle — ERPNext v15 POS

Lightweight bottle returns inside **standard ERPNext POS**, with an independent **return warehouse for each POS Profile**. No core ERPNext modifications and no separate cashier screen.

**Reward:** 3 points per empty bottle (or a configured whole-number rate); 1 point = EGP 1 in the native ERPNext POS loyalty redemption. Normal POS sales never earn points from the bottle-return loyalty programme.

## POS Profile settings (new)

Once the app is installed or migrated, open **Accounts > POS Profile > [your profile]**. Under **Empty Bottle Returns**, fill:

| Field | Example / purpose |
| --- | --- |
| Enable Bottle Returns | On for this POS only |
| Empty Bottle Warehouse | Branch A - Empty Bottles; **separate from regular selling warehouse** |
| Empty Bottle Item | EMPTY-GLASS-BOTTLE (stock-managed) |
| Reward Points per Bottle | 3 |
| Empty Bottle Valuation (EGP) | Real recoverable book value, or 0 only when justified |
| Bottle Return Loyalty Program | Bottle Return Rewards |
| Bottle Reward Expense Account | Bottle Rewards Expense (EGP expense account) |
| Bottle Stock Clearing Account | EGP non-stock Asset account, only when valuation > 0 |

**Example:** POS Profile Cairo Branch -> Empty Bottles - Cairo; POS Profile Giza Branch -> Empty Bottles - Giza. Each return uses only the warehouse configured for the cashier's **open** POS Profile. The shared loyalty programme lets a customer earn points in one branch and redeem in another branch of the same EGP company.

No `Bottle Return Settings` singleton remains. A migration patch retires that DocType **without copying its old warehouse automatically**: configure each POS Profile explicitly before receiving bottles. Existing submitted Bottle Return records remain as they are.

## One-time prerequisites

1. Create a stock Item for empty glass bottles, e.g. `EMPTY-GLASS-BOTTLE` (Stock UOM Nos, not serialised/batched).
2. Create a leaf **Warehouse per branch** for empty bottles.
3. In the EGP company, create **Bottle Rewards Liability** (Liability account), **Bottle Rewards Expense** (Expense account), and optionally **Bottle Stock Clearing** (Asset account, not Account Type Stock) for positive inventory valuation.
4. Create one **Loyalty Program** named `Bottle Return Rewards` for the company:
   - Single Tier, From Date today or earlier, Tier `Bottle Return` with Minimum Total Spent 0 and Collection Factor 1000000000 (POS Invoice earning is disabled by the app).
   - **Conversion Factor = 1**; expiry duration e.g. 365 days; select a **Cost Center**.
   - **Expense Account = Bottle Rewards Liability** (intentionally a liability, so redemption reduces the obligation); not the rewards expense account.
   - Disable Auto Opt In. Customer enrolment occurs upon first bottle return.
5. Configure each **POS Profile** individually and enable the bottle return section only when complete. Leave it disabled on profiles not using this programme.
6. Ensure cashiers have Sales User/Sales Manager roles and Customer read permissions; a matching **POS Opening Entry** is required. Avoid a shared walk-in customer for points.

> This uses one loyalty programme across all enabled profiles in a company. Other unrelated loyalty programmes already assigned to a customer are not overwritten.

## Installation / migration

**Test on an isolated ERPNext v15 site before production.**

```bash
cd /home/frappe/frappe-bench
bench get-app https://github.com/amrbasha900/return_bottle.git --branch feat/bottle-return-pos-loyalty
bench --site YOUR_TEST_SITE install-app return_bottle
bench --site YOUR_TEST_SITE migrate
bench build --app return_bottle
bench --site YOUR_TEST_SITE clear-cache
```

If already installed, check out/pull the feature branch in `apps/return_bottle`, and run `migrate`, `build`, and `clear-cache` for the intended site. `bench restart` is only needed where processes need recycling: **it affects all sites in a shared bench**, so coordinate it.

## دليل استخدام الكاشير

1. افتح **Point of Sale** بحساب الكاشير وسجّل **POS Opening Entry** لبروفايل نقطة البيع.
2. إذا كانت الخاصية مفعلة في هذا البروفايل، سيظهر زر **Return Bottles** بجوار أدوات شاشة POS.
3. اختار **العميل**، واكتب **عدد الزجاجات**. هتظهر النقاط المستحقة تلقائيًا (5 زجاجات = 15 نقطة).
4. النافذة تعرض **مخزن الزجاجات المرتجعة** الخاص بالبروفايل الحالي للقراءة فقط، ولا يستطيع الكاشير تغييره.
5. اضغط **Confirm Bottle Return**. يتم إنشاء Bottle Return + Stock Entry + Journal Entry + Loyalty Point Entry في نفس عملية الاعتماد.
6. عند عملية شراء لاحقة اختر نفس العميل واستخدم **Redeem Loyalty Points** من الدفع القياسي: فاتورة 100 جنيه - 15 نقطة = 85 جنيه مستحق.

## Accounting

For five returned bottles at EGP 3 each and an empty bottle inventory value of zero, award issuance generates DR Bottle Rewards Expense 15 / CR Bottle Rewards Liability 15, along with a zero-valued stock receipt of five bottles. For a value of EGP 2 per bottle, the stock receipt is DR Inventory 10 / CR Stock Clearing 10; the reward journal is DR Stock Clearing 10, DR Rewards Expense 5 / CR Rewards Liability 15. Standard POS loyalty redemption debits the programme's linked Liability account and credits the customer settlement. Confirm local taxation and bottle valuation with accounting.

## Safety and assumptions

- Server validates the selected profile, current cashier's open POS session, customer permissions, target warehouse, reward rate and accounting configuration.
- API request UUID prevents duplicate issuance during network retries; cancellation of a redeemed return is blocked.
- No automatic copying of legacy singleton configuration to all branches, and no fallback to POS selling warehouse.
- Enabled bottle return loyalty programmes **never earn points from normal POS sales**, even on a different profile of the same company, via the POS Invoice class override. Redemption uses native ERPNext logic.
- Existing POS Invoice overrides from another Frappe app need explicit reconciliation. Standard Sales Invoices outside POS are not part of this change, so do not use the bottle programme to award points on those invoices.
- Initial release uses an EGP company and 1:1 EGP loyalty-point conversion, as specified.

## QA before merge

See [TEST_PLAN.md](TEST_PLAN.md). This code has **not** been run on a live ERPNext bench in this environment. Test stock posting, ledger balancing, POS Closing Entry, redemption and cancellations against your installed ERPNext v15 patch version before production.
