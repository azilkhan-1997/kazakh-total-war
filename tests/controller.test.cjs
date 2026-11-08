/* SPDX-License-Identifier: GPL-2.0-or-later
 * Mocked engine-integration tests of the actual KtwController source.
 * These prove controller/core contracts, not native rendering, binary save
 * compatibility, Windows acceptance or performance. Native QA is separate.
 */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const C = require(path.join(root, 'mods/kazakh_total_war/simulation/helpers/KtwCampaign.js'));
const source = fs.readFileSync(path.join(root, 'mods/kazakh_total_war/simulation/components/KtwController.js'), 'utf8');
const plain = x => JSON.parse(JSON.stringify(x));

function pending() {
  const s = C.create(1465);
  C.moveArmy(s, 'kazakh_main', 'sarysu');
  C.endTurn(s);
  assert.ok(s.pendingBattle);
  return s;
}

function harness(state = pending()) {
  const entities = new Map(), errors = [];
  let nextEntity = 1, registered, controller;
  function GuiInterface() {}
  GuiInterface.prototype.ScriptCall = () => 'upstream';
  const context = {
    KtwCampaign: C, GuiInterface, SYSTEM_ENTITY: 0, INVALID_ENTITY: -1,
    InitAttributes: {settings: null},
    QueryPlayerIDInterface: () => ({SetEnemy() {}}),
    error: message => errors.push(message),
    Engine: {
      RegisterSystemComponentType(iid, name, constructor) { registered = constructor; },
      AddEntity(template) {
        const id = nextEntity++;
        entities.set(id, {id, template, health:100, owner:0, x:0, z:0, angle:0, orders:[]});
        return id;
      },
      DestroyEntity(id) { entities.delete(id); },
      QueryInterface(id, iid) {
        if (id === 0) {
          if (iid === 'IID_KtwController') return controller;
          if (iid === 'IID_Timer') return {SetInterval() { return 7; }};
          if (iid === 'IID_RangeManager') return {SetLosRevealAll() {}};
        }
        const e = entities.get(id);
        if (!e) return null;
        if (iid === 'IID_Health') return {GetHitpoints: () => e.health};
        if (iid === 'IID_Position') return {
          JumpTo(x,z) { e.x=x; e.z=z; }, SetYRotation(a) { e.angle=a; },
          GetPosition2D: () => ({x:e.x, y:e.z}), IsInWorld: () => true
        };
        if (iid === 'IID_Ownership') return {SetOwner(owner) { e.owner=owner; }};
        if (iid === 'IID_UnitAI') return {
          SwitchToStance(stance) { e.stance=stance; },
          Walk(x,z,queued) { e.orders.push({type:'walk',x,z,queued}); },
          Attack(target,allowCapture,queued) { e.orders.push({type:'attack',target,allowCapture,queued}); }
        };
        if (iid === 'IID_UnitMotion') return {GetCurrentSpeed: () => 0, SetSpeedMultiplier(value) { e.speed=value; }};
        return null;
      }
    }
  };
  for (const iid of new Set(source.match(/\bIID_[A-Za-z0-9_]+\b/g))) context[iid]=iid;
  vm.createContext(context);
  vm.runInContext(source,context,{filename:'KtwController.js'});
  controller = new registered();
  controller.Init();
  controller.mode='battle';
  controller.state=state;
  return {controller, entities, errors, context};
}

test('mocked controller spawns exact 325-warrior roster and assigns commanders to existing soldiers', () => {
  const {controller:c, entities} = harness();
  c.BuildBattleScene();
  assert.equal(entities.size,325);
  assert.equal(c.units.length,325);
  assert.equal(c.commanders.length,2);
  assert.equal(new Set(c.commanders.map(x=>x.entity)).size,2);
  for (const commander of c.commanders) {
    const a = C.getArmy(c.state,commander.armyId);
    const unit = c.units.find(x=>x.entity===commander.entity);
    assert.equal(commander.characterId,a.commander);
    assert.ok(a.regiments.some(r=>r.id===unit.regimentId));
    assert.equal(entities.get(unit.entity).owner,a.faction==='kazakh'?1:2);
  }
  assert.equal(c.battleStats.kazakh,170);
  assert.equal(c.battleStats.abulkhair,155);
});

test('mocked real Health death reaches transactional campaign succession exactly once', () => {
  const {controller:c,entities} = harness();
  c.BuildBattleScene();
  const commander = c.commanders.find(x=>x.characterId==='kerei');
  entities.get(commander.entity).health=0;
  c.FinishBattle('kazakh');
  assert.equal(c.error,'');
  assert.equal(c.transition,'campaign');
  assert.equal(c.lastResult.commanderOutcomes.kerei,'dead');
  assert.equal(c.lastResult.commanderOutcomes.abulkhair,'alive');
  assert.equal(C.getCharacter(c.state,'kerei').alive,false);
  assert.equal(C.getFaction(c.state,'kazakh').rulerId,'janibek');
  assert.equal(C.getArmy(c.state,'kazakh_main').commander,'janibek');
  assert.equal(C.soldiers(C.getArmy(c.state,'kazakh_main')),169);
  assert.equal(C.soldiers(C.getArmy(c.state,'abulkhair_main')),155);
  assert.equal(c.state.resolvedBattles.length,1);
  const resolved = JSON.stringify(c.state);
  c.FinishBattle('kazakh');
  assert.equal(JSON.stringify(c.state),resolved);
  assert.equal(C.resolveBattle(c.state,plain(c.lastResult)).alreadyApplied,true);
  assert.equal(JSON.stringify(c.state),resolved);
});

test('mocked controller does not convert ordinary troop casualties into commander deaths', () => {
  const {controller:c,entities} = harness();
  c.BuildBattleScene();
  const commanderIds = new Set(c.commanders.map(x=>x.entity));
  const killed = c.units.filter(x=>!commanderIds.has(x.entity)).slice(0,4);
  killed.forEach(x=>entities.get(x.entity).health=0);
  c.FinishBattle('kazakh');
  assert.equal(c.error,'');
  assert.equal(c.lastResult.commanderOutcomes.kerei,'alive');
  assert.equal(c.lastResult.commanderOutcomes.abulkhair,'alive');
  assert.equal(C.getFaction(c.state,'kazakh').rulerId,'kerei');
  assert.equal(c.state.armies.reduce((n,a)=>n+C.soldiers(a),0),321);
});

test('schema-1 recorded midbattle snapshot upgrades without inventing commander entity history', () => {
  const recorded = JSON.parse(fs.readFileSync(path.join(root,'evidence/state-midbattle-before.json'),'utf8')).view;
  assert.equal(recorded.state.schemaVersion,1);
  const {controller:c} = harness(plain(recorded.state));
  delete c.commanders; // This field did not exist in v0.1 component saves.
  c.elapsed=recorded.battleStats.seconds;
  const originalRoster=JSON.stringify(c.state.armies);
  c.OnDeserialized();
  assert.equal(c.error,'');
  assert.equal(c.state.schemaVersion,2);
  assert.equal(JSON.stringify(c.state.armies),originalRoster);
  assert.equal(c.state.pendingBattle.id,recorded.state.pendingBattle.id);
  assert.equal(c.elapsed,recorded.battleStats.seconds);
  assert.deepEqual(plain(c.commanders),[]);
  assert.ok(c.state.characters.every(x=>x.alive));
  // Engine binary serialization must keep its v0.1 default component shape.
  assert.equal(c.Serialize,undefined);
  assert.equal(c.Deserialize,undefined);
});

test('malformed recorded old save stays untouched and blocks commands and battle ticks', () => {
  const recorded=JSON.parse(fs.readFileSync(path.join(root,'evidence/state-midbattle-before.json'),'utf8')).view.state;
  recorded.armies[0].regiments[0].count=-1;
  const {controller:c,errors}=harness(recorded);
  const before=JSON.stringify(c.state), elapsed=c.elapsed;
  c.OnDeserialized();
  assert.match(c.error,/^KTW_LOAD_RECOVERY_REQUIRED/);
  assert.equal(errors.length,1);
  assert.equal(JSON.stringify(c.state),before);
  c.Command(1,{action:'surrender'});
  c.Tick();
  assert.equal(JSON.stringify(c.state),before);
  assert.equal(c.elapsed,elapsed);
  assert.equal(c.transition,null);
});

test('rejected battle completion preserves pending state and can retry with corrected outcome', () => {
  const {controller:c}=harness();
  c.BuildBattleScene();
  const before=JSON.stringify(c.state), entities=JSON.stringify(c.units);
  c.FinishBattle('unknown-faction');
  assert.match(c.error,/KTW_/);
  assert.equal(c.transition,null);
  assert.equal(c.lastResult,null);
  assert.equal(JSON.stringify(c.state),before);
  assert.equal(JSON.stringify(c.units),entities);
  c.Command(1,{action:'surrender'});
  assert.equal(c.error,'');
  assert.equal(c.transition,'campaign');
  assert.equal(c.state.pendingBattle,null);
});

test('GUI gateway exposes simulation council and Health-based commander status without mutating campaign', () => {
  const {controller:c,context,entities}=harness();
  c.BuildBattleScene();
  const first=c.commanders[0];
  entities.get(first.entity).health=0;
  const before=JSON.stringify(c.state);
  const view=(new context.GuiInterface()).ScriptCall(1,'KtwGetState',{});
  assert.equal(view.council.rulerId,'kerei');
  assert.equal(view.commanders.find(x=>x.characterId===first.characterId).alive,false);
  assert.equal(JSON.stringify(c.state),before);
  assert.equal((new context.GuiInterface()).ScriptCall(1,'OtherEngineCall',{}),'upstream');
});

test('schema-2 commander mapping corruption is rejected atomically for wrong side, duplicate and absent identity', () => {
  const corruptions = [
    c => { c.commanders[0].entity=c.commanders[1].entity; },
    c => { c.commanders[1]=plain(c.commanders[0]); },
    c => { c.commanders[0].entity=999999; }
  ];
  for (const corrupt of corruptions) {
    const {controller:c,errors}=harness();
    c.BuildBattleScene();
    corrupt(c);
    const state=JSON.stringify(c.state), mappings=JSON.stringify(c.commanders);
    c.OnDeserialized();
    assert.match(c.error,/^KTW_LOAD_RECOVERY_REQUIRED: KTW_SAVE_COMMANDER_ENTITIES$/);
    assert.equal(errors.length,1);
    assert.equal(JSON.stringify(c.state),state);
    assert.equal(JSON.stringify(c.commanders),mappings);
    c.Tick();
    c.Command(1,{action:'surrender'});
    assert.equal(JSON.stringify(c.state),state);
    assert.equal(c.transition,null);
  }
});

test('schema-2 valid dead commander mapping restores even after engine removes its Health entity', () => {
  const {controller:c,entities}=harness();
  c.BuildBattleScene();
  const commander=c.commanders.find(x=>x.characterId==='kerei');
  entities.delete(commander.entity);
  const state=JSON.stringify(c.state), mappings=JSON.stringify(c.commanders);
  c.OnDeserialized();
  assert.equal(c.error,'');
  assert.equal(JSON.stringify(c.state),state);
  assert.equal(JSON.stringify(c.commanders),mappings);
  assert.equal(c.GetState().commanders.find(x=>x.characterId==='kerei').alive,false);
  c.FinishBattle('kazakh');
  assert.equal(c.error,'');
  assert.equal(c.lastResult.commanderOutcomes.kerei,'dead');
  assert.equal(C.getFaction(c.state,'kazakh').rulerId,'janibek');
});

test('schema-2 political corruption leaves recovery GUI readable without calculating council', () => {
  const {controller:c}=harness();
  delete c.state.characters;
  const state=JSON.stringify(c.state);
  c.OnDeserialized();
  assert.match(c.error,/^KTW_LOAD_RECOVERY_REQUIRED/);
  const view=c.GetState();
  assert.equal(view.council,null);
  assert.match(view.error,/^KTW_LOAD_RECOVERY_REQUIRED/);
  assert.equal(JSON.stringify(c.state),state);
});
