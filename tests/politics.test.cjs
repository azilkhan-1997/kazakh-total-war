'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = path.resolve(__dirname,'../mods/kazakh_total_war/simulation/helpers/KtwPolitics.js');
const P = require(source);
const copy = x=>JSON.parse(JSON.stringify(x));
function campaign() {
  const state={turn:1,year:1465,season:'spring',armies:[
    {id:'kazakh_main',faction:'kazakh',commander:'kerei'},
    {id:'abulkhair_main',faction:'abulkhair',commander:'abulkhair'}
  ]};
  return P.initialize(state);
}
function battle(s) {
  return {id:'battle-1',commanders:s.armies.filter(a=>a.commander !== null).map(a=>({
    armyId:a.id,faction:a.faction,character:copy(P.getCharacter(s,a.commander))
  }))};
}
test('initial political state preserves persistent IDs, verified lineage, unknown dates and future rulers',()=>{
  const s=campaign();assert.equal(s.characters.length,5);assert.equal(P.getFaction(s,'kazakh').rulerId,'kerei');
  assert.deepEqual(P.getCharacter(s,'burunduk').parents,['kerei']);
  assert.deepEqual(P.getCharacter(s,'kasym').parents,['janibek']);
  assert.equal(P.getCharacter(s,'kasym').status,'reserve');
  assert.ok(s.characters.every(c=>c.birthYear===null));
  assert.equal(P.getCharacter(s,'abulkhair').dynastyId,null);
  assert.ok(P.validate(s));assert.deepEqual(campaign(),s);
});
test('initialization preserves existing political state and refuses partial state',()=>{
  const s=campaign();s.factions[0].authority=32;const before=copy(s);P.initialize(s);assert.deepEqual(s,before);
  assert.throws(()=>P.initialize({characters:[]}),/PARTIAL_STATE/);
});
test('simulation helper registers in SpiderMonkey-style host without Node dependencies',()=>{
  let exported;
  const context={Engine:{RegisterGlobal(name,value){assert.equal(name,'KtwPolitics');exported=value;}}};
  vm.createContext(context);vm.runInContext(fs.readFileSync(source,'utf8'),context);
  const s={turn:1,year:1465,season:'spring',armies:[]};exported.initialize(s);assert.equal(s.characters.length,5);
});
test('council report gives reconstructible numeric reasons and excludes future/current rulers',()=>{
  const s=campaign(),before=copy(s),c=P.describeCouncil(s,'kazakh');
  assert.equal(c.selectedCandidateId,'janibek');assert.deepEqual(s,before);
  assert.equal(c.candidates.find(x=>x.characterId==='kerei').exclusionReason,'current_ruler');
  assert.equal(c.candidates.find(x=>x.characterId==='kasym').exclusionReason,'reserve');
  for(const g of c.groups){
    assert.equal(g.supportsCharacterId,'janibek');
    for(const candidate of g.candidates){
      assert.equal(candidate.score,candidate.factors.reduce((n,x)=>n+x.points,0));
      assert.ok(candidate.factors.every(x=>x.points===x.value*x.weight));
    }
  }
});
test('different military/political abilities can produce explained disagreement between groups',()=>{
  const s=campaign(),k=P.getCharacter(s,'kasym');k.status='active';k.abilities.warfare=100;k.abilities.diplomacy=0;
  const report=P.describeCouncil(s,'kazakh');
  assert.equal(report.groups[0].supportsCharacterId,'janibek');
  assert.equal(report.groups[1].supportsCharacterId,'kasym');
  assert.equal(report.selectedCandidateId,'janibek');
  assert.equal(report.candidates.find(c=>c.characterId==='kasym').supportWeight,1);
});
test('commander death archives character, preserves family links and performs deterministic succession',()=>{
  const s=campaign(),b=battle(s),family=copy(P.getCharacter(s,'kerei').children);
  assert.deepEqual(P.onBattleResult(s,b,{commanderOutcomes:{kerei:'dead'}}),['kerei']);
  const dead=P.getCharacter(s,'kerei');assert.equal(dead.alive,false);assert.equal(dead.health,0);assert.equal(dead.status,'dead');
  assert.deepEqual(dead.children,family);assert.equal(dead.death.battleId,'battle-1');assert.equal(s.characters.length,5);
  assert.equal(P.getFaction(s,'kazakh').rulerId,'janibek');assert.equal(s.armies[0].commander,'janibek');
  assert.equal(P.getCharacter(s,'janibek').title,'khan');assert.equal(P.getFaction(s,'kazakh').authority,45);
  assert.deepEqual(s.politicalEvents.map(e=>e.type),['character_died','succession_completed','commander_reassigned']);
  const election=s.politicalEvents[1].data;assert.equal(election.reasonCode,'weighted_council_vote');
  assert.equal(election.council.rulerId,'kerei');assert.ok(P.validate(s));
});
test('replayed death is idempotent inside political module as well as in BattleBridge',()=>{
  const s=campaign(),b=battle(s),r={commanderOutcomes:{kerei:'dead'}};
  P.onBattleResult(s,b,r);const before=copy(s);assert.deepEqual(P.onBattleResult(s,b,r),[]);assert.deepEqual(s,before);
});
test('both deaths are processed before succession, vacancy never invents a replacement ruler',()=>{
  const s=campaign(),b=battle(s);P.onBattleResult(s,b,{commanderOutcomes:{kerei:'dead',abulkhair:'dead'}});
  assert.equal(P.getFaction(s,'abulkhair').rulerId,null);assert.equal(s.armies[1].commander,null);
  assert.equal(P.getFaction(s,'kazakh').rulerId,'janibek');
  const vacant=s.politicalEvents.find(e=>e.type==='succession_vacant');assert.equal(vacant.data.reasonCode,'no_eligible_successor');
  assert.equal(s.characters.length,5);assert.ok(P.validate(s));
});
test('surviving commander or absent outcomes leave all political data unchanged',()=>{
  const s=campaign(),b=battle(s),before=copy(s);P.onBattleResult(s,b,{});P.onBattleResult(s,b,{commanderOutcomes:{kerei:'alive'}});assert.deepEqual(s,before);
});
test('invalid or non-participating commander outcomes reject before any death is applied',()=>{
  for(const outcomes of [{kerei:'dead',kasym:'dead'},{kerei:'dead',abulkhair:'wounded'},null,[]]){
    const s=campaign(),b=battle(s),before=copy(s);assert.throws(()=>P.onBattleResult(s,b,{commanderOutcomes:outcomes}),/COMMANDER_OUTCOMES/);assert.deepEqual(s,before);
  }
});
test('dead characters cannot be resurrected by alive result or killed in a different battle',()=>{
  const s=campaign(),b=battle(s);P.onBattleResult(s,b,{commanderOutcomes:{kerei:'dead'}});const before=copy(s);
  assert.throws(()=>P.onBattleResult(s,b,{commanderOutcomes:{kerei:'alive'}}),/ALREADY_DEAD/);
  b.id='battle-2';assert.throws(()=>P.onBattleResult(s,b,{commanderOutcomes:{kerei:'dead'}}),/ALREADY_DEAD/);assert.deepEqual(s,before);
});
test('unknown, duplicated and nonreciprocal family/dynasty references fail validation',()=>{
  for(const corrupt of [
    s=>s.characters.push(copy(s.characters[0])),
    s=>P.getCharacter(s,'burunduk').parents.push('unknown'),
    s=>P.getCharacter(s,'kerei').children=[],
    s=>P.getCharacter(s,'kasym').spouses=['burunduk'],
    s=>s.dynasties[0].members=['kerei']
  ]){const s=campaign();corrupt(s);assert.throws(()=>P.validate(s),/KTW_POLITICS_/);}
});
test('ancestry cycle rejected even when parent/child references are reciprocal',()=>{
  const s=campaign();P.getCharacter(s,'kerei').parents=['burunduk'];P.getCharacter(s,'burunduk').children=['kerei'];
  assert.throws(()=>P.validate(s),/FAMILY_CYCLE/);
});
test('dead commanders/rulers, malformed reasons and duplicate event IDs fail validation',()=>{
  const s=campaign(),b=battle(s);P.onBattleResult(s,b,{commanderOutcomes:{kerei:'dead'}});
  const badCommander=copy(s);badCommander.armies[0].commander='kerei';assert.throws(()=>P.validate(badCommander),/COMMANDER/);
  const badRuler=copy(s);badRuler.factions[0].rulerId='kerei';assert.throws(()=>P.validate(badRuler),/RULER/);
  const badWeights=copy(s);badWeights.factions[0].politicalGroups[0].weights.warfare=NaN;assert.throws(()=>P.validate(badWeights),/GROUP_WEIGHTS/);
  const badEvents=copy(s);badEvents.politicalEvents.push(copy(s.politicalEvents[0]));assert.throws(()=>P.validate(badEvents),/EVENT/);
});
test('serialized political archive restores identical genealogy, election explanation and IDs',()=>{
  const s=campaign();P.onBattleResult(s,battle(s),{commanderOutcomes:{kerei:'dead'}});
  const restored=JSON.parse(JSON.stringify(s));assert.ok(P.validate(restored));assert.deepEqual(restored,s);
  assert.deepEqual(P.describeCouncil(restored,'kazakh'),P.describeCouncil(s,'kazakh'));
});
test('reported authority loss matches clamped actual loss',()=>{
  const s=campaign();P.getFaction(s,'kazakh').authority=5;P.onBattleResult(s,battle(s),{commanderOutcomes:{kerei:'dead'}});
  assert.equal(P.getFaction(s,'kazakh').authority,0);assert.equal(s.politicalEvents.find(e=>e.type==='succession_completed').data.authorityChange,-5);
});
