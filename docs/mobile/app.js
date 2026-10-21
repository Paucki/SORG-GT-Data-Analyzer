const SUPABASE_URL='https://cdhfmhxhhtqqoetlferj.supabase.co';
const SUPABASE_KEY='sb_publishable_r9xkC56K3zezl30297f1qQ_fsz6ztfl';
const supa=window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY);
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];

let teamId='';
let currentUser=null;
let cloud={vehicles:[],drivers:[],events:[],sessions:[],sets:[],measurements:[]};

function esc(v=''){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function go(name){
  $$('.view').forEach(v=>v.classList.toggle('active',v.dataset.view===name));
  $$('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  if(name==='measure') populateMeasure();
  window.scrollTo({top:0,behavior:'smooth'});
}
$$('[data-tab]').forEach(b=>b.onclick=()=>go(b.dataset.tab));
$$('[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go));

function vehicleName(id){
  const v=cloud.vehicles.find(x=>x.id===id);
  return v?.name || [v?.manufacturer,v?.model].filter(Boolean).join(' ') || 'Fahrzeug';
}
function driverName(id){
  const d=cloud.drivers.find(x=>x.id===id);
  return d?.name || [d?.first_name,d?.last_name].filter(Boolean).join(' ') || 'Ohne Fahrer';
}
function eventName(id){
  return cloud.events.find(x=>x.id===id)?.name || 'Rennwochenende';
}
function setName(id){
  const s=cloud.sets.find(x=>x.id===id);
  return s ? 'Reifensatz '+s.set_number+(s.compound?' · '+s.compound:'') : 'Reifensatz';
}
function sessionName(s){
  if(!s)return 'Session';
  return [s.session_type||'Session',driverName(s.driver_id),vehicleName(s.vehicle_id)].join(' · ');
}

function groupedMeasurements(){
  const groups=new Map();
  for(const m of cloud.measurements){
    const key=(m.session_id||'')+'|'+(m.tyre_set_id||'');
    if(!groups.has(key)) groups.set(key,{session_id:m.session_id,tyre_set_id:m.tyre_set_id,created_at:m.created_at,updated_at:m.updated_at,rows:{}});
    const g=groups.get(key);
    g.rows[m.position]=m;
    const t=m.updated_at||m.created_at;
    if(t && (!g.updated_at || new Date(t)>new Date(g.updated_at))) g.updated_at=t;
  }
  return [...groups.values()].sort((a,b)=>new Date(b.updated_at||b.created_at||0)-new Date(a.updated_at||a.created_at||0));
}

function groupHtml(g){
  const session=cloud.sessions.find(s=>s.id===g.session_id);
  const pressures={vl:'–',vr:'–',hl:'–',hr:'–'};
  for(const p of Object.keys(pressures)){
    const r=g.rows[p];
    if(r) pressures[p]=r.measured_hot_pressure ?? r.measured_cold_pressure ?? '–';
  }
  const when=g.updated_at||g.created_at;
  return `<div class="entry">
    <div class="entry-top">
      <div class="entry-title">${esc(vehicleName(session?.vehicle_id))}</div>
      <div class="entry-time">${when?new Date(when).toLocaleString('de-DE',{dateStyle:'short',timeStyle:'short'}):''}</div>
    </div>
    <div class="entry-meta">${esc(eventName(session?.race_weekend_id))} · ${esc(sessionName(session))} · ${esc(setName(g.tyre_set_id))}</div>
    <div class="pressures">
      <div class="pbox"><span>VL</span><b>${pressures.vl}</b></div>
      <div class="pbox"><span>VR</span><b>${pressures.vr}</b></div>
      <div class="pbox"><span>HL</span><b>${pressures.hl}</b></div>
      <div class="pbox"><span>HR</span><b>${pressures.hr}</b></div>
    </div>
  </div>`;
}

function render(){
  const groups=groupedMeasurements();
  $('#statEntries').textContent=groups.length;
  $('#statCars').textContent=cloud.vehicles.length;
  $('#statDrivers').textContent=cloud.drivers.length;
  $('#lastEntry').className=groups.length?'':'empty-card';
  $('#lastEntry').innerHTML=groups.length?groupHtml(groups[0]):'Noch keine Messung vorhanden.';
  $('#allList').className='list'+(groups.length?'':' empty');
  $('#allList').innerHTML=groups.length?groups.map(groupHtml).join(''):'Noch keine Messungen vorhanden.';
  $('#cloudInfo').textContent=teamId
    ? 'Verbunden · dieselben Daten wie am PC'
    : 'Keine Team-Zuordnung gefunden.';
}

async function loadCloud(){
  if(!teamId)return;
  $('#cloudInfo').textContent='Synchronisierung läuft …';
  const [v,d,e,s,t,m]=await Promise.all([
    supa.from('vehicles').select('*').eq('team_id',teamId).order('name'),
    supa.from('drivers').select('*').eq('team_id',teamId).order('name'),
    supa.from('race_weekends').select('*').eq('team_id',teamId).order('start_date',{ascending:false}),
    supa.from('sessions').select('*').eq('team_id',teamId).order('measured_at',{ascending:false}),
    supa.from('tyre_sets').select('*').eq('team_id',teamId).order('set_number'),
    supa.from('tyre_measurements').select('*').eq('team_id',teamId).order('updated_at',{ascending:false})
  ]);
  const error=[v,d,e,s,t,m].find(x=>x.error)?.error;
  if(error){
    $('#cloudInfo').textContent='Cloud-Fehler: '+error.message;
    return;
  }
  cloud={vehicles:v.data||[],drivers:d.data||[],events:e.data||[],sessions:s.data||[],sets:t.data||[],measurements:m.data||[]};
  render();
}

async function initAccount(session){
  currentUser=session?.user||null;
  if(!currentUser){
    teamId='';
    $('#loginScreen').classList.remove('hidden');
    $('#app').classList.add('hidden');
    return;
  }
  const {data,error}=await supa.from('team_members').select('team_id,role').eq('user_id',currentUser.id).limit(1);
  if(error || !data?.length){
    $('#loginStatus').textContent='Dieses Konto ist noch keinem SORG-Team zugeordnet.';
    $('#loginScreen').classList.remove('hidden');
    $('#app').classList.add('hidden');
    return;
  }
  teamId=data[0].team_id;
  $('#loginScreen').classList.add('hidden');
  $('#app').classList.remove('hidden');
  await loadCloud();
}

$('#loginBtn').onclick=async()=>{
  const email=$('#loginEmail').value.trim(), password=$('#loginPassword').value;
  if(!email||!password){$('#loginStatus').textContent='Bitte E-Mail und Passwort eingeben.';return}
  $('#loginBtn').disabled=true;
  $('#loginStatus').textContent='Anmeldung läuft …';
  const {data,error}=await supa.auth.signInWithPassword({email,password});
  $('#loginBtn').disabled=false;
  if(error){$('#loginStatus').textContent='Anmeldung fehlgeschlagen: '+error.message;return}
  $('#loginStatus').textContent='';
  await initAccount(data.session);
};
$('#loginPassword').addEventListener('keydown',e=>{if(e.key==='Enter')$('#loginBtn').click()});
$('#logoutBtn').onclick=async()=>{await supa.auth.signOut();teamId='';await initAccount(null)};
$('#reloadBtn').onclick=()=>loadCloud();

function populateMeasure(){
  const ev=$('#eventSelect');
  const current=ev.value;
  ev.innerHTML=cloud.events.length
    ? cloud.events.map(x=>`<option value="${x.id}">${esc(x.name)}</option>`).join('')
    : '<option value="">Noch kein Rennwochenende am PC angelegt</option>';
  if(current && cloud.events.some(x=>x.id===current))ev.value=current;
  populateSessions();
}
function populateSessions(){
  const eventId=$('#eventSelect').value;
  const list=cloud.sessions.filter(x=>x.race_weekend_id===eventId);
  const el=$('#sessionSelect'), current=el.value;
  el.innerHTML=list.length
    ? list.map(x=>`<option value="${x.id}">${esc(sessionName(x))}</option>`).join('')
    : '<option value="">Noch keine Session vorhanden</option>';
  if(current && list.some(x=>x.id===current))el.value=current;
  populateSets();
}
function populateSets(){
  const session=cloud.sessions.find(x=>x.id===$('#sessionSelect').value);
  const list=cloud.sets.filter(x=>{
    if(!session)return false;
    return x.race_weekend_id===session.race_weekend_id && (!x.vehicle_id || x.vehicle_id===session.vehicle_id);
  });
  const el=$('#tyreSetSelect'), current=el.value;
  el.innerHTML=list.length
    ? list.map(x=>`<option value="${x.id}">${esc(setName(x.id))}</option>`).join('')
    : '<option value="">Noch kein Reifensatz vorhanden</option>';
  if(current && list.some(x=>x.id===current))el.value=current;
  fillExisting();
}
function fillExisting(){
  const session=cloud.sessions.find(x=>x.id===$('#sessionSelect').value);
  const setId=$('#tyreSetSelect').value;
  $('#sessionSummary').textContent=session
    ? [eventName(session.race_weekend_id),vehicleName(session.vehicle_id),driverName(session.driver_id)].join(' · ')
    : 'Bitte Event, Session und Reifensatz am PC anlegen.';
  const ids={vl:'#fl',vr:'#fr',hl:'#rl',hr:'#rr'};
  Object.values(ids).forEach(id=>$(id).value='');
  for(const [pos,id] of Object.entries(ids)){
    const r=cloud.measurements.find(x=>x.session_id===session?.id && x.tyre_set_id===setId && x.position===pos);
    if(r)$(id).value=r.measured_hot_pressure ?? '';
  }
}
$('#eventSelect').onchange=populateSessions;
$('#sessionSelect').onchange=populateSets;
$('#tyreSetSelect').onchange=fillExisting;

$('#pressureForm').onsubmit=async e=>{
  e.preventDefault();
  const sessionId=$('#sessionSelect').value;
  const setId=$('#tyreSetSelect').value;
  if(!teamId||!sessionId||!setId){$('#saveStatus').textContent='Bitte zuerst Event, Session und Reifensatz auswählen.';return}
  const vals={vl:$('#fl').value,vr:$('#fr').value,hl:$('#rl').value,hr:$('#rr').value};
  const note=$('#note').value.trim();
  $('#saveStatus').textContent='Wird gespeichert …';
  for(const [position,value] of Object.entries(vals)){
    const pressure=Number(value);
    const existing=cloud.measurements.find(x=>x.session_id===sessionId && x.tyre_set_id===setId && x.position===position);
    const payload={
      team_id:teamId,
      session_id:sessionId,
      tyre_set_id:setId,
      position,
      measured_hot_pressure:pressure,
      notes:note||existing?.notes||null,
      updated_at:new Date().toISOString()
    };
    let result;
    if(existing){
      result=await supa.from('tyre_measurements').update(payload).eq('id',existing.id);
    }else{
      result=await supa.from('tyre_measurements').insert(payload);
    }
    if(result.error){$('#saveStatus').textContent='Speichern fehlgeschlagen: '+result.error.message;return}
  }
  $('#note').value='';
  $('#saveStatus').textContent='Gespeichert.';
  await loadCloud();
  go('home');
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
supa.auth.onAuthStateChange((_event,session)=>initAccount(session));
(async()=>{const {data}=await supa.auth.getSession();await initAccount(data.session)})();
