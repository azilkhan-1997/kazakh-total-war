'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const file = path.resolve(__dirname,'../mods/kazakh_total_war/simulation/helpers/KtwCampaign.js');
const C = require(file);
function pending(seed=1465) { const s=C.create(seed); C.moveArmy(s,'kazakh_main','sarysu'); C.endTurn(s); assert.ok(s.pendingBattle); return s; }
function result(s,winner='kazakh',winnerRatio=0.8,loserRatio=0) {
  const out={battleId:s.pendingBattle.id,winner,survivors:{}};
  s.pendingBattle.armies.forEach(a=>a.regiments.forEach(r=>out.survivors[r.id]=Math.floor(r.count*(a.faction===winner?winnerRatio:loserRatio)))); return out;
}
function unchangedOnThrow(s,fn,re) { const before=JSON.stringify(s); assert.throws(fn,re); assert.equal(JSON.stringify(s),before); }
test('deterministic seed, 8provinces,325individual soldiers and5unit types',()=>{
 const a=C.create(71),b=C.create(71);assert.deepEqual(a,b);assert.equal(a.provinces.length,8);assert.equal(a.armies.reduce((n,x)=>n+C.soldiers(x),0),325);assert.equal(new Set(a.armies[0].regiments.map(x=>x.type)).size,5);assert.ok(C.validate(a));
});
test('campaign runs in SpiderMonkey-style host without require/module and registers global',()=>{
 const exported={};const context={Engine:{RegisterGlobal(name,value){exported[name]=value;}}}; vm.createContext(context); for (const name of ['KtwCampaign.js','KtwSaveSystem.js','KtwPolitics.js','KtwBattleBridge.js']) vm.runInContext(fs.readFileSync(path.join(path.dirname(file),name),'utf8'),context); assert.equal(exported.KtwCampaign.create().year,1465);assert.equal(Object.keys(exported).length,4);
});
test('adjacent movement captures province and uses one movement point',()=>{
 const s=C.create();C.moveArmy(s,'kazakh_main','sarysu');assert.equal(C.getArmy(s,'kazakh_main').province,'sarysu');assert.equal(C.getProvince(s,'sarysu').owner,'kazakh');unchangedOnThrow(s,()=>C.moveArmy(s,'kazakh_main','sygnak'),/INVALID_MOVE/);
});
test('nonadjacent and unknown moves never change state',()=>{
 const s=C.create(); unchangedOnThrow(s,()=>C.moveArmy(s,'kazakh_main','otrar'),/INVALID_MOVE/);unchangedOnThrow(s,()=>C.moveArmy(s,'kazakh_main','unknown'),/INVALID_MOVE/);unchangedOnThrow(s,()=>C.moveArmy(s,'abulkhair_main','sarysu'),/INVALID_MOVE/);
});
test('strategic opponent attacks after two end turns',()=>{
 const s=C.create();C.endTurn(s);assert.equal(C.getArmy(s,'abulkhair_main').province,'sarysu');assert.equal(s.pendingBattle,null);C.endTurn(s);assert.equal(s.pendingBattle.provinceId,'shu');assert.equal(s.pendingBattle.attackerId,'abulkhair_main');
});
test('pendingbattle locks economic commands and turn progression',()=>{
 const s=pending(); for (const fn of [()=>C.endTurn(s),()=>C.recruit(s,'kazakh_main','spearman',20),()=>C.build(s,'shu','pasture'),()=>C.diplomacy(s,'peace'),()=>C.moveArmy(s,'kazakh_main','shu')]) unchangedOnThrow(s,fn,/BATTLE_PENDING/);
});
test('tactical victory returns actual survivors, ownership,experience and campaign victory',()=>{
 const s=pending(),r=result(s);const original=C.soldiers(C.getArmy(s,'kazakh_main'));const summary=C.resolveBattle(s,r);assert.equal(s.pendingBattle,null);assert.equal(s.status,'victory');assert.equal(C.getProvince(s,'sarysu').owner,'kazakh');assert.equal(summary.losses.kazakh,original-C.soldiers(C.getArmy(s,'kazakh_main')));assert.equal(C.getArmy(s,'kazakh_main').regiments[0].experience,10);assert.equal(C.soldiers(C.getArmy(s,'abulkhair_main')),0);
});
test('tactical defeat captures territory and marks defeat when player has no survivors',()=>{
 const s=pending();C.resolveBattle(s,result(s,'abulkhair'));assert.equal(s.status,'defeat');assert.equal(C.getProvince(s,'sarysu').owner,'abulkhair');assert.equal(C.getArmy(s,'abulkhair_main').province,'sarysu');
});
test('surviving losing defender retreats to friendly adjacent province',()=>{
 const s=pending();C.resolveBattle(s,result(s,'abulkhair',0.8,0.5));assert.equal(s.status,'playing');assert.equal(C.getArmy(s,'kazakh_main').province,'shu');assert.equal(C.getProvince(s,'sarysu').owner,'abulkhair');
});
test('matching duplicate result applies once; changed duplicate rejected',()=>{
 const s=pending(),r=result(s);C.resolveBattle(s,r);const saved=JSON.stringify(s);assert.equal(C.resolveBattle(s,r).alreadyApplied,true);assert.equal(JSON.stringify(s),saved);const changed=structuredClone(r);changed.survivors.r1--;unchangedOnThrow(s,()=>C.resolveBattle(s,changed),/CONFLICTING_RESULT/);
});
test('stale IDs, foreign regiments,missing entries, soldier gains and impossible winners rejected atomically',()=>{
 for (const mutation of [r=>r.battleId='stale',r=>r.survivors.extra=0,r=>delete r.survivors.r1,r=>r.survivors.r1=1000,r=>r.winner='other',r=>{for (const k of Object.keys(r.survivors)) r.survivors[k]=0;}]) {const s=pending(),r=result(s);mutation(r);unchangedOnThrow(s,()=>C.resolveBattle(s,r),/KTW_/);}
});
test('autoresolve deterministic and never creates survivors',()=>{
 const a=pending(55),b=pending(55);const before=new Map(a.armies.flatMap(x=>x.regiments.map(r=>[r.id,r.count])));C.autoresolve(a);C.autoresolve(b);assert.deepEqual(a,b);a.armies.forEach(x=>x.regiments.forEach(r=>assert.ok(r.count<=before.get(r.id))));
});
test('retreat transfers provincial ownership and applies pursuit casualties',()=>{
 const s=pending();const before=C.soldiers(C.getArmy(s,'kazakh_main'));C.retreat(s);assert.equal(C.getArmy(s,'kazakh_main').province,'shu');assert.ok(C.soldiers(C.getArmy(s,'kazakh_main'))<before);assert.equal(s.pendingBattle,null);
});
test('pendingbattle roundtrip, postbattle roundtrip,continued simulation unchanged',()=>{
 let s=pending(53),copy=C.restore(C.serialize(s));assert.deepEqual(s,copy);C.autoresolve(s);C.autoresolve(copy);assert.deepEqual(s,copy);assert.deepEqual(C.restore(C.serialize(s)),s);
});
test('checksum detects damaged save and validation rejects malformed native state',()=>{
 const s=C.create(),text=C.serialize(s),envelope=JSON.parse(text);envelope.payload=envelope.payload.replace('650','999');assert.throws(()=>C.restore(JSON.stringify(envelope)),/SAVE_CHECKSUM/);assert.throws(()=>C.restore('{'),/SAVE_JSON/);const bad=structuredClone(s);bad.armies[0].regiments[0].count=-1;assert.throws(()=>C.validate(bad),/SAVE_REGIMENT/);bad.armies[0].regiments[0].count=30;bad.nextRegimentId=1;assert.throws(()=>C.validate(bad),/SAVE_COUNTER/);
});
test('recruitment charges resources, limits counts and rejects prototype property names',()=>{
 const s=C.create(),old=s.treasury.kazakh.silver;const r=C.recruit(s,'kazakh_main','spearman',20);assert.equal(r.count,20);assert.equal(s.treasury.kazakh.silver,old-C.unitTypes.spearman.cost);for(const n of [-20,0,31,NaN,1.5])unchangedOnThrow(s,()=>C.recruit(s,'kazakh_main','spearman',n),/INVALID_RECRUIT/);for(const type of ['__proto__','constructor','toString'])unchangedOnThrow(s,()=>C.recruit(s,'kazakh_main',type,20),/INVALID_RECRUIT/);
});
test('buildings require owned land and funds; supply shortage causes attrition not negative stocks',()=>{
 const s=C.create();C.build(s,'shu','pasture');assert.equal(C.getProvince(s,'shu').buildings.pasture,1);unchangedOnThrow(s,()=>C.build(s,'sygnak','market'),/INVALID_BUILDING/);unchangedOnThrow(s,()=>C.build(s,'shu','toString'),/INVALID_BUILDING/);s.treasury.kazakh.silver=0;unchangedOnThrow(s,()=>C.recruit(s,'kazakh_main','spearman',20),/INSUFFICIENT/);s.treasury.kazakh.food=0;s.turn=3;s.year=1465;s.season='autumn';const before=C.soldiers(C.getArmy(s,'kazakh_main'));C.endTurn(s);assert.equal(s.season,'winter');assert.equal(s.treasury.kazakh.food,0);assert.ok(C.soldiers(C.getArmy(s,'kazakh_main'))<before);
});
test('three-turn truce stops AI, blocks border capture,expires deterministically',()=>{
 const s=C.create();C.diplomacy(s,'peace');assert.equal(s.treasury.kazakh.silver,400);unchangedOnThrow(s,()=>C.moveArmy(s,'kazakh_main','sarysu'),/PEACE_BORDER/);C.endTurn(s);C.endTurn(s);assert.equal(C.getArmy(s,'abulkhair_main').province,'sygnak');C.endTurn(s);assert.equal(s.relation,'war');assert.equal(C.getArmy(s,'abulkhair_main').province,'sarysu');
});
test('stale battle snapshot in engine-native save is rejected',()=>{
 const s=pending();s.pendingBattle.armies[0].regiments[0].count++;assert.throws(()=>C.validate(s),/SAVE_BATTLE_ROSTER/);
});

test('unimplemented future troop types cannot enter an engine battle roster',()=>{
 const s=C.create();for(const type of ['sabre_warrior','khan_guard','scout','tribal_militia'])unchangedOnThrow(s,()=>C.recruit(s,'kazakh_main',type,20),/INVALID_RECRUIT/);assert.equal(C.implementedUnitTypes.length,5);
});

test('native saved state cannot introduce an unimplemented troop template',()=>{const s=C.create();s.armies[0].regiments[0].type='scout';assert.throws(()=>C.validate(s),/SAVE_REGIMENT/);});
