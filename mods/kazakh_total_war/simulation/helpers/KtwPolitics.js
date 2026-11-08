/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright (c) 2026 SAYRAM PLANETA HOLDING contributors.
 * Persistent characters and a small, explainable succession model.
 * Council groups, influence, abilities and election weights are gameplay rules,
 * not a reconstruction of the membership or constitution of a 1465 qurultay.
 */
var KtwPolitics = (function() {
"use strict";
function clone(x) { return JSON.parse(JSON.stringify(x)); }
function fail(code) { throw new Error('KTW_POLITICS_' + code); }
function integer(x, min, max) { return Number.isInteger(x) && x >= min && x <= max; }
function id(x) { return typeof x === 'string' && /^[a-z][a-z0-9_]*$/.test(x); }
function owns(x, key) { return Object.prototype.hasOwnProperty.call(x, key); }
function getCharacter(s, key) { return s.characters.find(function(c) { return c.id === key; }); }
function getFaction(s, key) { return s.factions.find(function(f) { return f.id === key; }); }
function names(ru, kk, en) { return {ru:ru, kk:kk, en:en}; }
function character(key, name, faction, dynasty, role, status, sources) {
  return {id:key, name:name, factionId:faction, dynastyId:dynasty, parents:[], children:[], spouses:[],
    birthYear:null, historicalPeriod:'15th-early16th-century', alive:true, health:100,
    status:status, title:role === 'khan' || role === 'rival_khan' ? 'khan' : role === 'cofounder' ? 'cofounder' : 'sultan',
    roleAtStart:role, abilities:{leadership:50, warfare:50, diplomacy:50}, traits:[],
    militaryExperience:0, relationships:{}, death:null, sourceIds:sources,
    statisticsBasis:'gameplay_placeholder'};
}
function groups(faction) {
  return [
    {id:faction+'_council', name:names('\u0421\u043e\u0432\u0435\u0442','\u041a\u0435\u04a3\u0435\u0441','Council'), influence:2,
      weights:{leadership:2, warfare:0, diplomacy:1, cofounder:25, ruling_dynasty:10}},
    {id:faction+'_commanders', name:names('\u0412\u043e\u0435\u043d\u0430\u0447\u0430\u043b\u044c\u043d\u0438\u043a\u0438','\u049a\u043e\u043b\u0431\u0430\u0441\u0448\u044b\u043b\u0430\u0440','Commanders'), influence:1,
      weights:{leadership:1, warfare:2, diplomacy:0, cofounder:10, ruling_dynasty:0}}
  ];
}
function initialize(s) {
  var fields = ['characters','factions','dynasties','politicalEvents','nextPoliticalEventId'];
  if (fields.some(function(key) { return owns(s,key); })) {
    if (!fields.every(function(key) { return owns(s,key); })) fail('PARTIAL_STATE');
    validate(s); return s;
  }
  s.characters = [
    character('kerei',names('\u041a\u0435\u0440\u0435\u0439 \u0445\u0430\u043d','\u041a\u0435\u0440\u0435\u0439 \u0445\u0430\u043d','Kerei Khan'),'kazakh','kerei_line','khan','active',['H5']),
    character('janibek',names('\u0416\u0430\u043d\u0438\u0431\u0435\u043a','\u0416\u04d9\u043d\u0456\u0431\u0435\u043a','Janibek'),'kazakh','janibek_line','cofounder','active',['H1','H5']),
    character('burunduk',names('\u0411\u0443\u0440\u0443\u043d\u0434\u0443\u043a','\u0411\u04b1\u0440\u044b\u043d\u0434\u044b\u049b','Burunduk'),'kazakh','kerei_line','not_deployed','reserve',['H3']),
    character('kasym',names('\u041a\u0430\u0441\u044b\u043c','\u049a\u0430\u0441\u044b\u043c','Kasym'),'kazakh','janibek_line','not_deployed','reserve',['H4']),
    character('abulkhair',names('\u0410\u0431\u0443\u043b\u0445\u0430\u0438\u0440 \u0445\u0430\u043d','\u04d8\u0431\u0456\u043b\u049b\u0430\u0439\u044b\u0440 \u0445\u0430\u043d','Abulkhair Khan'),'abulkhair',null,'rival_khan','active',['H2'])
  ];
  getCharacter(s,'kerei').children = ['burunduk'];
  getCharacter(s,'burunduk').parents = ['kerei'];
  getCharacter(s,'janibek').children = ['kasym'];
  getCharacter(s,'kasym').parents = ['janibek'];
  s.dynasties = [
    {id:'kerei_line', name:names('\u041b\u0438\u043d\u0438\u044f \u041a\u0435\u0440\u0435\u044f','\u041a\u0435\u0440\u0435\u0439 \u04d9\u0443\u043b\u0435\u0442\u0456','Kerei lineage'), members:['kerei','burunduk'], sourceIds:['H3'], classification:'lineage_archive'},
    {id:'janibek_line', name:names('\u041b\u0438\u043d\u0438\u044f \u0416\u0430\u043d\u0438\u0431\u0435\u043a\u0430','\u0416\u04d9\u043d\u0456\u0431\u0435\u043a \u04d9\u0443\u043b\u0435\u0442\u0456','Janibek lineage'), members:['janibek','kasym'], sourceIds:['H4'], classification:'lineage_archive'}
  ];
  s.factions = [
    {id:'kazakh', rulerId:'kerei', authority:60, politicalGroups:groups('kazakh')},
    {id:'abulkhair', rulerId:'abulkhair', authority:60, politicalGroups:groups('abulkhair')}
  ];
  s.politicalEvents = [];
  s.nextPoliticalEventId = 1;
  validate(s); return s;
}
function validate(s) {
  if (!Array.isArray(s.characters) || !s.characters.length || s.characters.length > 10000 ||
      !Array.isArray(s.factions) || !s.factions.length || !Array.isArray(s.dynasties) ||
      !Array.isArray(s.politicalEvents) || !integer(s.nextPoliticalEventId,1,10000000)) fail('STATE');
  var cids = new Set(), fids = new Set(), dids = new Set(), gids = new Set();
  s.characters.forEach(function(c) { if (!c || !id(c.id) || cids.has(c.id)) fail('CHARACTER_ID'); cids.add(c.id); });
  s.factions.forEach(function(f) { if (!f || !id(f.id) || fids.has(f.id)) fail('FACTION_ID'); fids.add(f.id); });
  s.dynasties.forEach(function(d) { if (!d || !id(d.id) || dids.has(d.id)) fail('DYNASTY_ID'); dids.add(d.id); });
  function checkNames(x) {
    if (!x || ['ru','kk','en'].some(function(lang) { return typeof x[lang] !== 'string' || !x[lang].length || x[lang].length > 120; })) fail('NAME');
  }
  function references(list, valid, error, ownId) {
    if (!Array.isArray(list) || new Set(list).size !== list.length || list.some(function(key) { return !valid.has(key) || key === ownId; })) fail(error);
  }
  s.characters.forEach(function(c) {
    checkNames(c.name);
    if (!fids.has(c.factionId) || (c.dynastyId !== null && !dids.has(c.dynastyId)) ||
        typeof c.alive !== 'boolean' || !['active','reserve','dead'].includes(c.status) ||
        (c.status === 'dead') !== !c.alive || !integer(c.health,0,100) || (c.health === 0) !== !c.alive ||
        (c.birthYear !== null && !integer(c.birthYear,1,s.year)) || !integer(c.militaryExperience,0,100000)) fail('CHARACTER');
    if (typeof c.title !== 'string' || typeof c.roleAtStart !== 'string' || !c.abilities ||
        ['leadership','warfare','diplomacy'].some(function(key) { return !integer(c.abilities[key],0,100); }) ||
        !Array.isArray(c.traits) || c.traits.some(function(x) { return typeof x !== 'string'; })) fail('CHARACTER_ATTRIBUTES');
    references(c.parents,cids,'PARENTS',c.id); references(c.children,cids,'CHILDREN',c.id); references(c.spouses,cids,'SPOUSES',c.id);
    if (c.parents.length > 2) fail('PARENTS');
    c.parents.forEach(function(key) { if (!getCharacter(s,key).children.includes(c.id)) fail('FAMILY_RECIPROCITY'); });
    c.children.forEach(function(key) { if (!getCharacter(s,key).parents.includes(c.id)) fail('FAMILY_RECIPROCITY'); });
    c.spouses.forEach(function(key) { if (!getCharacter(s,key).spouses.includes(c.id)) fail('FAMILY_RECIPROCITY'); });
    if (!c.relationships || typeof c.relationships !== 'object' || Array.isArray(c.relationships)) fail('RELATIONSHIPS');
    Object.keys(c.relationships).forEach(function(key) { if (!cids.has(key) || key === c.id || !integer(c.relationships[key],-100,100)) fail('RELATIONSHIPS'); });
    if (c.alive ? c.death !== null : !c.death || !integer(c.death.turn,1,s.turn) || !integer(c.death.year,1465,s.year) ||
        !['spring','summer','autumn','winter'].includes(c.death.season) || !/^battle-[1-9]\d*$/.test(c.death.battleId) || c.death.cause !== 'battle') fail('DEATH');
  });
  // Acyclic family ancestry is checked independently of reciprocal links.
  var visiting = new Set(), visited = new Set();
  function visit(key) {
    if (visiting.has(key)) fail('FAMILY_CYCLE');
    if (visited.has(key)) return;
    visiting.add(key); getCharacter(s,key).parents.forEach(visit); visiting.delete(key); visited.add(key);
  }
  cids.forEach(visit);
  s.dynasties.forEach(function(d) {
    checkNames(d.name); references(d.members,cids,'DYNASTY_MEMBERS',null);
    d.members.forEach(function(key) { if (getCharacter(s,key).dynastyId !== d.id) fail('DYNASTY_RECIPROCITY'); });
  });
  s.characters.forEach(function(c) {
    if (c.dynastyId !== null && !s.dynasties.find(function(d) { return d.id === c.dynastyId; }).members.includes(c.id)) fail('DYNASTY_RECIPROCITY');
  });
  s.factions.forEach(function(f) {
    var ruler = f.rulerId === null ? null : getCharacter(s,f.rulerId);
    if (f.rulerId !== null && (!ruler || ruler.factionId !== f.id || !ruler.alive || ruler.status !== 'active')) fail('RULER');
    if (!integer(f.authority,0,100) || !Array.isArray(f.politicalGroups) || f.politicalGroups.length > 20) fail('FACTION');
    f.politicalGroups.forEach(function(g) {
      if (!g || !id(g.id) || gids.has(g.id) || !integer(g.influence,1,100) || !g.weights) fail('GROUP');
      gids.add(g.id); checkNames(g.name);
      if (['leadership','warfare','diplomacy','cofounder','ruling_dynasty'].some(function(key) { return !integer(g.weights[key],0,100); })) fail('GROUP_WEIGHTS');
    });
  });
  (s.armies || []).forEach(function(a) {
    var commander = a.commander === null ? null : getCharacter(s,a.commander);
    if (a.commander !== null && (!commander || !commander.alive || commander.status !== 'active' || commander.factionId !== a.faction)) fail('COMMANDER');
  });
  var eids = new Set();
  s.politicalEvents.forEach(function(e) {
    if (!e || typeof e.id !== 'string' || !/^politics-[1-9]\d*$/.test(e.id) || eids.has(e.id) ||
        Number(e.id.slice(9)) >= s.nextPoliticalEventId || !integer(e.turn,1,s.turn) || !integer(e.year,1465,s.year) ||
        !['spring','summer','autumn','winter'].includes(e.season) || typeof e.type !== 'string' || !e.data || typeof e.data !== 'object') fail('EVENT');
    eids.add(e.id);
  });
  return true;
}
function candidateReason(c, f) {
  if (!c.alive) return 'dead';
  if (c.status !== 'active') return 'reserve';
  if (c.id === f.rulerId) return 'current_ruler';
  return null;
}
function describeCouncil(s, factionId) {
  var f = getFaction(s,factionId);
  if (!f) fail('FACTION');
  var ruler = f.rulerId === null ? null : getCharacter(s,f.rulerId);
  var candidates = s.characters.filter(function(c) { return c.factionId === factionId; }).map(function(c) {
    var exclusion = candidateReason(c,f);
    return {characterId:c.id, eligible:exclusion === null, exclusionReason:exclusion, totalScore:0, supportWeight:0};
  });
  var results = f.politicalGroups.map(function(g) {
    var scores = candidates.filter(function(c) { return c.eligible; }).map(function(candidate) {
      var c = getCharacter(s,candidate.characterId);
      var values = {leadership:c.abilities.leadership, warfare:c.abilities.warfare, diplomacy:c.abilities.diplomacy,
        cofounder:c.roleAtStart === 'cofounder' ? 1 : 0, ruling_dynasty:ruler && ruler.dynastyId !== null && ruler.dynastyId === c.dynastyId ? 1 : 0};
      var factors = Object.keys(values).map(function(key) { return {code:key, value:values[key], weight:g.weights[key], points:values[key]*g.weights[key]}; });
      var score = factors.reduce(function(total,x) { return total+x.points; },0);
      candidate.totalScore += score*g.influence;
      return {characterId:c.id, score:score, factors:factors};
    });
    scores.sort(function(a,b) { return b.score-a.score || (a.characterId < b.characterId ? -1 : a.characterId > b.characterId ? 1 : 0); });
    var supported = scores.length ? scores[0].characterId : null;
    if (supported !== null) candidates.find(function(c) { return c.characterId === supported; }).supportWeight += g.influence;
    return {id:g.id, name:clone(g.name), influence:g.influence, supportsCharacterId:supported, candidates:scores};
  });
  var eligible = candidates.filter(function(c) { return c.eligible; });
  eligible.sort(function(a,b) { return b.supportWeight-a.supportWeight || b.totalScore-a.totalScore ||
    (a.characterId < b.characterId ? -1 : a.characterId > b.characterId ? 1 : 0); });
  return {factionId:factionId, rulerId:f.rulerId, rule:'weighted_council_v1',
    ruleBasis:'gameplay_abstraction', tieBreak:'support_weight_then_weighted_score_then_character_id',
    groups:results, candidates:candidates, selectedCandidateId:eligible.length ? eligible[0].characterId : null};
}
function event(s, type, data) {
  var e = {id:'politics-'+s.nextPoliticalEventId++,turn:s.turn,year:s.year,season:s.season,type:type,data:clone(data)};
  s.politicalEvents.push(e); return e;
}
function onBattleResult(s, battle, result) {
  var outcomes = result.commanderOutcomes === undefined ? {} : result.commanderOutcomes;
  if (!outcomes || typeof outcomes !== 'object' || Array.isArray(outcomes)) fail('COMMANDER_OUTCOMES');
  var snapshots = battle.commanders || [];
  var deaths = [];
  // This module is run on BattleBridge's private candidate state. Reject the
  // complete outcome set before touching it; the caller commits only on success.
  Object.keys(outcomes).sort().forEach(function(key) {
    var snap = snapshots.find(function(x) { return x.character && x.character.id === key; });
    var c = getCharacter(s,key);
    if (!snap || !c || c.factionId !== snap.faction || !['alive','dead'].includes(outcomes[key])) fail('COMMANDER_OUTCOMES');
    if (outcomes[key] === 'dead') {
      if (!c.alive && c.death && c.death.battleId === battle.id) return;
      if (!c.alive || !snap.character.alive) fail('COMMANDER_ALREADY_DEAD');
      deaths.push(c);
    } else if (!c.alive) fail('COMMANDER_ALREADY_DEAD');
  });
  var affected = new Set();
  deaths.forEach(function(c) {
    c.alive = false; c.status = 'dead'; c.health = 0;
    c.death = {turn:s.turn,year:s.year,season:s.season,battleId:battle.id,cause:'battle'};
    affected.add(c.factionId);
    event(s,'character_died',{characterId:c.id,factionId:c.factionId,battleId:battle.id,reasonCode:'confirmed_battle_death'});
  });
  Array.from(affected).sort().forEach(function(factionId) {
    var f = getFaction(s,factionId), previous = f.rulerId === null ? null : getCharacter(s,f.rulerId);
    if (previous && !previous.alive) {
      // Preserve the previous ruler until scoring is complete, so lineage
      // continuity is evaluated against the deceased ruler, not the new one.
      var council = describeCouncil(s,factionId);
      f.rulerId = council.selectedCandidateId;
      var authorityBefore = f.authority;
      f.authority = Math.max(0,f.authority-15);
      if (f.rulerId !== null) getCharacter(s,f.rulerId).title = 'khan';
      event(s,f.rulerId === null ? 'succession_vacant' : 'succession_completed',{
        factionId:factionId,battleId:battle.id,previousRulerId:previous.id,rulerId:f.rulerId,
        reasonCode:f.rulerId === null ? 'no_eligible_successor' : 'weighted_council_vote',
        authorityChange:f.authority-authorityBefore,council:council
      });
    }
    (s.armies || []).filter(function(a) { return a.faction === factionId; }).forEach(function(a) {
      if (a.commander !== null && !getCharacter(s,a.commander).alive) {
        var old = a.commander;
        a.commander = f.rulerId;
        event(s,'commander_reassigned',{armyId:a.id,factionId:factionId,battleId:battle.id,
          characterId:a.commander,previousCommanderId:old,reasonCode:a.commander === null ? 'no_eligible_commander' : 'ruler_takes_command'});
      }
    });
  });
  return deaths.map(function(c) { return c.id; });
}
return {initialize:initialize,validate:validate,onBattleResult:onBattleResult,describeCouncil:describeCouncil,
  getCharacter:getCharacter,getFaction:getFaction};
})();
if (typeof module !== 'undefined' && module.exports) module.exports = KtwPolitics;
if (typeof Engine !== 'undefined') Engine.RegisterGlobal('KtwPolitics', KtwPolitics);
