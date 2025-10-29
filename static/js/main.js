const $ = (s, d=document)=>d.querySelector(s);
const $$ = (s, d=document)=>Array.from(d.querySelectorAll(s));

async function post(url, data){
  return fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data||{})});
}

function attach() {
  // edit phone
  $$('.phone').forEach(inp=>{
    inp.addEventListener('change', async e=>{
      const tr = e.target.closest('tr');
      const id = tr.dataset.id;
      await post(`/update_phone/${id}`, {client_phone: e.target.value});
    });
  });

  // badge click to trigger call
  $$('.badge-clickable').forEach(badge=>{
    badge.addEventListener('click', async e=>{
      const tr = e.target.closest('tr');
      const id = tr.dataset.id;
      const currentAction = e.target.dataset.action;

      // Don't trigger call if already resolved or connecting
      if(currentAction === "Resolved" || currentAction === "Connecting") {
        return;
      }

      await post(`/call/${id}`);
      refreshRow(id);
    });
  });

  // search
  $('#search').addEventListener('input', e=>{
    const q = e.target.value.toLowerCase();
    $$('#txnTable tbody tr').forEach(r=>{
      r.style.display = r.innerText.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}

async function refreshRow(id){
  const res = await fetch('/transactions'); const all = await res.json();
  const t = all.find(x=>x.id===id);
  if(!t) return;
  const tr = document.querySelector(`tr[data-id="${id}"]`);
  const phoneInput = tr.querySelector('.phone');

  // Only update phone if user is not currently editing it
  if(document.activeElement !== phoneInput) {
    phoneInput.value = t.client_phone;
  }

  const badge = tr.querySelector('.badge');
  badge.textContent = t.action; badge.dataset.action = t.action;
}

async function poll(){
  const res = await fetch('/transactions'); const all = await res.json();
  all.forEach(t=>refreshRow(t.id));
}

attach();
setInterval(poll, 5000);
