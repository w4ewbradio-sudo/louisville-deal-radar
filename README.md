# Louisville Deal Radar

Static GitHub Pages dashboard for Louisville flip/BRRR candidates.

## Privacy note
GitHub Pages is static hosting. The included password gate is client-side obfuscation, not true security. Do not publish private finances, account docs, or non-public deal info here. For true privacy, use Cloudflare Access or the private Marvin dashboard.

## Daily workflow
- `data/deals.json` is the current deal feed.
- `scripts/build_daily.py` rebuilds the homepage and dated snapshot.
- Deal records can come from emailed CSVs, manual entries, MLS exports, wholesaler lists, Zillow/Realtor links, or public data enrichments.

## Key formulas
- Flip max offer: `(ARV * 0.70) - rehab_estimate`
- Flip spread: `ARV - purchase_price - rehab_estimate - selling_costs - holding_costs`
- BRRR total basis: `purchase_price + rehab_estimate`
- Refi proceeds: `ARV * refi_ltv`
- Cash left in deal: `total_basis + closing_costs - refi_proceeds`
- DSCR approximation: `monthly_rent / (PITI + HOA + maintenance reserve)`
