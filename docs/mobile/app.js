const SUPABASE_URL='https://cdhfmhxhhtqqoetlferj.supabase.co';
const SUPABASE_KEY='sb_publishable_r9xkC56K3zezl30297f1qQ_fsz6ztfl';
const supa=window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY);
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
let teamId='',currentUser=null,currentRole='user';
let cloud={tracks:[],vehicles:[],drivers:[],events:[],sessions:[],sets:[],measurements:[]};
let recoveryMode=false;
const startedAt=Date.now();

function esc(v=''){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function delay(ms){return new Promise(r=>setTimeout(r,ms))}
function go(name){
  $$('.view').forEach(v=>v.classList.toggle('active',v.dataset.view===name));
  $$('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  if(name==='measure')populateMeasure();
  if(name==='setup')populateSetup();
  window.scrollTo({top:0,behavior:'smooth'});
}
$$('[data-tab]').forEach(b=>b.onclick=()=>go(b.dataset.tab));
$$('[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go));

function vehicleName(id){const v=cloud.vehicles.find(x=>x.id===id);return v?.name||[v?.manufacturer,v?.model].filter(Boolean).join(' ')||'Fahrzeug'}
function driverName(id){const d=cloud.drivers.find(x=>x.id===id);return d?.name||[d?.first_name,d?.last_name].filter(Boolean).join(' ')||'Ohne Fahrer'}
function eventName(id){return cloud.events.find(x=>x.id===id)?.name||'Rennwochenende'}
function setName(id){const s=cloud.sets.find(x=>x.id===id);return s?'Reifensatz '+s.set_number+(s.compound?' · '+s.compound:''):'Reifensatz'}
function sessionName(s){return s?[s.session_type||'Session',driverName(s.driver_id),vehicleName(s.vehicle_id)].join(' · '):'Session'}

function groupedMeasurements(){
  const groups=new Map();
  for(const m of cloud.measurements){
    const key=(m.session_id||'')+'|'+(m.tyre_set_id||'');
    if(!groups.has(key))groups.set(key,{session_id:m.session_id,tyre_set_id:m.tyre_set_id,created_at:m.created_at,updated_at:m.updated_at,rows:{}});
    const g=groups.get(key);g.rows[m.position]=m;
    const t=m.updated_at||m.created_at;if(t&&(!g.updated_at||new Date(t)>new Date(g.updated_at)))g.updated_at=t;
  }
  return [...groups.values()].sort((a,b)=>new Date(b.updated_at||b.created_at||0)-new Date(a.updated_at||a.created_at||0));
}
function groupHtml(g){
  const session=cloud.sessions.find(s=>s.id===g.session_id),p={vl:'–',vr:'–',hl:'–',hr:'–'};
  Object.keys(p).forEach(pos=>{const r=g.rows[pos];if(r)p[pos]=r.measured_hot_pressure??r.measured_cold_pressure??'–'});
  const when=g.updated_at||g.created_at;
  return '<div class="entry"><div class="entry-top"><div class="entry-title">'+esc(vehicleName(session?.vehicle_id))+'</div><div class="entry-time">'+(when?new Date(when).toLocaleString('de-DE',{dateStyle:'short',timeStyle:'short'}):'')+'</div></div><div class="entry-meta">'+esc(eventName(session?.race_weekend_id))+' · '+esc(sessionName(session))+' · '+esc(setName(g.tyre_set_id))+'</div><div class="pressures"><div class="pbox"><span>VL</span><b>'+p.vl+'</b></div><div class="pbox"><span>VR</span><b>'+p.vr+'</b></div><div class="pbox"><span>HL</span><b>'+p.hl+'</b></div><div class="pbox"><span>HR</span><b>'+p.hr+'</b></div></div></div>';
}
function render(){
  const groups=groupedMeasurements();
  $('#statEntries').textContent=groups.length;$('#statCars').textContent=cloud.vehicles.length;$('#statDrivers').textContent=cloud.drivers.length;
  $('#lastEntry').className=groups.length?'':'empty-card';$('#lastEntry').innerHTML=groups.length?groupHtml(groups[0]):'Noch keine Messung vorhanden.';
  $('#allList').className='list'+(groups.length?'':' empty');$('#allList').innerHTML=groups.length?groups.map(groupHtml).join(''):'Noch keine Messungen vorhanden.';
  $('#cloudInfo').textContent=teamId?'Verbunden · Teamdaten aktuell':'Keine Team-Zuordnung gefunden.';
}
async function loadCloud(){
  if(!teamId)return;
  $('#cloudInfo').textContent='Synchronisierung läuft …';
  const [tr,v,d,e,s,t,m]=await Promise.all([
    supa.from('tracks').select('*').eq('team_id',teamId).order('name'),
    supa.from('vehicles').select('*').eq('team_id',teamId).order('name'),
    supa.from('drivers').select('*').eq('team_id',teamId).order('name'),
    supa.from('race_weekends').select('*').eq('team_id',teamId).order('start_date',{ascending:false}),
    supa.from('sessions').select('*').eq('team_id',teamId).order('measured_at',{ascending:false}),
    supa.from('tyre_sets').select('*').eq('team_id',teamId).order('set_number'),
    supa.from('tyre_measurements').select('*').eq('team_id',teamId).order('updated_at',{ascending:false})
  ]);
  const err=[tr,v,d,e,s,t,m].find(x=>x.error)?.error;
  if(err){$('#cloudInfo').textContent='Cloud-Fehler: '+err.message;return}
  cloud={tracks:tr.data||[],vehicles:v.data||[],drivers:d.data||[],events:e.data||[],sessions:s.data||[],sets:t.data||[],measurements:m.data||[]};
  render();
  if($('.view[data-view="setup"]')?.classList.contains('active'))populateSetup();
}
async function initAccount(session,reveal=true){
  currentUser=session?.user||null;
  if(!currentUser){
    teamId='';currentRole='user';
    if(reveal){$('#loginScreen').classList.remove('hidden');$('#app').classList.add('hidden');}
    return;
  }
  const {data,error}=await supa.from('team_members').select('team_id,role').eq('user_id',currentUser.id).limit(1);
  if(error||!data?.length){
    $('#loginStatus').textContent='Dieses Konto ist noch keinem SORG-Team zugeordnet.';
    if(reveal){$('#loginScreen').classList.remove('hidden');$('#app').classList.add('hidden');}
    return;
  }
  teamId=data[0].team_id;currentRole=data[0].role||'user';
  $('#adminUsersCard').classList.toggle('hidden',currentRole!=='admin');
  $('#adminLiveMenu').classList.toggle('hidden',currentRole!=='admin');
  if(reveal){$('#loginScreen').classList.add('hidden');$('#recoveryScreen').classList.add('hidden');$('#app').classList.remove('hidden');}
  await loadCloud();
}
async function finishSplash(){
  const remain=Math.max(0,2200-(Date.now()-startedAt));await delay(remain);
  $('#splashScreen').classList.add('splash-out');await delay(350);$('#splashScreen').classList.add('hidden');
  if(recoveryMode){$('#recoveryScreen').classList.remove('hidden');return}
  const {data}=await supa.auth.getSession();
  if(data.session)await initAccount(data.session,true);else{$('#loginScreen').classList.remove('hidden');$('#app').classList.add('hidden');}
}

$('#loginBtn').onclick=async()=>{
  const username=$('#loginUsername').value.trim(),password=$('#loginPassword').value;
  if(!username||!password){$('#loginStatus').textContent='Bitte Benutzername und Passwort eingeben.';return}
  $('#loginBtn').disabled=true;$('#loginStatus').textContent='Anmeldung läuft …';
  try{
    const response=await fetch(SUPABASE_URL+'/functions/v1/auth-login',{method:'POST',headers:{'Content-Type':'application/json','apikey':SUPABASE_KEY},body:JSON.stringify({username,password})});
    const data=await response.json();if(!response.ok)throw new Error(data.error||'Anmeldung fehlgeschlagen');
    const result=await supa.auth.setSession({access_token:data.access_token,refresh_token:data.refresh_token});if(result.error)throw result.error;
    localStorage.setItem('sorg_remember_login',$('#rememberLogin').checked?'1':'0');
    localStorage.setItem('sorg_username',username);
    $('#loginStatus').textContent='';await initAccount(result.data.session,true);
  }catch(error){$('#loginStatus').textContent='Anmeldung fehlgeschlagen: '+error.message}
  finally{$('#loginBtn').disabled=false}
};
$('#loginPassword').addEventListener('keydown',e=>{if(e.key==='Enter')$('#loginBtn').click()});
$('#forgotBtn').onclick=async()=>{
  const username=$('#loginUsername').value.trim();if(!username){$('#loginStatus').textContent='Bitte zuerst deinen Benutzernamen eingeben.';return}
  $('#loginStatus').textContent='Wiederherstellung wird geprüft …';
  try{
    const response=await fetch(SUPABASE_URL+'/functions/v1/auth-recover',{method:'POST',headers:{'Content-Type':'application/json','apikey':SUPABASE_KEY},body:JSON.stringify({username,redirect_to:location.origin+location.pathname})});
    const data=await response.json();if(!response.ok)throw new Error(data.error||'Passwort-Reset nicht möglich');
    $('#loginStatus').textContent='Falls möglich, wurde eine Reset-Nachricht versendet. Sonst kann ein Admin dein Passwort direkt ändern.';
  }catch(error){$('#loginStatus').textContent='Passwort-Reset nicht möglich: '+error.message}
};
$('#savePasswordBtn').onclick=async()=>{
  const p1=$('#newPassword').value,p2=$('#newPassword2').value;
  if(p1.length<6){$('#recoveryStatus').textContent='Passwort muss mindestens 6 Zeichen haben.';return}
  if(p1!==p2){$('#recoveryStatus').textContent='Die Passwörter stimmen nicht überein.';return}
  const {error}=await supa.auth.updateUser({password:p1});if(error){$('#recoveryStatus').textContent='Passwort konnte nicht geändert werden: '+error.message;return}
  $('#recoveryStatus').textContent='Passwort wurde geändert.';setTimeout(async()=>{const {data}=await supa.auth.getSession();await initAccount(data.session,true)},500);
};
async function logout(){
  localStorage.setItem('sorg_remember_login','0');
  await supa.auth.signOut();teamId='';currentRole='user';currentUser=null;
  $('#app').classList.add('hidden');$('#loginScreen').classList.remove('hidden');$('#loginPassword').value='';
}
$('#logoutBtn').onclick=logout;$('#logoutFullBtn').onclick=logout;$('#reloadBtn').onclick=loadCloud;

function populateMeasure(){
  const ev=$('#eventSelect'),current=ev.value;
  ev.innerHTML=cloud.events.length?cloud.events.map(x=>'<option value="'+x.id+'">'+esc(x.name)+'</option>').join(''):'<option value="">Noch kein Rennwochenende vorhanden</option>';
  if(current&&cloud.events.some(x=>x.id===current))ev.value=current;populateSessions();
}
function populateSessions(){
  const eventId=$('#eventSelect').value,list=cloud.sessions.filter(x=>x.race_weekend_id===eventId),el=$('#sessionSelect'),current=el.value;
  el.innerHTML=list.length?list.map(x=>'<option value="'+x.id+'">'+esc(sessionName(x))+'</option>').join(''):'<option value="">Noch keine Session vorhanden</option>';
  if(current&&list.some(x=>x.id===current))el.value=current;populateSets();
}
function populateSets(){
  const session=cloud.sessions.find(x=>x.id===$('#sessionSelect').value);
  const list=cloud.sets.filter(x=>session&&x.race_weekend_id===session.race_weekend_id&&(!x.vehicle_id||x.vehicle_id===session.vehicle_id)),el=$('#tyreSetSelect'),current=el.value;
  el.innerHTML=list.length?list.map(x=>'<option value="'+x.id+'">'+esc(setName(x.id))+'</option>').join(''):'<option value="">Noch kein Reifensatz vorhanden</option>';
  if(current&&list.some(x=>x.id===current))el.value=current;fillExisting();
}
function fillExisting(){
  const session=cloud.sessions.find(x=>x.id===$('#sessionSelect').value),setId=$('#tyreSetSelect').value;
  $('#sessionSummary').textContent=session?[eventName(session.race_weekend_id),vehicleName(session.vehicle_id),driverName(session.driver_id)].join(' · '):'Bitte Event, Session und Reifensatz auswählen.';
  const ids={vl:'#fl',vr:'#fr',hl:'#rl',hr:'#rr'};Object.values(ids).forEach(id=>$(id).value='');
  Object.entries(ids).forEach(([pos,id])=>{const r=cloud.measurements.find(x=>x.session_id===session?.id&&x.tyre_set_id===setId&&x.position===pos);if(r)$(id).value=r.measured_hot_pressure??''});
}
$('#eventSelect').onchange=populateSessions;$('#sessionSelect').onchange=populateSets;$('#tyreSetSelect').onchange=fillExisting;
$('#pressureForm').onsubmit=async e=>{
  e.preventDefault();const sessionId=$('#sessionSelect').value,setId=$('#tyreSetSelect').value;
  if(!teamId||!sessionId||!setId){$('#saveStatus').textContent='Bitte zuerst Rennwochenende, Session und Reifensatz auswählen.';return}
  const vals={vl:$('#fl').value,vr:$('#fr').value,hl:$('#rl').value,hr:$('#rr').value},note=$('#note').value.trim();$('#saveStatus').textContent='Wird gespeichert …';
  for(const [position,value] of Object.entries(vals)){
    const existing=cloud.measurements.find(x=>x.session_id===sessionId&&x.tyre_set_id===setId&&x.position===position);
    const payload={team_id:teamId,session_id:sessionId,tyre_set_id:setId,position,measured_hot_pressure:Number(value),notes:note||existing?.notes||null,updated_at:new Date().toISOString()};
    const result=existing?await supa.from('tyre_measurements').update(payload).eq('id',existing.id):await supa.from('tyre_measurements').insert(payload);
    if(result.error){$('#saveStatus').textContent='Speichern fehlgeschlagen: '+result.error.message;return}
  }
  $('#note').value='';$('#saveStatus').textContent='Gespeichert.';await loadCloud();go('home');
};


function options(rows,label,empty='Noch keine Daten'){
  return rows.length?rows.map(x=>'<option value="'+x.id+'">'+esc(label(x))+'</option>').join(''):'<option value="">'+empty+'</option>';
}
function populateSetup(){
  if(currentRole!=='admin')return;
  const set=(id,html)=>{const el=$(id);if(el)el.innerHTML=html};
  set('#setupEventTrack',options(cloud.tracks,x=>x.name,'Noch keine Strecke'));
  set('#setupSessionEvent',options(cloud.events,x=>x.name,'Noch kein Rennwochenende'));
  set('#setupSessionCar',options(cloud.vehicles,x=>vehicleName(x.id),'Noch kein Fahrzeug'));
  set('#setupSessionDriver','<option value="">Ohne Fahrer</option>'+options(cloud.drivers,x=>driverName(x.id),'').replace('<option value=""></option>',''));
  set('#setupTyreSession',options(cloud.sessions,x=>eventName(x.race_weekend_id)+' · '+sessionName(x),'Noch keine Session'));
}
function setupStatus(msg,ok=false){
  const el=$('#setupStatus');if(!el)return;el.textContent=msg;el.style.color=ok?'#8ee3b4':'';
}
async function insertShared(table,payload){
  const result=await supa.from(table).insert({...payload,team_id:teamId});
  if(result.error)throw result.error;
}
$('#createTrackBtn').onclick=async()=>{
  const name=$('#setupTrackName').value.trim();
  if(!name){setupStatus('Bitte einen Streckennamen eingeben.');return}
  try{
    setupStatus('Strecke wird gespeichert …');
    await insertShared('tracks',{id:crypto.randomUUID(),name,country:$('#setupTrackCountry').value.trim(),length_km:Number($('#setupTrackLength').value||0),corners:Number($('#setupTrackCorners').value||0)});
    await loadCloud();setupStatus('Strecke gespeichert. Sie steht jetzt PC und Handy zur Verfügung.',true);
  }catch(e){setupStatus('Strecke konnte nicht gespeichert werden: '+e.message)}
};
$('#createCarBtn').onclick=async()=>{
  const manufacturer=$('#setupCarManufacturer').value.trim(),model=$('#setupCarModel').value.trim();
  if(!manufacturer&&!model){setupStatus('Bitte Hersteller oder Modell eingeben.');return}
  try{
    setupStatus('Fahrzeug wird gespeichert …');
    await insertShared('vehicles',{id:crypto.randomUUID(),name:[manufacturer,model].filter(Boolean).join(' '),manufacturer,model,start_number:$('#setupCarNumber').value.trim(),vehicle_class:$('#setupCarClass').value.trim()});
    await loadCloud();setupStatus('Fahrzeug gespeichert.',true);
  }catch(e){setupStatus('Fahrzeug konnte nicht gespeichert werden: '+e.message)}
};
$('#createDriverBtn').onclick=async()=>{
  const first_name=$('#setupDriverFirst').value.trim(),last_name=$('#setupDriverLast').value.trim();
  if(!first_name&&!last_name){setupStatus('Bitte einen Fahrernamen eingeben.');return}
  try{
    setupStatus('Fahrer wird gespeichert …');
    await insertShared('drivers',{id:crypto.randomUUID(),name:[first_name,last_name].filter(Boolean).join(' '),first_name,last_name,race_number:$('#setupDriverNumber').value.trim(),number:$('#setupDriverNumber').value.trim(),licence_class:$('#setupDriverLicence').value.trim()});
    await loadCloud();setupStatus('Fahrer gespeichert.',true);
  }catch(e){setupStatus('Fahrer konnte nicht gespeichert werden: '+e.message)}
};
$('#createEventBtn').onclick=async()=>{
  const name=$('#setupEventName').value.trim(),track_id=$('#setupEventTrack').value;
  if(!name||!track_id){setupStatus('Rennwochenende und Strecke sind erforderlich.');return}
  try{
    setupStatus('Rennwochenende wird gespeichert …');
    await insertShared('race_weekends',{id:crypto.randomUUID(),name,track_id,start_date:$('#setupEventStart').value||null,end_date:$('#setupEventEnd').value||null,championship:$('#setupEventChampionship').value.trim(),event_type:$('#setupEventType').value.trim()});
    await loadCloud();setupStatus('Rennwochenende gespeichert.',true);
  }catch(e){setupStatus('Rennwochenende konnte nicht gespeichert werden: '+e.message)}
};
$('#createSessionBtn').onclick=async()=>{
  const race_weekend_id=$('#setupSessionEvent').value,vehicle_id=$('#setupSessionCar').value;
  if(!race_weekend_id||!vehicle_id){setupStatus('Rennwochenende und Fahrzeug sind erforderlich.');return}
  const rawDate=$('#setupSessionDate').value;
  const measured_at=rawDate?new Date(rawDate).toISOString():new Date().toISOString();
  try{
    setupStatus('Session wird gespeichert …');
    await insertShared('sessions',{id:crypto.randomUUID(),race_weekend_id,vehicle_id,driver_id:$('#setupSessionDriver').value||null,session_type:$('#setupSessionType').value.trim()||'Session',measured_at,session_date:measured_at});
    await loadCloud();setupStatus('Session gespeichert.',true);
  }catch(e){setupStatus('Session konnte nicht gespeichert werden: '+e.message)}
};
$('#createTyreSetBtn').onclick=async()=>{
  const session=cloud.sessions.find(x=>x.id===$('#setupTyreSession').value);
  if(!session){setupStatus('Bitte zuerst eine Session auswählen.');return}
  const id=crypto.randomUUID();
  try{
    setupStatus('Reifensatz wird gespeichert …');
    await insertShared('tyre_sets',{id,race_weekend_id:session.race_weekend_id,vehicle_id:session.vehicle_id,set_number:Number($('#setupTyreNumber').value||1),compound:$('#setupTyreCompound').value.trim()||'Unbekannt',condition:'gebraucht',tyre_type:'Slick',laps:0,heat_cycles:0});
    const patch=await supa.from('sessions').update({tyre_set_id:id,updated_at:new Date().toISOString()}).eq('id',session.id);
    if(patch.error)throw patch.error;
    await loadCloud();setupStatus('Reifensatz gespeichert und der Session zugeordnet.',true);
  }catch(e){setupStatus('Reifensatz konnte nicht gespeichert werden: '+e.message)}
};

async function adminCall(payload){const {data,error}=await supa.functions.invoke('admin-users',{body:payload});if(error)throw new Error(error.message||'Admin-Funktion fehlgeschlagen');if(data?.error)throw new Error(data.error);return data||{}}
async function loadAdminUsers(){
  $('#adminStatus').textContent='Benutzer werden geladen …';
  try{
    const data=await adminCall({action:'list'}),users=data.users||[];
    $('#adminUserList').innerHTML=users.map(u=>{
      const full=[u.first_name,u.last_name].filter(Boolean).join(' ')||u.display_name||u.username;
      return '<div class="user-admin-row" data-id="'+u.id+'"><div class="user-admin-head"><div><b>'+esc(full)+'</b><span>@'+esc(u.username)+' · '+esc(u.team_role||'Mechaniker')+'</span><span>'+esc(u.phone||'Keine Telefonnummer')+' · '+esc(u.residence||'Kein Wohnort')+'</span></div><span class="user-state '+(u.inactive?'off':'')+'">'+(u.inactive?'INAKTIV':'AKTIV')+'</span></div><div class="user-admin-actions"><select class="teamRoleSelect"><option '+(u.team_role==='Reifen'?'selected':'')+'>Reifen</option><option '+(u.team_role==='Mechaniker'?'selected':'')+'>Mechaniker</option><option '+(u.team_role==='Car Chief'?'selected':'')+'>Car Chief</option><option '+(u.team_role==='Fahrer'?'selected':'')+'>Fahrer</option></select><select class="permissionSelect"><option value="user" '+(u.permission==='user'?'selected':'')+'>Benutzer</option><option value="admin" '+(u.permission==='admin'?'selected':'')+'>Admin</option></select><button class="ghost compact profileBtn">Daten bearbeiten</button><button class="ghost compact permBtn">Berechtigung speichern</button><button class="ghost compact pwBtn">Passwort setzen</button><button class="ghost compact activeBtn">'+(u.inactive?'Aktivieren':'Deaktivieren')+'</button></div></div>';
    }).join('')||'<div class="empty">Noch keine Benutzer.</div>';
    $$('.user-admin-row').forEach(row=>{
      const id=row.dataset.id,user=users.find(u=>u.id===id);
      row.querySelector('.profileBtn').onclick=async()=>{
        const first_name=prompt('Vorname:',user.first_name||'');if(first_name===null)return;
        const last_name=prompt('Nachname:',user.last_name||'');if(last_name===null)return;
        const username=prompt('Benutzername:',user.username||'');if(username===null)return;
        const phone=prompt('Telefonnummer:',user.phone||'');if(phone===null)return;
        const residence=prompt('Wohnort:',user.residence||'');if(residence===null)return;
        try{await adminCall({action:'update_profile',user_id:id,first_name,last_name,username,phone,residence,team_role:row.querySelector('.teamRoleSelect').value});await loadAdminUsers()}catch(e){$('#adminStatus').textContent=e.message}
      };
      row.querySelector('.permBtn').onclick=async()=>{try{await adminCall({action:'set_role',user_id:id,role:row.querySelector('.permissionSelect').value});await loadAdminUsers()}catch(e){$('#adminStatus').textContent=e.message}};
      row.querySelector('.pwBtn').onclick=async()=>{const pw=prompt('Neues Passwort eingeben:');if(pw===null)return;try{await adminCall({action:'set_password',user_id:id,password:pw});$('#adminStatus').textContent='Passwort wurde geändert.'}catch(e){$('#adminStatus').textContent=e.message}};
      row.querySelector('.activeBtn').onclick=async()=>{const inactive=row.querySelector('.user-state').classList.contains('off');try{await adminCall({action:'set_active',user_id:id,active:inactive});await loadAdminUsers()}catch(e){$('#adminStatus').textContent=e.message}};
    });
    $('#adminStatus').textContent=users.length+' Benutzer';
  }catch(e){$('#adminStatus').textContent=e.message}
}
$('#loadUsersBtn').onclick=async()=>{$('#userAdminPanel').classList.remove('hidden');await loadAdminUsers()};
$('#createUserBtn').onclick=async()=>{
  const payload={action:'create',first_name:$('#adminFirstName').value.trim(),last_name:$('#adminLastName').value.trim(),username:$('#adminUsername').value.trim(),phone:$('#adminPhone').value.trim(),residence:$('#adminResidence').value.trim(),team_role:$('#adminTeamRole').value,permission:$('#adminPermission').value,password:$('#adminPassword').value};
  try{await adminCall(payload);['#adminFirstName','#adminLastName','#adminUsername','#adminPhone','#adminResidence','#adminPassword'].forEach(id=>$(id).value='');$('#adminStatus').textContent='Benutzer wurde angelegt.';await loadAdminUsers()}catch(e){$('#adminStatus').textContent=e.message}
};

let deferredPrompt=null;
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;$('#installBtn').classList.remove('hidden')});
$('#installBtn').onclick=async()=>{if(!deferredPrompt)return;deferredPrompt.prompt();await deferredPrompt.userChoice;deferredPrompt=null;$('#installBtn').classList.add('hidden')};
if('serviceWorker' in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js'));

supa.auth.onAuthStateChange(async(event,session)=>{
  if(event==='PASSWORD_RECOVERY'){recoveryMode=true;$('#loginScreen').classList.add('hidden');$('#app').classList.add('hidden');if($('#splashScreen').classList.contains('hidden'))$('#recoveryScreen').classList.remove('hidden');return}
  if($('#splashScreen').classList.contains('hidden'))await initAccount(session,true);
});

(async()=>{
  $('#rememberLogin').checked=localStorage.getItem('sorg_remember_login')!=='0';
  $('#loginUsername').value=localStorage.getItem('sorg_username')||'';
  let {data}=await supa.auth.getSession();
  if(data.session&&localStorage.getItem('sorg_remember_login')==='0'){await supa.auth.signOut();data={session:null}}
  if(data.session)await initAccount(data.session,false);
  await finishSplash();
})();