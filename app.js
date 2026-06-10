async function sha256(s){const b=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s));return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')}
async function unlock(){const v=document.getElementById('pw').value; if(await sha256(v)===PASS_HASH){localStorage.setItem('ldr_ok','1');show()} else alert('Nope. Tiny moat says no.')}
function show(){document.getElementById('lock').hidden=true;document.getElementById('app').hidden=false}
if(localStorage.getItem('ldr_ok')==='1') show();
document.getElementById('pw')?.addEventListener('keydown',e=>{if(e.key==='Enter') unlock()});
