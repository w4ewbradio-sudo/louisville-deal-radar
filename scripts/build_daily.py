#!/usr/bin/env python3
import json, datetime, pathlib, html
ROOT = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((ROOT/'data'/'deals.json').read_text())
auth = json.loads((ROOT/'data'/'auth.json').read_text())
ass = data['assumptions']
now = datetime.datetime.now().astimezone()

NEIGHBORHOODS = {
    'St. Matthews': {'vibe':'stable, competitive, usually safer, harder to find deep discounts', 'risk':'low', 'strategy':'BRRR only if bought unusually well; light flips can work'},
    'Crescent Hill': {'vibe':'older housing stock, strong buyer demand, rehab surprises possible', 'risk':'low-med', 'strategy':'good flip candidate if ARV comps are tight'},
    'Butchertown': {'vibe':'small inventory, appreciation story, quirky properties', 'risk':'medium', 'strategy':'watch for oddball deals and zoning upside'},
    'Germantown': {'vibe':'good first-flip zone, lots of small houses, demand is real', 'risk':'medium', 'strategy':'strong candidate for cosmetic-to-medium rehab'},
    'Highlands': {'vibe':'high demand, older expensive homes, fewer obvious bargains', 'risk':'low-med', 'strategy':'quality flips, cautious with rehab scope'},
    'Iroquois': {'vibe':'more affordability, block-by-block safety matters', 'risk':'block-by-block', 'strategy':'rental math may work, crime filter is critical'}
}

def money(x):
    if x is None: return 'n/a'
    return '${:,.0f}'.format(x)

def pct(x): return '{:.0f}%'.format(x*100)

def cls(value, good, warn):
    return 'good' if value >= good else 'warn' if value >= warn else 'bad'

def analyze(d):
    price=d.get('list_price') or 0
    arv=d.get('arv_estimate') or 0
    rehab=d.get('rehab_estimate') or 0
    rent=d.get('rent_estimate') or 0
    timeline=d.get('rehab_months') or ass.get('holding_months',4)
    selling=arv*ass['selling_cost_percent']
    holding=ass['holding_cost_monthly']*timeline
    max_offer=arv*ass['flip_rule_percent']-rehab
    flip_profit=arv-price-rehab-selling-holding
    basis=price+rehab
    closing=price*ass['closing_cost_percent']
    refi=arv*ass['refi_ltv']
    cash_left=basis+closing-refi
    down_payment=price*ass.get('down_payment_percent',.20)
    startup_cash_needed=down_payment+rehab+closing
    monthly_reserves=rent*(ass['maintenance_reserve_percent_rent']+ass['vacancy_percent_rent']+ass['management_percent_rent'])
    loan=max(price-down_payment, 0)
    rate=ass.get('heloc_rate',.08)/12
    n=360
    pi=loan*(rate*(1+rate)**n)/(((1+rate)**n)-1) if loan else 0
    taxes=(arv*0.0125)/12
    insurance=d.get('insurance_monthly') or 140
    monthly_cost=pi+taxes+insurance+monthly_reserves
    monthly_profit=rent-monthly_cost
    dscr=rent/monthly_cost if monthly_cost else 0
    score=0
    score += 25 if flip_profit>=ass.get('flip_min_profit_target',30000) else 12 if flip_profit>=20000 else 0
    score += 20 if monthly_profit>=500 else 14 if monthly_profit>=ass.get('rental_min_monthly_profit_target',300) else 5 if monthly_profit>=100 else 0
    score += 20 if price<=max_offer else 8 if price<=max_offer*1.08 else 0
    score += 15 if startup_cash_needed<=ass.get('heloc_available',100000) else 5 if startup_cash_needed<=ass.get('heloc_available',100000)*1.15 else 0
    score += 10 if timeline<=ass.get('rehab_timeline_target_months_max',5) else 0
    score += 10 if d.get('arv_confidence')=='high' else 5 if d.get('arv_confidence')=='medium' else 0
    safety=d.get('safety_flag','unknown')
    if safety=='avoid': score-=35
    elif safety=='caution': score-=10
    score=max(0,min(100,score))
    if safety=='avoid': verdict='Hard pass, safety filter'
    elif flip_profit>=ass.get('flip_min_profit_target',30000) and startup_cash_needed<=ass.get('heloc_available',100000): verdict='Flip candidate'
    elif monthly_profit>=ass.get('rental_min_monthly_profit_target',300): verdict='Rental candidate'
    elif score>=55: verdict='Research deeper'
    else: verdict='Watch only'
    return dict(max_offer=max_offer, flip_profit=flip_profit, selling=selling, holding=holding, basis=basis, closing=closing, refi=refi, cash_left=cash_left, dscr=dscr, score=score, monthly_profit=monthly_profit, monthly_cost=monthly_cost, startup_cash_needed=startup_cash_needed, down_payment=down_payment, timeline=timeline, verdict=verdict)

for d in data['deals']:
    d['metrics']=analyze(d)

ordered=sorted(data['deals'], key=lambda x:x['metrics']['score'], reverse=True)
best=max([d['metrics']['score'] for d in data['deals']] or [0])
flip_candidates=sum(1 for d in data['deals'] if d['metrics']['flip_profit']>=ass.get('flip_min_profit_target',30000))
rental_candidates=sum(1 for d in data['deals'] if d['metrics']['monthly_profit']>=ass.get('rental_min_monthly_profit_target',300))
heloc_fit=sum(1 for d in data['deals'] if d['metrics']['startup_cash_needed']<=ass.get('heloc_available',100000))

cards='\n'.join(f"""
<article class="deal-card" data-neighborhood="{html.escape(d.get('neighborhood',''))}" data-verdict="{html.escape(d['metrics']['verdict'])}" data-score="{d['metrics']['score']}">
  <div class="deal-head">
    <div><p class="eyebrow">{html.escape(d.get('neighborhood','Unknown'))} · {html.escape(d.get('property_type',''))}</p><h3>{html.escape(d['address'])}</h3></div>
    <div class="score big">{d['metrics']['score']}</div>
  </div>
  <div class="verdict {d['metrics']['verdict'].split()[0].lower()}">{html.escape(d['metrics']['verdict'])}</div>
  <div class="metric-grid">
    <div><label>Price</label><strong>{money(d.get('list_price'))}</strong></div>
    <div><label>ARV</label><strong>{money(d.get('arv_estimate'))}</strong><small>{d.get('arv_confidence','?')} confidence</small></div>
    <div><label>Rehab</label><strong>{money(d.get('rehab_estimate'))}</strong><small>{d['metrics']['timeline']} mo est.</small></div>
    <div><label>Max offer</label><strong>{money(d['metrics']['max_offer'])}</strong></div>
    <div><label>Flip net</label><strong class="{cls(d['metrics']['flip_profit'], ass.get('flip_min_profit_target',30000), 15000)}">{money(d['metrics']['flip_profit'])}</strong></div>
    <div><label>Rental profit</label><strong class="{cls(d['metrics']['monthly_profit'], 500, ass.get('rental_min_monthly_profit_target',300))}">{money(d['metrics']['monthly_profit'])}/mo</strong></div>
    <div><label>Cash needed</label><strong class="{'good' if d['metrics']['startup_cash_needed']<=ass.get('heloc_available',100000) else 'bad'}">{money(d['metrics']['startup_cash_needed'])}</strong></div>
    <div><label>Safety</label><strong>{html.escape(d.get('safety_flag','unknown'))}</strong></div>
  </div>
  <div class="bars"><span style="width:{d['metrics']['score']}%"></span></div>
  <p>{html.escape(d.get('notes',''))}</p>
  <p class="source">Source: {html.escape(d.get('source',''))} {('<a href="'+html.escape(d.get('source_url',''))+'">open</a>') if d.get('source_url') else ''}</p>
</article>
""" for d in ordered)

rows='\n'.join(f"""
<tr data-neighborhood="{html.escape(d.get('neighborhood',''))}">
<td><strong>{html.escape(d['address'])}</strong><br><span>{html.escape(d.get('neighborhood',''))} · {d.get('beds','?')}/{d.get('baths','?')} · {d.get('sqft','?')} sqft</span></td>
<td>{money(d.get('list_price'))}</td><td>{money(d.get('arv_estimate'))}</td><td>{money(d.get('rehab_estimate'))}</td>
<td>{money(d['metrics']['startup_cash_needed'])}</td><td>{money(d['metrics']['max_offer'])}</td>
<td class="{cls(d['metrics']['flip_profit'], ass.get('flip_min_profit_target',30000), 15000)}">{money(d['metrics']['flip_profit'])}</td>
<td class="{cls(d['metrics']['monthly_profit'], 500, ass.get('rental_min_monthly_profit_target',300))}">{money(d['metrics']['monthly_profit'])}/mo</td>
<td>{html.escape(d.get('safety_flag','unknown'))}</td><td><span class="score">{d['metrics']['score']}</span></td>
</tr>
""" for d in ordered)

neighborhood_cards='\n'.join(f"""
<div class="hood-card"><h3>{html.escape(name)}</h3><p>{html.escape(info['vibe'])}</p><div><span class="pill">Risk: {html.escape(info['risk'])}</span></div><small>{html.escape(info['strategy'])}</small></div>
""" for name,info in NEIGHBORHOODS.items())

source_items=''.join(f'<li>{html.escape(line)}</li>' for line in [
    'Email me listing links, MLS/PropStream exports, wholesaler sheets, screenshots, or addresses.',
    'For every candidate I’ll estimate ARV from comps, rehab, safety, carrying time, flip net, rental profit, and HELOC fit.',
    'Best paid next step if serious: PropStream/BatchLeads or MLS export access, plus Rentometer for rental comps.',
    'Public baseline sources: Jefferson PVA, LOJIC parcel/GIS layers, Louisville permits/open data, FEMA flood maps.'
])

html_doc=f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Louisville Deal Radar</title><link rel="stylesheet" href="styles.css"></head>
<body>
<div id="lock"><div class="lock-card"><div class="orb"></div><h1>Louisville Deal Radar</h1><p>Private static dashboard. Enter passphrase.</p><input id="pw" type="password" placeholder="Passphrase"><button onclick="unlock()">Open radar</button><p class="tiny">Static GitHub Pages gate, casual privacy only.</p></div></div>
<main id="app" hidden>
<header class="hero"><div><p class="eyebrow">Flip + BRRR command center</p><h1>Louisville Deal Radar</h1><p>Focused on {', '.join(data['target_areas'])}. Current mode: learn fast, avoid sketchy blocks, preserve capital, build the war chest.</p></div><div class="stamp"><strong>Updated</strong><br>{now.strftime('%b %-d, %Y %-I:%M %p')}</div></header>
<section class="summary">
  <div><label>Candidates</label><strong>{len(data['deals'])}</strong><small>active feed</small></div>
  <div><label>Best score</label><strong>{best}</strong><small>0-100 radar score</small></div>
  <div><label>Flip target</label><strong>{money(ass.get('flip_min_profit_target',30000))}</strong><small>net after costs</small></div>
  <div><label>Rental floor</label><strong>{money(ass.get('rental_min_monthly_profit_target',300))}/mo</strong><small>$500 ideal</small></div>
  <div><label>HELOC</label><strong>{money(ass.get('heloc_available',100000))}</strong><small>purchase + rehab</small></div>
  <div><label>Timeline</label><strong>{ass.get('rehab_timeline_target_months_min',3)}-{ass.get('rehab_timeline_target_months_max',5)} mo</strong><small>target rehab/turn</small></div>
</section>
<section class="control-panel"><div><h2>Radar filters</h2><p>Use this when the feed gets real listings.</p></div><div class="filters"><button data-filter="all" class="active">All</button><button data-filter="Flip candidate">Flips</button><button data-filter="Rental candidate">Rentals</button><button data-filter="Research deeper">Research</button><button data-filter="Watch only">Watch</button></div></section>
<section><div class="section-head"><h2>Deal cards</h2><span>{flip_candidates} flip target · {rental_candidates} rental target · {heloc_fit} fit HELOC</span></div><div class="cards" id="cards">{cards}</div></section>
<section class="split"><div><h2>Neighborhood radar</h2><div class="hoods">{neighborhood_cards}</div></div><aside class="notes"><h2>Feed me deals</h2><ul>{source_items}</ul><p class="tiny">Send resources to Marvin by email or Telegram. I’ll normalize them into the dashboard.</p></aside></section>
<section><h2>Full deal table</h2><div class="table-wrap"><table><thead><tr><th>Property</th><th>Price</th><th>ARV</th><th>Rehab</th><th>Cash needed</th><th>Max offer</th><th>Flip net</th><th>Rental profit</th><th>Safety</th><th>Score</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="notes"><h2>Current buy box</h2><div class="buybox"><p><strong>Capital:</strong> no starting cash assumed. Model uses 20% down and HELOC/hard money constraints.</p><p><strong>Rental:</strong> $300/mo true profit minimum, $500/mo ideal, after mortgage/taxes/insurance/reserves.</p><p><strong>Flip:</strong> $30k net is the learning target. We’ll revise after seeing Louisville inventory.</p><p><strong>Safety:</strong> high-crime blocks are hard-pass, even if the math looks cute. Math can wear a fake mustache.</p></div></section>
</main><script>const PASS_HASH='{auth['password_sha256']}';</script><script src="app.js"></script></body></html>"""
(ROOT/'index.html').write_text(html_doc)
(ROOT/'daily'/f"{now.date().isoformat()}.html").write_text(html_doc)
print('built', ROOT/'index.html')
