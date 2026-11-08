/* SPDX-License-Identifier: GPL-2.0-or-later
 * Battle transfer contracts. No renderer, GUI, file system or random calls.
 */
var KtwBattleBridge = (function() {
"use strict";
function fail(code) { throw new Error('KTW_' + code); }
function clone(value) { return JSON.parse(JSON.stringify(value)); }
function owns(value, key) { return Object.prototype.hasOwnProperty.call(value, key); }
function weather(season) { return season === 'winter' ? 'snow' : 'clear'; }
function enrichSnapshot(state, battle) {
  battle.bridgeVersion = 2;
  battle.currentDate = { year: state.year, season: state.season, turn: state.turn };
  battle.weather = weather(state.season);
  battle.battleType = 'field';
  battle.reinforcements = [];
  battle.commanders = [];
  battle.armies.forEach(function(army) {
    if (army.commander === null) return;
    var character = state.characters.find(function(c) { return c.id === army.commander; });
    if (!character || !character.alive || character.factionId !== army.faction) fail('BATTLE_COMMANDER');
    battle.commanders.push({ armyId: army.id, faction: army.faction, character: clone(character) });
  });
  return battle;
}
function validateSnapshot(state, battle) {
  if (!battle) return true;
  var province = state.provinces.find(function(p) { return p.id === battle.provinceId; });
  var attacker = battle.armies.find(function(a) { return a.id === battle.attackerId; });
  var defender = battle.armies.find(function(a) { return a.id === battle.defenderId; });
  var origin = attacker && state.provinces.find(function(p) { return p.id === attacker.province; });
  if (!province || !attacker || !defender || !origin || battle.terrain !== province.terrain ||
      battle.attackerOrigin !== attacker.province || battle.defenderOrigin !== defender.province ||
      defender.province !== battle.provinceId || !origin.adjacent.includes(battle.provinceId) ||
      attacker.movement !== 0 || state.relation !== 'war') fail('SAVE_BATTLE_GEOGRAPHY');
  if (battle.bridgeVersion !== 2 || !battle.currentDate || battle.currentDate.year !== state.year || battle.currentDate.season !== state.season || battle.currentDate.turn !== state.turn || battle.turn !== state.turn || battle.season !== state.season || battle.weather !== weather(state.season) || battle.battleType !== 'field' || !Array.isArray(battle.reinforcements) || battle.reinforcements.length) fail('SAVE_BATTLE_CONTEXT');
  var expected = enrichSnapshot(state, { armies: battle.armies }).commanders;
  if (!Array.isArray(battle.commanders) || JSON.stringify(expected) !== JSON.stringify(battle.commanders)) fail('SAVE_BATTLE_COMMANDERS');
  return true;
}
function outcomes(result) {
  if (result.commanderOutcomes === undefined) return {};
  var value = result.commanderOutcomes;
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail('RESULT_COMMANDERS');
  Object.keys(value).forEach(function(id) {
    if (!/^[a-z][a-z0-9_]*$/.test(id) || !['alive', 'dead'].includes(value[id])) fail('RESULT_COMMANDERS');
  });
  return value;
}
function signature(result) {
  var value = { battleId: result.battleId, winner: result.winner,
    survivors: Object.keys(result.survivors || {}).sort().map(function(id) { return [id, result.survivors[id]]; }) };
  // An omitted outcome means no reported death. Explicitly alive therefore has
  // the same signature as the legacy result, preserving schema 1 receipts.
  var changes = outcomes(result);
  var deaths = Object.keys(changes).filter(function(id) { return changes[id] === 'dead'; }).sort();
  if (deaths.length) value.deadCommanders = deaths;
  return JSON.stringify(value);
}
function validateResult(state, result) {
  if (!result || typeof result !== 'object' || typeof result.battleId !== 'string' || !/^battle-[1-9]\d*$/.test(result.battleId) || !['kazakh', 'abulkhair', 'draw'].includes(result.winner) || !result.survivors || typeof result.survivors !== 'object' || Array.isArray(result.survivors)) fail('INVALID_RESULT');
  var reported = outcomes(result);
  var digest = signature(result);
  var prior = state.resolvedBattles.find(function(x) { return x.id === result.battleId; });
  if (prior) {
    if (prior.signature !== digest) fail('CONFLICTING_RESULT');
    var priorCommanders = prior.commanderIds || state.characters.map(function(c) { return c.id; });
    if (Object.keys(reported).some(function(id) { return !priorCommanders.includes(id); })) fail('RESULT_COMMANDERS');
    return { alreadyApplied: true, battleId: result.battleId, signature: digest };
  }
  var battle = state.pendingBattle;
  if (!battle || battle.id !== result.battleId) fail('STALE_RESULT');
  var all = [];
  battle.armies.forEach(function(army) { army.regiments.forEach(function(r) { all.push(r); }); });
  if (Object.keys(result.survivors).length !== all.length) fail('RESULT_ROSTER');
  all.forEach(function(r) {
    if (!owns(result.survivors, r.id) || !Number.isInteger(result.survivors[r.id]) || result.survivors[r.id] < 0 || result.survivors[r.id] > r.count) fail('RESULT_SURVIVORS');
  });
  if (result.winner !== 'draw') {
    var winner = battle.armies.find(function(a) { return a.faction === result.winner; });
    if (!winner || !winner.regiments.some(function(r) { return result.survivors[r.id] > 0; })) fail('RESULT_WINNER');
  }
  Object.keys(reported).forEach(function(id) {
    var commander = battle.commanders.find(function(c) { return c.character.id === id; });
    if (!commander) fail('RESULT_COMMANDERS');
    if (reported[id] === 'dead') {
      var army = battle.armies.find(function(a) { return a.id === commander.armyId; });
      if (!army.regiments.some(function(r) { return result.survivors[r.id] < r.count; })) fail('RESULT_COMMANDER_WITHOUT_CASUALTY');
    }
  });
  return { alreadyApplied: false, battleId: result.battleId, signature: digest };
}
return { enrichSnapshot: enrichSnapshot, validateSnapshot: validateSnapshot, validateResult: validateResult, signature: signature };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = KtwBattleBridge;
if (typeof Engine !== 'undefined') Engine.RegisterGlobal('KtwBattleBridge', KtwBattleBridge);
