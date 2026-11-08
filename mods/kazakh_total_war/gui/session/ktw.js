/* SPDX-License-Identifier: GPL-2.0-or-later
 * UI-only presentation. Authoritative state and actions live in simulation.
 */
var g_KtwView=null, g_KtwSelected=null, g_KtwTick=0, g_KtwTransitioning=false, g_KtwFeedbackUntil=0, g_KtwBooted=false, g_KtwCameraSet=false;
var g_KtwRecruitTypes=["mounted_archer","light_cavalry","heavy_cavalry","spearman","infantry_archer"];
function ktwObject(name) { return Engine.GetGUIObjectByName(name); }
function ktwCaption(name,value) { ktwObject(name).caption=String(value); }
function ktwFeedback(value) { ktwCaption("ktwFeedback",value);g_KtwFeedbackUntil=Date.now()+6000; }
function ktwCommand(action,args) { Engine.PostNetworkCommand(Object.assign({type:"ktw",action:action},args || {})); }
function ktwSessionInit() {
 g_KtwBooted=true;
 var labels={ktwSave:"save",ktwMenu:"menu",ktwProvinceHeading:"provinces",ktwProvinceLabel:"selected",ktwMove:"move",ktwEconomyLabel:"supplies",ktwPasture:"pasture",ktwMarket:"market",ktwTruce:"truce",ktwRecruit:"recruit",ktwEndTurn:"endTurn",ktwFight:"fight",ktwAuto:"auto",ktwRetreat:"retreat",ktwPendingTitle:"pending",ktwSurrender:"surrender",ktwCampaignHint:"hint",ktwBattleHint:"battleHint",ktwCouncil:"council",ktwJournal:"journal",ktwSessionOptions:"settings",ktwDossierCouncil:"council",ktwDossierArchive:"archive",ktwDossierClose:"close",ktwCommanderFocus:"commander",ktwRecoveryTitle:"recoveryTitle",ktwRecoveryMessage:"recoveryMessage",ktwRecoveryLoad:"loadBackup",ktwRecoveryMenu:"menu"};
 for(var name in labels)ktwCaption(name,ktwText(labels[name]));
 ktwObject("ktwProvinceHeading").tooltip=ktwText("hint");
 var combo=ktwObject("ktwRecruitType");combo.list=g_KtwRecruitTypes.map(ktwUnit);combo.list_data=g_KtwRecruitTypes;combo.selected=0;
}
function ktwSessionTick() {
 if(Date.now()-g_KtwTick<250 || g_KtwTransitioning)return;
 g_KtwTick=Date.now();
 if(!g_KtwBooted)ktwSessionInit();
 var view=Engine.GuiInterfaceCall("KtwGetState");
 if(!view){ktwObject("ktwRoot").hidden=true;return;}
 ktwObject("ktwRoot").hidden=false;g_KtwView=view;
 var recovery=String(view.error || "").indexOf("KTW_LOAD_RECOVERY_REQUIRED")===0;
 ktwObject("ktwRecovery").hidden=!recovery;
 ktwObject("ktwSave").enabled=!recovery;
 if(recovery) {
  ["ktwCampaignPanels","ktwBattlePanel","ktwPending","ktwDossier","topPanel","selectionDetails","unitCommands","supplementalSelectionDetails"].forEach(n=>{ktwObject(n).hidden=true;});
  ktwCaption("ktwHeading",ktwText("recoveryTitle"));ktwCaption("ktwClock","");ktwCaption("ktwFeedback","");
  return;
 }
 if(!view.state){ktwObject("ktwRoot").hidden=true;return;}
 ktwAutosave(view);
 ktwRenderDossier();
 if(view.transition){
  g_KtwTransitioning=true;
  // The native checkpoint includes pending battle and all live simulation entities.
  Engine.SaveGame("ktw_transition", "KTW transition · "+view.state.turn, getSavedGameData());
  ktwLaunch(view.transition,view.state,true);return;
 }
 var s=view.state, campaign=view.mode==="campaign", army=s.armies.find(a=>a.id==="kazakh_main");
 if(!g_KtwCameraSet){
  g_KtwCameraSet=true;
  if(campaign){Engine.SetCameraData(512,500,880,1.05,Math.PI,550);Engine.CameraMoveTo(512,512);}
  else {Engine.SetCameraData(512,200,230,0.65,0,280);Engine.CameraMoveTo(512,500);}
 }
 ktwObject("ktwCampaignPanels").hidden=!campaign;ktwObject("ktwBattlePanel").hidden=campaign;
 ktwObject("topPanel").hidden=campaign;
 ["selectionDetails","unitCommands","supplementalSelectionDetails"].forEach(n=>{if(campaign)ktwObject(n).hidden=true;});
 ktwCaption("ktwHeading",ktwText(campaign?"campaign":"battle"));
 ktwCaption("ktwClock",s.year+" · "+ktwText(s.season)+" · "+ktwText("turn")+" "+s.turn);
 ktwObject("ktwPending").hidden=!campaign || !s.pendingBattle;
 if(view.error)ktwFeedback(ktwErrorText(view.error));
 else if(g_KtwFeedbackUntil<Date.now())ktwCaption("ktwFeedback",s.status==="playing"?"":ktwText(s.status));
 if(!campaign){
  var stats=view.battleStats || {};
  var a=stats.kazakh===undefined?"":stats.kazakh;
  var b=stats.abulkhair===undefined?"":stats.abulkhair;
  var friend=(stats.regiments || []).filter(r=>r.faction==="kazakh"&&r.remaining>0);
  var morale=friend.length?Math.round(friend.reduce((n,r)=>n+r.morale,0)/friend.length):0;
  var fatigue=friend.length?Math.round(friend.reduce((n,r)=>n+r.fatigue,0)/friend.length):0;
  ktwCaption("ktwBattleStats",a!==""?ktwText("kazakh")+": "+a+"   ·   "+ktwText("abulkhair")+": "+b+"\n"+ktwText("morale")+": "+morale+"   ·   "+ktwText("fatigue")+": "+fatigue:"");
  var commander=(view.commanders || []).find(c=>c.armyId==="kazakh_main");
  ktwCaption("ktwCommanderFocus",commander?ktwCharacterName(s,commander.characterId)+(commander.alive?"":" · "+ktwText("dead")):ktwText("noCommander"));
  ktwObject("ktwCommanderFocus").enabled=!!commander && commander.alive;
  return;
 }
 if(!g_KtwSelected || !s.provinces.some(p=>p.id===g_KtwSelected))g_KtwSelected=s.selectedProvince || army.province;
 // Selecting an actual 3D settlement also selects the corresponding province.
 if(view.markers && typeof g_Selection!=="undefined"){
  var selected=g_Selection.toList();
  var marker=Array.isArray(view.markers)?view.markers.find(m=>selected.includes(m.entity || m.entityId)):null;
  if(marker && marker.provinceId)g_KtwSelected=marker.provinceId;
 }
 var province=s.provinces.find(p=>p.id===g_KtwSelected), current=s.provinces.find(p=>p.id===army.province);
 s.provinces.forEach(function(p,i){
  var btn=ktwObject("ktwProvince"+i);
  btn.caption=(p.id===army.province?"◆ ":p.owner==="kazakh"?"• ":"  ")+ktwLocal(p.name);
  btn.textcolor=p.id===g_KtwSelected?"255 215 135":p.owner==="kazakh"?"161 218 221":"216 191 164";
 });
 ktwCaption("ktwSelectedTitle",ktwLocal(province.name));
 ktwCaption("ktwProvinceInfo",ktwText("owner")+": "+ktwText(province.owner)+"\n\n"+ktwText("routes")+":\n"+province.adjacent.map(id=>ktwLocal(s.provinces.find(p=>p.id===id).name)).join(", "));
 var ready=s.status==="playing"&&!s.pendingBattle;
 ktwObject("ktwMove").enabled=ready&&army.movement>0&&current.adjacent.includes(province.id);
 ktwObject("ktwEndTurn").enabled=ready;
 ktwObject("ktwRecruit").enabled=ready&&current.owner==="kazakh";
 ktwObject("ktwPasture").enabled=ready&&province.owner==="kazakh"&&province.buildings.pasture<3;
 ktwCaption("ktwPasture",ktwText("pasture").split(" · ")[0]+" · "+(160*(province.buildings.pasture+1)));
 ktwObject("ktwMarket").enabled=ready&&province.owner==="kazakh"&&province.buildings.market<3;
 ktwCaption("ktwMarket",ktwText("market").split(" · ")[0]+" · "+(200*(province.buildings.market+1)));
 var recruitType=ktwObject("ktwRecruitType").list_data[ktwObject("ktwRecruitType").selected];
 ktwCaption("ktwRecruit",ktwText("recruit")+" · "+ktwData().unitCosts[recruitType]);
 ktwObject("ktwTruce").enabled=ready&&s.relation==="war";
 ktwCaption("ktwArmyTitle",ktwText("commander")+": "+(army.commander?ktwCharacterName(s,army.commander):ktwText("noCommander"))+" · "+army.regiments.reduce((n,r)=>n+r.count,0)+" "+ktwText("soldiers"));
 ktwCaption("ktwResources",ktwText("silver")+": "+s.treasury.kazakh.silver+"   ·   "+ktwText("food")+": "+s.treasury.kazakh.food);
 ktwCaption("ktwRoster",army.regiments.filter(r=>r.count>0).map(r=>ktwUnit(r.type)+"  "+r.count+"  ("+Math.round(r.morale)+")").join("   |   "));
 ktwCaption("ktwArmyHint",ktwText("movement")+": "+army.movement+"   ·   "+ktwText(s.relation));
 if(s.pendingBattle){var p=s.provinces.find(p=>p.id===s.pendingBattle.provinceId);ktwCaption("ktwPendingInfo",ktwLocal(p.name)+"\n"+s.pendingBattle.armies.map(a=>ktwText(a.faction)+": "+a.regiments.reduce((n,r)=>n+r.count,0)+" "+ktwText("soldiers")).join("\n"));}
}
function ktwSelectProvince(index) {
 if(!g_KtwView)return;
 var p=g_KtwView.state.provinces[index];g_KtwSelected=p.id;
 // Position conversion matches the campaign generator's 1024-world-unit scene.
 Engine.CameraMoveTo(1024*(0.12+0.76*p.mapPosition.x),1024*(0.12+0.76*p.mapPosition.z));
 g_KtwTick=0;
}
function ktwOrderMove(){ktwCommand("move",{armyId:"kazakh_main",provinceId:g_KtwSelected});}
function ktwOrderBuild(kind){ktwCommand("build",{provinceId:g_KtwSelected,kind:kind});}
function ktwRecruit(){var combo=ktwObject("ktwRecruitType");ktwCommand("recruit",{armyId:"kazakh_main",unitType:combo.list_data[combo.selected],count:20});}
function ktwErrorText(code){
 var value=String(code);
 if(/MOVEMENT|ALREADY_MOVED/.test(value))return ktwText("noMove");
 if(/ADJACENT/.test(value))return ktwText("notAdjacent");
 if(/RESOURCES/.test(value))return ktwText("funds");
 if(/BATTLE_PENDING/.test(value))return ktwText("pendingError");
 return ktwText("error")+": "+value;
}
function ktwSaveGame(){
 var description="KTW "+(g_KtwView?g_KtwView.mode+" · "+g_KtwView.state.turn:"")+" · "+Date.now();
 Engine.SaveGame("ktw_quicksave",description,getSavedGameData());
 var ok=Engine.GetSavedGames().some(g=>g.id==="ktw_quicksave"&&g.metadata.description===description);
 ktwFeedback(ktwText(ok?"saved":"saveFailed"));
}
async function ktwToMenu(){
 g_PauseControl.implicitPause();
 var index=await Engine.OpenChildPage("page_msgbox.xml",{width:500,height:220,title:ktwText("menu"),message:ktwText("menuWarning"),buttonCaptions:[ktwText("cancel"),ktwText("menu")]});
 if(index===1){Engine.EndGame();Engine.SwitchGuiPage("page_pregame.xml");}
 else resumeGame();
}
async function ktwConfirmSurrender(){
 g_PauseControl.implicitPause();
 var index=await Engine.OpenChildPage("page_msgbox.xml",{width:500,height:210,title:ktwText("surrender"),message:ktwText("surrender")+"?",buttonCaptions:[ktwText("cancel"),ktwText("surrender")]});
 resumeGame();
 if(index===1)ktwCommand("surrender");
}

// Political presentation only: all decisions are computed by simulation.
var g_KtwDossier = null, g_KtwDossierStamp = "", g_KtwAutosaveTurn = null;
function ktwCharacterName(state,id) {
 var character=(state.characters || []).find(c=>c.id===id);
 return character?ktwLocal(character.name):id || ktwText("noCandidate");
}
function ktwProvinceName(state,id) {
 var province=state.provinces.find(p=>p.id===id);
 return province?ktwLocal(province.name):id || "";
}
function ktwToggleDossier(section) {
 g_KtwDossier=g_KtwDossier===section?null:section;
 g_KtwDossierStamp="";
 ktwRenderDossier();
}
function ktwDossierSection(section) { g_KtwDossier=section;g_KtwDossierStamp="";ktwRenderDossier(); }
function ktwCouncilText(view) {
 var s=view.state, council=view.council;
 var lines=[ktwText("councilRule"),""];
 if(!council)return lines.concat([ktwText("noCandidate")]).join("\n");
 lines.push(ktwText("ruler")+": "+ktwCharacterName(s,council.rulerId));
 lines.push(ktwText("nextCandidate")+": "+ktwCharacterName(s,council.selectedCandidateId),"");
 (council.groups || []).forEach(function(group) {
  lines.push(ktwLocal(group.name)+" · "+ktwText("influence")+": "+group.influence);
  lines.push(ktwText("supports")+": "+ktwCharacterName(s,group.supportsCharacterId));
  (group.candidates || []).forEach(function(candidate) {
   lines.push("  "+ktwCharacterName(s,candidate.characterId)+" — "+ktwText("score")+": "+candidate.score);
   lines.push("  "+(candidate.factors || []).map(function(f) {
    return ktwText(f.code)+" "+f.value+" × "+f.weight+" = "+f.points;
   }).join("; "));
  });
  lines.push("");
 });
 return lines.join("\n");
}
function ktwArchiveText(s) {
 var lines=[ktwText("characterDataNotice"),""];
 (s.characters || []).forEach(function(c) {
  var dynasty=(s.dynasties || []).find(d=>d.id===c.dynastyId);
  lines.push(ktwCharacterName(s,c.id)+" — "+ktwText(c.title)+" · "+ktwText(c.status));
  lines.push(ktwText(c.factionId)+" · "+ktwText("dynasty")+": "+(dynasty?ktwLocal(dynasty.name):c.dynastyId || ktwText("unknown")));
  lines.push(ktwText("birthYear")+": "+(c.birthYear || ktwText("unknown"))+" · "+ktwText("health")+": "+c.health);
  ["parents","children","spouses"].forEach(function(link){
   lines.push(ktwText(link)+": "+(c[link] && c[link].length?c[link].map(id=>ktwCharacterName(s,id)).join(", "):ktwText("unknown")));
  });
  if(c.abilities)lines.push(["leadership","warfare","diplomacy"].map(key=>ktwText(key)+": "+c.abilities[key]).join(" · "));
  if(c.death)lines.push(ktwText("dead")+": "+c.death.year+", "+ktwText(c.death.season)+" · "+ktwText("turn")+" "+c.death.turn+" · "+c.death.battleId);
  lines.push("");
 });
 return lines.join("\n");
}
function ktwEventText(s,event) {
 var data=event.data || {}, type=event.key || event.type, lines=[ktwText("turn")+" "+event.turn+" · "+ktwText(type)];
 if(data.provinceId)lines.push(ktwProvinceName(s,data.provinceId));
 if(data.reason)lines.push(ktwText("reason")+": "+ktwText(data.reason));
 if(data.factors) {
  var facts=data.factors;
  lines.push(["ownSoldiers","enemySoldiers","distanceProvinces"].filter(k=>facts[k]!==undefined).map(k=>ktwText(k)+": "+facts[k]).join(" · "));
 }
 if(type==="recruited")lines.push(ktwUnit(data.type)+": "+data.count);
 if(type==="building_completed")lines.push(ktwText(data.kind).split(" · ")[0]);
 if(type==="truce_signed" && data.payment)lines.push(ktwText("silver")+": "+data.payment+" · "+ktwText("turn")+": "+data.durationTurns);
 if(type==="turn_started")lines.push(data.year+" · "+ktwText(data.season));
 if(data.winner)lines.push(ktwText("winner")+": "+ktwText(data.winner));
 if(data.losses)lines.push(ktwText("losses")+": "+Object.keys(data.losses).map(f=>ktwText(f)+" "+data.losses[f]).join(" · "));
 if(data.characterId)lines.push(ktwCharacterName(s,data.characterId));
 if(data.previousRulerId)lines.push(ktwText("former_khan")+": "+ktwCharacterName(s,data.previousRulerId));
 if(data.rulerId)lines.push(ktwText("ruler")+": "+ktwCharacterName(s,data.rulerId));
 if(data.commanderId)lines.push(ktwText("commander")+": "+ktwCharacterName(s,data.commanderId));
 if(data.reasonCode)lines.push(ktwText("reason")+": "+ktwText(data.reasonCode));
 return lines.filter(Boolean).join("\n");
}
function ktwJournalText(s) {
 var events=(s.events || []).concat(s.politicalEvents || []).map(function(event,index){return {event,index};});
 events.sort(function(a,b){return b.event.turn-a.event.turn || b.index-a.index;});
 return events.length?events.map(item=>ktwEventText(s,item.event)).join("\n\n"):ktwText("noEvents");
}
function ktwRenderDossier() {
 var visible=!!g_KtwDossier && g_KtwView && g_KtwView.mode==="campaign" && !g_KtwView.state.pendingBattle;
 ktwObject("ktwDossier").hidden=!visible;
 if(!visible)return;
 var s=g_KtwView.state;
 var stamp=JSON.stringify([g_KtwDossier,s.turn,s.lastBattle,s.events,s.politicalEvents,s.characters,g_KtwView.council]);
 if(stamp===g_KtwDossierStamp)return;
 g_KtwDossierStamp=stamp;
 ktwCaption("ktwDossierTitle",ktwText(g_KtwDossier));
 ktwCaption("ktwDossierBody",g_KtwDossier==="council"?ktwCouncilText(g_KtwView):g_KtwDossier==="archive"?ktwArchiveText(s):ktwJournalText(s));
 ktwObject("ktwDossierCouncil").hidden=g_KtwDossier==="journal";
 ktwObject("ktwDossierArchive").hidden=g_KtwDossier==="journal";
}
function ktwAutosave(view) {
 if(g_KtwAutosaveTurn===null){g_KtwAutosaveTurn=view.state.turn;return;}
 if(view.mode!=="campaign" || view.error || view.state.turn===g_KtwAutosaveTurn)return;
 g_KtwAutosaveTurn=view.state.turn;
 var slot="ktw_autosave_"+(view.state.turn%2);
 var description="KTW autosave · "+view.state.turn+" · "+Date.now();
 Engine.SaveGame(slot,description,getSavedGameData());
 var ok=Engine.GetSavedGames().some(g=>g.id===slot && g.metadata.description===description);
 if(!ok)ktwFeedback(ktwText("saveFailed"));
}
function ktwFocusCommander() {
 if(!g_KtwView)return;
 var commander=(g_KtwView.commanders || []).find(c=>c.armyId==="kazakh_main" && c.alive);
 if(!commander)return;
 var state=Engine.GuiInterfaceCall("GetEntityState",commander.entity);
 if(state && state.position)Engine.CameraMoveTo(state.position.x,state.position.z);
}
async function ktwSessionSettings() {
 g_PauseControl.implicitPause();
 await ktwOpenOptions();
 resumeGame();
}
