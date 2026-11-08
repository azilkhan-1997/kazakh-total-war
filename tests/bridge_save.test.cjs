'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../mods/kazakh_total_war/simulation/helpers');
const C = require(path.join(root, 'KtwCampaign.js'));
const P = require(path.join(root, 'KtwPolitics.js'));
const S = require(path.join(root, 'KtwSaveSystem.js'));
function fixture(name) { return fs.readFileSync(path.join(__dirname, 'fixtures', name+'.campaign.json'), 'utf8'); }
function pending() { const s=C.create(); C.moveArmy(s,'kazakh_main','sarysu'); C.endTurn(s); return s; }
function result(s) {
 const r={battleId:s.pendingBattle.id,winner:'kazakh',survivors:{}};
 s.pendingBattle.armies.forEach(a=>a.regiments.forEach(x=>r.survivors[x.id]=Math.floor(x.count*(a.faction==='kazakh'?0.8:0.3))));
 return r;
}
function rejected(s, fn, pattern=/KTW_/) { const before=JSON.stringify(s); assert.throws(fn,pattern); assert.equal(JSON.stringify(s),before); }

test('schema 1 pending fixture migrates without altering calendar, resources or troops',()=>{
 const source=fixture('v1_pending'), old=JSON.parse(JSON.parse(source).payload), s=C.restore(source);
 assert.equal(old.schemaVersion,1); assert.equal(s.schemaVersion,2);
 for(const key of ['campaignId','turn','year','season','treasury','armies','provinces','resolvedBattles'])assert.deepEqual(s[key],old[key]);
 assert.equal(s.pendingBattle.id,old.pendingBattle.id);assert.equal(s.pendingBattle.bridgeVersion,2);
 assert.deepEqual(s.pendingBattle.armies,old.pendingBattle.armies);assert.equal(s.pendingBattle.commanders.length,2);
 assert.ok(s.characters.every(c=>c.alive));assert.deepEqual(C.restore(C.serialize(s)),s);
});
test('schema 1 completed fixture preserves old receipt and remains idempotent',()=>{
 const s=C.restore(fixture('v1_completed')), old=JSON.parse(JSON.parse(fixture('v1_completed')).payload);
 assert.deepEqual(s.resolvedBattles,old.resolvedBattles); assert.deepEqual(s.armies,old.armies);
 const stored=JSON.parse(s.resolvedBattles[0].signature), r={battleId:stored.battleId,winner:stored.winner,survivors:Object.fromEntries(stored.survivors)};
 const before=JSON.stringify(s);assert.equal(C.resolveBattle(s,r).alreadyApplied,true);assert.equal(JSON.stringify(s),before);
});
test('native-state upgrade returns independent validated clone and preserves source',()=>{
 const old=JSON.parse(JSON.parse(fixture('v1_pending')).payload), before=JSON.stringify(old), s=C.upgrade(old);
 assert.equal(JSON.stringify(old),before);assert.notEqual(s,old);assert.equal(s.schemaVersion,2);
 s.armies[0].regiments[0].count--;assert.equal(JSON.stringify(old),before);
 const v2=C.create(),copy=C.upgrade(v2);assert.deepEqual(copy,v2);assert.notEqual(copy,v2);
});
test('checksum is checked before migration, and envelope/payload versions must match',()=>{
 const e=JSON.parse(fixture('v1_pending'));e.payload=e.payload.replace('"silver":800','"silver":801');
 assert.throws(()=>C.restore(JSON.stringify(e)),/SAVE_CHECKSUM/);
 const wrong=JSON.parse(fixture('v1_pending'));wrong.version=2;assert.throws(()=>C.restore(JSON.stringify(wrong)),/SAVE_VERSION/);
 const invalid=JSON.parse(JSON.parse(fixture('v1_pending')).payload);invalid.armies[0].regiments[0].count=-1;
 assert.throws(()=>C.upgrade(invalid),/SAVE_REGIMENT/);
 assert.throws(()=>C.upgrade({...C.create(),schemaVersion:99}),/SAVE_VERSION/);
});
test('pending battle snapshots commanders, context and immutable army copies',()=>{
 const s=pending(),b=s.pendingBattle;assert.deepEqual(b.currentDate,{year:1465,season:'summer',turn:2});assert.equal(b.weather,'clear');
 assert.equal(b.battleType,'field');assert.deepEqual(b.reinforcements,[]);
 assert.deepEqual(b.commanders.map(c=>c.character.id),['abulkhair','kerei']);
 assert.notEqual(b.commanders[0].character,C.getCharacter(s,'abulkhair'));
 assert.notEqual(b.armies[0],C.getArmy(s,'abulkhair_main'));
});
test('stale commander snapshot and altered battle context reject loaded state',()=>{
 for(const mutate of [s=>s.pendingBattle.commanders[0].character.health=1,s=>s.pendingBattle.weather='rain',s=>s.pendingBattle.currentDate.turn++,s=>s.pendingBattle.reinforcements.push({id:'fake'})]){
  const s=pending();mutate(s);assert.throws(()=>C.validate(s),/KTW_/);
 }
});
test('confirmed commander death triggers succession and keeps family archive',()=>{
 const s=pending(),r=result(s);r.commanderOutcomes={kerei:'dead',abulkhair:'alive'};const outer=s;
 C.resolveBattle(s,r);assert.equal(s,outer);assert.equal(C.getCharacter(s,'kerei').alive,false);
 assert.equal(C.getCharacter(s,'kerei').death.battleId,r.battleId);
 assert.deepEqual(C.getCharacter(s,'kerei').children,['burunduk']);assert.deepEqual(C.getCharacter(s,'burunduk').parents,['kerei']);
 assert.equal(C.getFaction(s,'kazakh').rulerId,'janibek');assert.equal(C.getArmy(s,'kazakh_main').commander,'janibek');
 assert.equal(C.getFaction(s,'kazakh').authority,45);assert.deepEqual(s.lastBattle.deadCommanders,['kerei']);
 const succession=s.politicalEvents.find(e=>e.type==='succession_completed');assert.ok(succession);
 assert.equal(succession.data.reasonCode,'weighted_council_vote');assert.ok(succession.data.council.groups[0].candidates[0].factors.length);
 assert.ok(C.validate(s));assert.deepEqual(C.restore(C.serialize(s)),s);
});
test('commander death receipt survives restart and cannot apply consequences twice',()=>{
 const s=pending(),r=result(s);r.commanderOutcomes={kerei:'dead'};C.resolveBattle(s,r);
 const loaded=C.restore(C.serialize(s)),before=JSON.stringify(loaded);
 assert.equal(C.resolveBattle(loaded,r).alreadyApplied,true);assert.equal(JSON.stringify(loaded),before);
 const alive=structuredClone(r);alive.commanderOutcomes.kerei='alive';rejected(loaded,()=>C.resolveBattle(loaded,alive),/CONFLICTING_RESULT/);
});
test('explicit all-alive outcome has same receipt as a legacy no-outcome result',()=>{
 const s=pending(),r=result(s);C.resolveBattle(s,r);const before=JSON.stringify(s);
 r.commanderOutcomes={kerei:'alive',abulkhair:'alive'};assert.equal(C.resolveBattle(s,r).alreadyApplied,true);assert.equal(JSON.stringify(s),before);
});
test('unverified commander IDs, wrong types and unsupported outcome states are atomic rejections',()=>{
 for(const value of [{kasym:'dead'},{unknown:'alive'},{kerei:'wounded'},null,[],{kerei:1}]){
  const s=pending(),r=result(s);r.commanderOutcomes=value;rejected(s,()=>C.resolveBattle(s,r),/RESULT_COMMANDERS/);
 }
});
test('reported commander death requires an actual casualty in the same army',()=>{
 const s=pending(),r=result(s);for(const a of s.pendingBattle.armies)if(a.faction==='kazakh')for(const x of a.regiments)r.survivors[x.id]=x.count;
 r.commanderOutcomes={kerei:'dead'};rejected(s,()=>C.resolveBattle(s,r),/RESULT_COMMANDER_WITHOUT_CASUALTY/);
});
test('transaction rollback includes failures after staged casualty mutation',()=>{
 const s=pending(),r=result(s),original=P.onBattleResult;
 try{P.onBattleResult=function(candidate){candidate.treasury.kazakh.silver=0;throw new Error('INJECTED_CONSEQUENCE_FAILURE');};rejected(s,()=>C.resolveBattle(s,r),/INJECTED/);}
 finally{P.onBattleResult=original;}
 assert.ok(s.pendingBattle);C.resolveBattle(s,r);assert.equal(s.pendingBattle,null);
});
test('interrupted battle can be restored; corrupt report leaves checkpoint usable',()=>{
 const original=pending(),checkpoint=C.serialize(original),restored=C.restore(checkpoint),bad=result(restored);bad.survivors.r1=999;
 rejected(restored,()=>C.resolveBattle(restored,bad),/RESULT_SURVIVORS/);assert.equal(C.serialize(restored),checkpoint);
 const valid=result(restored);valid.commanderOutcomes={kerei:'dead'};C.resolveBattle(restored,valid);
 assert.equal(restored.pendingBattle,null);assert.equal(C.getCharacter(restored,'kerei').alive,false);
});
test('death of sole enemy ruler leaves explicit vacancy without invented historical successor',()=>{
 const s=pending(),r=result(s);r.commanderOutcomes={abulkhair:'dead'};C.resolveBattle(s,r);
 assert.equal(C.getFaction(s,'abulkhair').rulerId,null);assert.equal(C.getArmy(s,'abulkhair_main').commander,null);
 assert.equal(s.characters.length,5);assert.ok(s.politicalEvents.some(e=>e.type==='succession_vacant'));
 assert.ok(C.validate(s));
});
test('JSON recovery selects valid primary or validated backup and never repairs corrupt data in place',()=>{
 const primary=C.serialize(pending()),backup=C.serialize(C.create()),first=C.restoreWithRecovery(primary,backup);
 assert.equal(first.source,'primary');assert.equal(first.recovered,false);assert.ok(first.state.pendingBattle);
 const fallback=C.restoreWithRecovery(primary.slice(0,-20),backup);assert.equal(fallback.source,'backup');assert.equal(fallback.recovered,true);
 assert.equal(fallback.state.pendingBattle,null);assert.match(fallback.primaryError,/SAVE_JSON/);
 assert.throws(()=>C.restoreWithRecovery('{','{'),/SAVE_RECOVERY_FAILED/);
 assert.equal(C.restoreWithRecovery('{',fixture('v1_pending')).state.schemaVersion,2);
});
test('stable event IDs and political IDs survive serialization without duplication',()=>{
 const s=pending(),r=result(s);r.commanderOutcomes={kerei:'dead'};C.resolveBattle(s,r);const copy=C.restore(C.serialize(s));
 assert.deepEqual(copy.events,s.events);assert.deepEqual(copy.politicalEvents,s.politicalEvents);
 const ids=[...s.events,...s.politicalEvents].map(e=>e.id);assert.equal(new Set(ids).size,ids.length);
 const invalid=structuredClone(s);invalid.events[1].id=invalid.events[0].id;assert.throws(()=>C.validate(invalid),/SAVE_EVENT/);
});
test('strategic movement and diplomatic changes expose reproducible reason factors',()=>{
 const s=C.create();C.endTurn(s);const decision=s.events.find(e=>e.key==='strategic_decision');assert.ok(decision);
 assert.equal(decision.data.reason,'advance_against_hostile_army');assert.equal(decision.data.factors.relation,'war');
 assert.ok(decision.data.factors.ownSoldiers>0);assert.deepEqual(decision.data.factors.path,['sygnak','sarysu','shu']);
 const peaceful=C.create();C.diplomacy(peaceful,'peace');assert.equal(peaceful.events.at(-1).data.reason,'tribute_accepted');
 C.endTurn(peaceful);C.endTurn(peaceful);C.endTurn(peaceful);assert.equal(peaceful.events.find(e=>e.key==='truce_expired').data.reason,'agreed_term_ended');
});
test('codec rejects oversize envelopes rather than producing unloadable output',()=>{
 assert.throws(()=>S.decode('x'.repeat(2000001)),/SAVE_SIZE/);
 assert.throws(()=>S.encode({schemaVersion:2,huge:'"'.repeat(600000)}),/SAVE_SIZE/);
});
test('battle ID counters and malformed receipts cannot be reused after loading',()=>{
 const s=pending();s.nextBattleId=1;assert.throws(()=>C.validate(s),/SAVE_BATTLE/);
 for(const mutate of [x=>x.nextBattleId=1,x=>x.resolvedBattles[0].signature='{',x=>x.resolvedBattles[0].id='battle-999',x=>x.lastBattle.battleId='battle-999']){
  const complete=pending();C.resolveBattle(complete,result(complete));mutate(complete);assert.throws(()=>C.validate(complete),/SAVE_HISTORY/);
 }
});
test('dead character archive and battle receipt must agree after loading',()=>{
 const s=pending(),r=result(s);r.commanderOutcomes={kerei:'dead'};C.resolveBattle(s,r);
 const missing=structuredClone(s),receipt=JSON.parse(missing.resolvedBattles[0].signature);delete receipt.deadCommanders;
 missing.resolvedBattles[0].signature=JSON.stringify(receipt);assert.throws(()=>C.validate(missing),/SAVE_CHARACTER_HISTORY/);
 const unknown=structuredClone(s),bad=JSON.parse(unknown.resolvedBattles[0].signature);bad.deadCommanders.push('fictional_commander');
 unknown.resolvedBattles[0].signature=JSON.stringify(bad);assert.throws(()=>C.validate(unknown),/SAVE_CHARACTER_HISTORY/);
});
test('autoresolve of depleted one-warrior regiments retains a valid winner',()=>{
 const s=pending(),r=result(s);r.winner='draw';for(const id of Object.keys(r.survivors))r.survivors[id]=1;
 C.resolveBattle(s,r);C.endTurn(s);assert.ok(s.pendingBattle);
 const before=new Map(s.pendingBattle.armies.flatMap(a=>a.regiments.map(x=>[x.id,x.count])));
 const summary=C.autoresolve(s);assert.equal(s.pendingBattle,null);
 assert.ok(C.soldiers(C.getArmy(s,summary.winner+'_main'))>=1);
 s.armies.forEach(a=>a.regiments.forEach(x=>assert.ok(x.count<=before.get(x.id))));assert.ok(C.validate(s));
});
test('battle terrain and retreat origins must agree with actual army positions',()=>{
 for(const mutate of [s=>s.pendingBattle.terrain='not_a_terrain',s=>s.pendingBattle.attackerOrigin='otrar',s=>s.pendingBattle.defenderOrigin='shu',s=>s.relation='peace']){
  const s=pending();mutate(s);assert.throws(()=>C.validate(s),/SAVE_BATTLE_GEOGRAPHY/);
 }
});
test('a forged internally matching roster cannot move the defender or attacker away from battle adjacency',()=>{
 const displaced=pending(),d=displaced.pendingBattle;
 C.getArmy(displaced,d.defenderId).province='shu';d.armies[1].province='shu';d.defenderOrigin='shu';
 assert.throws(()=>C.validate(displaced),/SAVE_BATTLE_GEOGRAPHY/);
 const distant=pending(),b=distant.pendingBattle;
 C.getArmy(distant,b.attackerId).province='otrar';b.armies[0].province='otrar';b.attackerOrigin='otrar';
 assert.throws(()=>C.validate(distant),/SAVE_BATTLE_GEOGRAPHY/);
 const movement=pending(),m=movement.pendingBattle;
 C.getArmy(movement,m.attackerId).movement=1;m.armies[0].movement=1;
 assert.throws(()=>C.validate(movement),/SAVE_BATTLE_GEOGRAPHY/);
});
