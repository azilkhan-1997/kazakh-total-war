/* SPDX-License-Identifier: GPL-2.0-or-later */
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const Politics=require('../mods/kazakh_total_war/simulation/helpers/KtwPolitics.js');
function harness(language='ru') {
 const objects={},saved=[],writes=[];
 const info={engine_serialization_version:'0.28.0',mods:[{mod:'public',version:'0.28.0'},{mod:'kazakh_total_war',version:'0.2.0'}]};
 const context=vm.createContext({Date,Engine:{
  ConfigDB_GetValue:()=>language,
  GetEngineInfo:()=>info,
  GetSavedGames:()=>saved,
  GetGUIObjectByName:name=>objects[name] || (objects[name]={}),
  SaveGame:(id,description)=>{writes.push({id,description});const old=saved.findIndex(s=>s.id===id);if(old>=0)saved.splice(old,1);saved.push({id,metadata:{description}});},
  ReadJSONFile:()=>JSON.parse(fs.readFileSync(path.join(root,'mods/kazakh_total_war/gui/ktw/data.json'),'utf8'))
 },getSavedGameData:()=>({})});
 for(const file of ['gui/common/ktw.js','gui/session/ktw.js'])vm.runInContext(fs.readFileSync(path.join(root,'mods/kazakh_total_war',file),'utf8'),context);
 return {context,objects,saved,writes,info};
}
function saved(id,time,version='0.1.0') {return {id,metadata:{time,engine_serialization_version:'0.28.0',mods:[{mod:'public',version:'0.28.0'},{mod:'kazakh_total_war',version}],initAttributes:{map:'maps/random/ktw_campaign',settings:{KtwMode:'campaign'}}}};}
test('Continue accepts v0.1 native KTW saves and chooses newest compatible campaign',()=>{
 const h=harness();h.saved.push(saved('old',100),saved('recent',200,'0.2.0'));
 const other=saved('unrelated',300);other.metadata.initAttributes.map='maps/random/acropolis';h.saved.push(other);
 assert.equal(h.context.ktwLatestSave().id,'recent');
 h.saved.splice(1,1);assert.equal(h.context.ktwLatestSave().id,'old');
});
test('Continue rejects future schema carrier, missing mod, extra dependency and incompatible engine',()=>{
 const h=harness();const variants=[saved('future',10,'0.3.0'),saved('missing',10),saved('extra',10),saved('engine',10)];
 variants[1].metadata.mods.pop();variants[2].metadata.mods.push({mod:'other',version:'1'});variants[3].metadata.engine_serialization_version='0.27.0';
 for(const save of variants)assert.equal(h.context.ktwCompatibleSave(save,h.info),false,save.id);
});
test('Autosave starts only on turn advance and alternates two slots without repeating on UI ticks',()=>{
 const h=harness(),view={mode:'campaign',error:'',state:{turn:1}};
 h.context.ktwAutosave(view);assert.equal(h.writes.length,0);
 view.state.turn=2;h.context.ktwAutosave(view);h.context.ktwAutosave(view);
 view.state.turn=3;h.context.ktwAutosave(view);
 assert.deepEqual(h.writes.map(w=>w.id),['ktw_autosave_0','ktw_autosave_1']);
 view.mode='battle';view.state.turn=4;h.context.ktwAutosave(view);assert.equal(h.writes.length,2);
 view.mode='campaign';view.error='KTW_INVALID_STATE';h.context.ktwAutosave(view);assert.equal(h.writes.length,2);
});
test('RU KK EN explain enemy decisions with translated reasons and numeric factors',()=>{
 const event={turn:2,key:'strategic_decision',data:{provinceId:'shu',reason:'advance_against_hostile_army',factors:{ownSoldiers:155,enemySoldiers:170,distanceProvinces:2}}};
 for(const language of ['ru','kk','en']){
  const h=harness(language);const text=h.context.ktwEventText({provinces:[{id:'shu',name:{ru:'Шу',kk:'Шу',en:'Shu'}}]},event);
  assert.ok(!text.includes('advance_against_hostile_army'));
  assert.ok(!text.includes('strategic_decision'));
  assert.match(text,/155/);assert.match(text,/170/);assert.match(text,/2/);
 }
});
test('Council presents simulation factor weights, archive retains known family links and unknown dates',()=>{
 const state={turn:1,year:1465,season:'spring',armies:[{id:'kazakh_main',faction:'kazakh',commander:'kerei'},{id:'abulkhair_main',faction:'abulkhair',commander:'abulkhair'}]};Politics.initialize(state);
 const h=harness('en'),council=Politics.describeCouncil(state,'kazakh');
 const text=h.context.ktwCouncilText({state,council}),archive=h.context.ktwArchiveText(state);
 assert.match(text,/Janibek/);assert.match(text,/Leadership 50 × 2 = 100/);
 assert.match(archive,/Burunduk/);assert.match(archive,/Parents: Kerei Khan/);assert.match(archive,/Birth year: Not established/);
});
test('Recovery screen blocks campaign controls and saving before malformed state is rendered',()=>{
 const h=harness();h.context.Engine.GuiInterfaceCall=()=>({error:'KTW_LOAD_RECOVERY_REQUIRED: invalid unit binding',state:{bad:true}});
 h.context.g_KtwBooted=true;
 h.context.ktwSessionTick();
 assert.equal(h.objects.ktwRecovery.hidden,false);
 assert.equal(h.objects.ktwSave.enabled,false);
 assert.equal(h.objects.ktwCampaignPanels.hidden,true);
 assert.equal(h.writes.length,0);
});
