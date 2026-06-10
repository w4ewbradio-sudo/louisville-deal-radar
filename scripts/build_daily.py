#!/usr/bin/env python3
import json, hashlib, datetime, pathlib, html
ROOT = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((ROOT/'data'/'deals.json').read_text())
auth = json.loads((ROOT/'data'/'auth.json').read_text())
ass = data['assumptions']
now = datetime.datetime.now().astimezone()

def money(x):
    if x is None: return 'n/a'
    return '${:,.0f}'.format(x)

def pct(x): return '{:.1f}%'.format(x*100)

def analyze(d):
    price=d.get('list_price') or 0; arv=d.get('arv_estimate') or 0; rehab=d.get('rehab_estimate') or 0; rent=d.get('rent_estimate') or 0
    selling=arv*ass['selling_cost_percent']; holding=ass['holding_cost_monthly']*ass['holding_months']
    max_offer=arv*ass['flip_rule_percent']-rehab
    flip_profit=arv-price-rehab-selling-holding
    basis=price+rehab
    closing=price*ass['closing_cost_percent']
    refi=arv*ass['refi_ltv']
    cash_left=basis+closing-refi
    monthly_reserves=rent*(ass['maintenance_reserve_percent_rent']+ass['vacancy_percent_rent']+ass['management_percent_rent'])
    # PITI placeholder: assumes 75% of basis financed at 7.5%, 30yr, plus estimated taxes/insurance.
    loan=basis*.75; r=.075/12; n=360
    pi=loan*(r*(1+r)**n)/(((1+r)**n)-1) if loan else 0
    taxes=(arv*0.0125)/12
    insurance=140
    piti=pi+taxes+insurance
    dscr=rent/(piti+monthly_reserves) if piti+monthly_reserves else 0
    score=0
    score += 30 if flip_profit>=35000 else 15 if flip_profit>=20000 else 0
    score += 25 if price<=max_offer else 10 if price<=max_offer*1.08 else 0
    score += 20 if cash_left<=15000 else 10 if cash_left<=30000 else 0
    score += 15 if dscr>=1.2 else 8 if dscr>=1.05 else 0
    score += 10 if d.get('arv_confidence')=='high' else 5 if d.get('arv_confidence')=='medium' else 0
    return dict(max_offer=max_offer, flip_profit=flip_profit, selling=selling, holding=holding, basis=basis, closing=closing, refi=refi, cash_left=cash_left, dscr=dscr, score=score)

for d in data['deals']:
    d['metrics']=analyze(d)

rows='\n'.join(f"""
<tr>
<td><strong>{html.escape(d['address'])}</strong><br><span>{html.escape(d.get('neighborhood',''))} · {html.escape(d.get('property_type',''))} · {d.get('beds','?')}/{d.get('baths','?')} · {d.get('sqft','?')} sqft</span></td>
<td>{money(d.get('list_price'))}</td><td>{money(d.get('arv_estimate'))}<br><small>{d.get('arv_confidence','?')} confidence</small></td>
<td>{money(d.get('rehab_estimate'))}</td><td>{money(d['metrics']['max_offer'])}</td>
<td class="{'good' if d['metrics']['flip_profit']>25000 else 'warn' if d['metrics']['flip_profit']>0 else 'bad'}">{money(d['metrics']['flip_profit'])}</td>
<td>{money(d.get('rent_estimate'))}<br><small>DSCR ~ {d['metrics']['dscr']:.2f}</small></td>
<td>{money(d['metrics']['cash_left'])}</td>
<td><span class="score">{d['metrics']['score']}</span><br><small>{', '.join(d.get('tags',[]))}</small></td>
</tr>
""" for d in sorted(data['deals'], key=lambda x:x['metrics']['score'], reverse=True))

cards='\n'.join(f"""
<div class="deal-card">
  <div class="deal-head"><div><h3>{html.escape(d['address'])}</h3><p>{html.escape(d.get('neighborhood',''))}</p></div><div class="score big">{d['metrics']['score']}</div></div>
  <div class="grid">
    <div><label>Price</label><strong>{money(d.get('list_price'))}</strong></div>
    <div><label>ARV</label><strong>{money(d.get('arv_estimate'))}</strong></div>
    <div><label>Max offer</label><strong>{money(d['metrics']['max_offer'])}</strong></div>
    <div><label>Flip profit</label><strong>{money(d['metrics']['flip_profit'])}</strong></div>
    <div><label>Rent</label><strong>{money(d.get('rent_estimate'))}</strong></div>
    <div><label>Cash left BRRR</label><strong>{money(d['metrics']['cash_left'])}</strong></div>
  </div>
  <p>{html.escape(d.get('notes',''))}</p>
  <p class="source">Source: {html.escape(d.get('source',''))} {('<a href="'+html.escape(d.get('source_url',''))+'">link</a>') if d.get('source_url') else ''}</p>
</div>
""" for d in sorted(data['deals'], key=lambda x:x['metrics']['score'], reverse=True)[:5])

html_doc=f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Louisville Deal Radar</title><link rel="stylesheet" href="styles.css"></head>
<body>
<div id="lock"><div class="lock-card"><h1>Louisville Deal Radar</h1><p>Private static dashboard. Enter passphrase.</p><input id="pw" type="password" placeholder="Passphrase"><button onclick="unlock()">Open</button><p class="tiny">Static GitHub Pages gate, casual privacy only.</p></div></div>
<main id="app" hidden>
<header><div><h1>Louisville Deal Radar</h1><p>Flip + BRRR candidates for {', '.join(data['target_areas'])}</p></div><div class="stamp">Updated {now.strftime('%b %-d, %Y %-I:%M %p')}</div></header>
<section class="summary"><div><label>Candidates</label><strong>{len(data['deals'])}</strong></div><div><label>Best score</label><strong>{max([d['metrics']['score'] for d in data['deals']] or [0])}</strong></div><div><label>Refi LTV</label><strong>{pct(ass['refi_ltv'])}</strong></div><div><label>Flip rule</label><strong>{pct(ass['flip_rule_percent'])}</strong></div></section>
<section><h2>Top cards</h2><div class="cards">{cards}</div></section>
<section><h2>Deal table</h2><div class="table-wrap"><table><thead><tr><th>Property</th><th>Price</th><th>ARV</th><th>Rehab</th><th>Max offer</th><th>Flip profit</th><th>Rent / DSCR</th><th>Cash left</th><th>Score</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="notes"><h2>What I need from Eric</h2><ul><li>Target max purchase price/cash to deploy.</li><li>Financing assumptions: down payment, rate, points, refi LTV, hard-money vs bank.</li><li>Minimum acceptable flip profit and BRRR cash left/DSCR.</li><li>Property types to include/exclude.</li><li>Any MLS/PropStream/wholesaler/Rentometer exports or logins you want me to use.</li></ul></section>
</main><script>const PASS_HASH='{auth['password_sha256']}';</script><script src="app.js"></script></body></html>"""
(ROOT/'index.html').write_text(html_doc)
(ROOT/'daily'/f"{now.date().isoformat()}.html").write_text(html_doc)
print('built', ROOT/'index.html')
