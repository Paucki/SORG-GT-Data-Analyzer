const SUPABASE_URL='https://cdhfmhxhhtqqoetlferj.supabase.co';
const SUPABASE_KEY='sb_publishable_r9xkC56K3zezl30297f1qQ_fsz6ztfl';
const supa=window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY);
const KEY='sorg_gt_mobile_v1';
const state=JSON.parse(localStorage.getItem(KEY)||'{"entries":[],"cars":[],"drivers":[]}');
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];

function save(){localStorage.setItem(KEY,JSON.stringify(state));render()}
function esc(v=''){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function go(name){
  $$('.view').forEach(v=>v.classList.toggle('active',v.dataset.view===name));
  $$('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  if(name==='measure') prepareMeasure();
  window.scrollTo({top:0,behavior:'smooth'});
}
$$('[data-tab]').forEach(b=>b.onclick=()=>go(b.dataset.tab));
$$('[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go));

function lastEntry(){return state.entries[state.entries.length-1]||null}
function entryHtml(e){
  return `<div class="entry"><div class="entry-top"><div class="entry-title">${esc(e.car)}</div><div class="entry-time">${new Date(e.ts).toLocaleString('de-DE',{dateStyle:'short',timeStyle:'short'})}</div></div><div class="entry-meta">${esc(e.driver)} · ${esc(e.session)}${e.setName?' · '+esc(e.setName):''}</div><div class="pressures"><div class="pbox"><span>VL</span><b>${e.fl}</b></div><div class="pbox"><span>VR</span><b>${e.fr}</b></div><div class="pbox"><span>HL</span><b>${e.rl}</b></div><div class="pbox"><span>HR</span><b>${e.rr}</b></div></div>${e.note?`<div class="entry-note">${esc(e.note)}</div>`:''}</div>`;
}

function render(){
  $('#statEntries').textContent=state.entries.length;
  $('#statCars').textContent=state.cars.length;
  $('#statDrivers').textContent=state.drivers.length;

  const last=lastEntry();
  $('#lastEntry').className=last?'':'empty-card';
  $('#lastEntry').innerHTML=last?entryHtml(last):'Noch keine Messung vorhanden.';

  const all=state.entries.slice().reverse();
  $('#allList').className='list'+(all.length?'':' empty');
  $('#allList').innerHTML=all.length?all.map(entryHtml).join(''):'Noch keine Messungen vorhanden.';

  $('#carList').innerHTML=state.cars.map(x=>`<span class="chip">${esc(x)}</span>`).join('');
  $('#driverList').innerHTML=state.drivers.map(x=>`<span class="chip">${esc(x)}</span>`).join('');
  $('#carOptions').innerHTML=state.cars.map(x=>`<option value="${esc(x)}"></option>`).join('');
  $('#driverOptions').innerHTML=state.drivers.map(x=>`<option value="${esc(x)}"></option>`).join('');
  updateContextSummary();
}

function prepareMeasure(){
  const last=lastEntry();
  if(last){
    if(!$('#car').value) $('#car').value=last.car||'';
    if(!$('#driver').value) $('#driver').value=last.driver||'';
    if(!$('#setName').value) $('#setName').value=last.setName||'';
    if(last.session) $('#session').value=last.session;
  }
  const ready=$('#car').value.trim()&&$('#driver').value.trim();
  $('#contextFields').classList.toggle('hidden',!!ready);
  $('#toggleContext').textContent=ready?'Ändern':'Auswahl';
  updateContextSummary();
  setTimeout(()=>$('#fl').focus(),120);
}

function updateContextSummary(){
  const car=$('#car').value.trim(), driver=$('#driver').value.trim(), session=$('#session').value, set=$('#setName').value.trim();
  $('#contextSummary').textContent=(car||driver)?[car,driver,session,set].filter(Boolean).join(' · '):'Fahrzeug und Fahrer auswählen';
}
['#car','#driver','#session','#setName'].forEach(id=>$(id).addEventListener('input',updateContextSummary));
$('#toggleContext').onclick=()=>{
  $('#contextFields').classList.toggle('hidden');
  $('#toggleContext').textContent=$('#contextFields').classList.contains('hidden')?'Ändern':'Fertig';
};

$('#pressureForm').onsubmit=e=>{
  e.preventDefault();
  const v=id=>$(id).value.trim();
  const entry={ts:Date.now(),car:v('#car'),driver:v('#driver'),session:v('#session'),setName:v('#setName'),fl:v('#fl'),fr:v('#fr'),rl:v('#rl'),rr:v('#rr'),note:v('#note')};
  state.entries.push(entry);
  if(entry.car&&!state.cars.includes(entry.car))state.cars.push(entry.car);
  if(entry.driver&&!state.drivers.includes(entry.driver))state.drivers.push(entry.driver);
  localStorage.setItem(KEY,JSON.stringify(state));
  ['#fl','#fr','#rl','#rr','#note'].forEach(id=>$(id).value='');
  render();
  go('home');
};

function add(kind,input){
  const v=$(input).value.trim();
  if(v&&!state[kind].includes(v)){state[kind].push(v);save()}
  $(input).value='';
}
$('#addCar').onclick=e=>{e.preventDefault();add('cars','#newCar')};
$('#addDriver').onclick=e=>{e.preventDefault();add('drivers','#newDriver')};

$('#exportBtn').onclick=()=>{
  const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='SORG_GT_Mobile_Export.json';
  a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),1000);
};
$('#clearBtn').onclick=()=>{
  if(confirm('Wirklich alle lokal gespeicherten Daten löschen?')){
    state.entries=[];state.cars=[];state.drivers=[];
    save();
  }
};

let deferredPrompt=null;
window.addEventListener('beforeinstallprompt',e=>{
  e.preventDefault();deferredPrompt=e;$('#installBtn').classList.remove('hidden');
});
$('#installBtn').onclick=async()=>{
  if(!deferredPrompt)return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt=null;
  $('#installBtn').classList.add('hidden');
};

if('serviceWorker' in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js'));
render();
async function showAuthState(){
  const {data}=await supa.auth.getSession();
  const logged=!!data.session;
  $('#loginScreen').classList.toggle('hidden',logged);
  $('#app').classList.toggle('hidden',!logged);
}
$('#loginBtn').onclick=async()=>{
  const email=$('#loginEmail').value.trim(), password=$('#loginPassword').value;
  $('#loginStatus').textContent='Anmeldung läuft …';
  const {error}=await supa.auth.signInWithPassword({email,password});
  $('#loginStatus').textContent=error?'Anmeldung fehlgeschlagen: '+error.message:'';
  if(!error) showAuthState();
};
$('#signupBtn').onclick=async()=>{
  const email=$('#loginEmail').value.trim(), password=$('#loginPassword').value;
  if(password.length<6){$('#loginStatus').textContent='Passwort muss mindestens 6 Zeichen haben.';return}
  $('#loginStatus').textContent='Konto wird angelegt …';
  const {error}=await supa.auth.signUp({email,password});
  $('#loginStatus').textContent=error?'Konto konnte nicht angelegt werden: '+error.message:'Konto angelegt. Falls nötig, bestätige die E-Mail.';
};
$('#logoutBtn').onclick=async()=>{await supa.auth.signOut();showAuthState()};
supa.auth.onAuthStateChange(()=>showAuthState());
showAuthState();
