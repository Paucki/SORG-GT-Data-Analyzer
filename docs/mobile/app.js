const KEY='sorg_gt_mobile_v1';
const state=JSON.parse(localStorage.getItem(KEY)||'{"entries":[],"cars":[],"drivers":[]}');
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
function save(){localStorage.setItem(KEY,JSON.stringify(state));render()}
function esc(v=''){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function go(name){$$('.view').forEach(v=>v.classList.toggle('active',v.dataset.view===name));$$('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));window.scrollTo({top:0,behavior:'smooth'})}
$$('[data-tab]').forEach(b=>b.onclick=()=>go(b.dataset.tab));$$('[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go));
function entryHtml(e){return `<div class="entry"><div class="entry-top"><div class="entry-title">${esc(e.car)}</div><div class="entry-time">${new Date(e.ts).toLocaleString('de-DE',{dateStyle:'short',timeStyle:'short'})}</div></div><div class="entry-meta">${esc(e.driver)} · ${esc(e.session)}${e.setName?' · '+esc(e.setName):''}</div><div class="pressures"><div class="pbox"><b>${e.fl}</b><span>VL</span></div><div class="pbox"><b>${e.fr}</b><span>VR</span></div><div class="pbox"><b>${e.rl}</b><span>HL</span></div><div class="pbox"><b>${e.rr}</b><span>HR</span></div></div>${e.note?`<div class="entry-meta" style="margin-top:9px">${esc(e.note)}</div>`:''}</div>`}
function render(){
  $('#statEntries').textContent=state.entries.length;$('#statCars').textContent=state.cars.length;$('#statDrivers').textContent=state.drivers.length;
  const recent=state.entries.slice().reverse().slice(0,4);$('#recentList').className='list'+(recent.length?'':' empty');$('#recentList').innerHTML=recent.length?recent.map(entryHtml).join(''):'Noch keine Messungen vorhanden.';
  const all=state.entries.slice().reverse();$('#allList').className='list card'+(all.length?'':' empty');$('#allList').innerHTML=all.length?all.map(entryHtml).join(''):'Noch keine Messungen vorhanden.';
  $('#carList').innerHTML=state.cars.map(x=>`<span class="chip">${esc(x)}</span>`).join('');$('#driverList').innerHTML=state.drivers.map(x=>`<span class="chip">${esc(x)}</span>`).join('');
}
$('#pressureForm').onsubmit=e=>{e.preventDefault();const v=id=>$(id).value.trim();const entry={ts:Date.now(),car:v('#car'),driver:v('#driver'),session:v('#session'),setName:v('#setName'),fl:v('#fl'),fr:v('#fr'),rl:v('#rl'),rr:v('#rr'),note:v('#note')};state.entries.push(entry);if(entry.car&&!state.cars.includes(entry.car))state.cars.push(entry.car);if(entry.driver&&!state.drivers.includes(entry.driver))state.drivers.push(entry.driver);save();e.target.reset();go('dashboard')};
function add(kind,input){const v=$(input).value.trim();if(v&&!state[kind].includes(v)){state[kind].push(v);save()}$(input).value=''}
$('#addCar').onclick=e=>{e.preventDefault();add('cars','#newCar')};$('#addDriver').onclick=e=>{e.preventDefault();add('drivers','#newDriver')};
$('#exportBtn').onclick=()=>{const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='SORG_GT_Mobile_Export.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
$('#clearBtn').onclick=()=>{if(confirm('Wirklich alle lokal gespeicherten Daten löschen?')){state.entries=[];state.cars=[];state.drivers=[];save()}};
let deferredPrompt=null;window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;$('#installBtn').classList.remove('hidden')});$('#installBtn').onclick=async()=>{if(!deferredPrompt)return;deferredPrompt.prompt();await deferredPrompt.userChoice;deferredPrompt=null;$('#installBtn').classList.add('hidden')};
if('serviceWorker' in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js'));
render();