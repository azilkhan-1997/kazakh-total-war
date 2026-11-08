/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright (c) 2026 SAYRAM PLANETA HOLDING contributors.
 * Deterministic simulation-only campaign; schematic historical setting.
 */
var KtwCampaign = (function() {
"use strict";
var DATA = {"campaignId":"great_steppe_1465_slice","startYear":1465,"notice":{"ru":"\u041e\u043a\u043e\u043b\u043e 1465 \u0433\u043e\u0434\u0430. \u0418\u0441\u0442\u043e\u0440\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u043c\u0435\u0441\u0442\u0430, \u0443\u0441\u043b\u043e\u0432\u043d\u044b\u0435 \u0433\u0440\u0430\u043d\u0438\u0446\u044b \u0438 \u0438\u0433\u0440\u043e\u0432\u0430\u044f \u0440\u0430\u0441\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430 \u0441\u0438\u043b. \u0421\u043e\u0431\u044b\u0442\u0438\u044f \u043f\u043e\u0441\u043b\u0435 \u043d\u0430\u0447\u0430\u043b\u0430 \u0437\u0430\u0432\u0438\u0441\u044f\u0442 \u043e\u0442 \u0438\u0433\u0440\u043e\u043a\u0430.","kk":"\u0428\u0430\u043c\u0430\u043c\u0435\u043d 1465 \u0436\u044b\u043b. \u0422\u0430\u0440\u0438\u0445\u0438 \u043e\u0440\u044b\u043d\u0434\u0430\u0440, \u0448\u0430\u0440\u0442\u0442\u044b \u0448\u0435\u043a\u0430\u0440\u0430\u043b\u0430\u0440 \u0436\u04d9\u043d\u0435 \u043e\u0439\u044b\u043d\u0493\u0430 \u0431\u0435\u0439\u0456\u043c\u0434\u0435\u043b\u0433\u0435\u043d \u043a\u04af\u0448\u0442\u0435\u0440. \u041e\u049b\u0438\u0493\u0430\u043b\u0430\u0440\u0434\u044b\u04a3 \u0431\u0430\u0440\u044b\u0441\u044b \u043e\u0439\u044b\u043d\u0448\u044b\u0493\u0430 \u0431\u0430\u0439\u043b\u0430\u043d\u044b\u0441\u0442\u044b.","en":"Around 1465. Historical places, schematic borders and forces arranged for gameplay. Events after the start depend on the player."},"factions":[{"id":"kazakh","name":{"ru":"\u041a\u0430\u0437\u0430\u0445\u0441\u043a\u043e\u0435 \u0445\u0430\u043d\u0441\u0442\u0432\u043e","kk":"\u049a\u0430\u0437\u0430\u049b \u0445\u0430\u043d\u0434\u044b\u0493\u044b","en":"Kazakh Khanate"},"leader":"kerei","cofounder":"janibek","startingArmyProvince":"shu","sourceIds":["H1","H5"]},{"id":"abulkhair","name":{"ru":"\u0413\u043e\u0441\u0443\u0434\u0430\u0440\u0441\u0442\u0432\u043e \u0410\u0431\u0443\u043b\u0445\u0430\u0438\u0440\u0430","kk":"\u04d8\u0431\u0456\u043b\u049b\u0430\u0439\u044b\u0440 \u0445\u0430\u043d\u0434\u044b\u0493\u044b","en":"Abulkhair\u2019s state"},"leader":"abulkhair","startingArmyProvince":"sygnak","sourceIds":["H2"]}],"provinces":[{"id":"shu","name":{"ru":"\u0427\u0443\u0439\u0441\u043a\u0430\u044f \u0434\u043e\u043b\u0438\u043d\u0430","kk":"\u0428\u0443 \u0430\u04a3\u0493\u0430\u0440\u044b","en":"Shu valley"},"mapPosition":{"x":0.8889,"z":0.7143,"coordinateSystem":"normalized 0..1; x east, z south"},"terrain":"river_steppe","initialOwner":"kazakh","adjacent":["talas","sarysu"],"settlement":{"name":{"ru":"\u0417\u0438\u043c\u043e\u0432\u043a\u0430 \u0432 \u0434\u043e\u043b\u0438\u043d\u0435 \u0428\u0443","kk":"\u0428\u0443 \u0430\u04a3\u0493\u0430\u0440\u044b\u043d\u0434\u0430\u0493\u044b \u049b\u044b\u0441\u0442\u0430\u0443","en":"Shu winter camp"},"kind":"nomadic_camp"}},{"id":"talas","name":{"ru":"\u0422\u0430\u043b\u0430\u0441\u0441\u043a\u0430\u044f \u0434\u043e\u043b\u0438\u043d\u0430","kk":"\u0422\u0430\u043b\u0430\u0441 \u0430\u04a3\u0493\u0430\u0440\u044b","en":"Talas valley"},"mapPosition":{"x":0.6296,"z":0.8286,"coordinateSystem":"normalized 0..1; x east, z south"},"terrain":"foothill_steppe","initialOwner":"kazakh","adjacent":["shu","suzak","otrar"],"settlement":{"name":{"ru":"\u041a\u043e\u0447\u0435\u0432\u044c\u0435 \u0443 \u0422\u0430\u043b\u0430\u0441\u0430","kk":"\u0422\u0430\u043b\u0430\u0441 \u0431\u043e\u0439\u044b\u043d\u0434\u0430\u0493\u044b \u049b\u043e\u043d\u044b\u0441","en":"Talas encampment"},"kind":"nomadic_camp"}},{"id":"sarysu","name":{"ru":"\u0421\u0430\u0440\u044b\u0441\u0443","kk":"\u0421\u0430\u0440\u044b\u0441\u0443","en":"Sarysu"},"mapPosition":{"x":0.3951,"z":0.1714,"coordinateSystem":"normalized 0..1; x east, z south"},"terrain":"dry_steppe","initialOwner":"abulkhair","adjacent":["shu","suzak","sygnak"],"settlement":{"name":{"ru":"\u0421\u0442\u0435\u043f\u043d\u0430\u044f \u0441\u0442\u0430\u0432\u043a\u0430","kk":"\u0414\u0430\u043b\u0430 \u043e\u0440\u0434\u0430\u0441\u044b","en":"Steppe camp"},"kind":"nomadic_camp"}},{"id":"suzak","name":{"ru":"\u0421\u0443\u0437\u0430\u043a","kk":"\u0421\u043e\u0437\u0430\u049b","en":"Suzak"},"mapPosition":{"x":0.2716,"z":0.4571,"coordinateSystem":"normalized 0..1; x east, z south"},"terrain":"foothills","initialOwner":"abulkhair","adjacent":["talas","sarysu","sygnak","sauran","yasy"],"settlement":{"name":{"ru":"\u0421\u0443\u0437\u0430\u043a","kk":"\u0421\u043e\u0437\u0430\u049b","en":"Suzak"},"kind":"fortified_town"}},{"id":"sygnak","name":{"ru":"\u0421\u044b\u0433\u043d\u0430\u043a","kk":"\u0421\u044b\u0493\u0430\u043d\u0430\u049b","en":"Sygnak"},"mapPosition":{"x":0.0864,"z":0.4571,"coordinateSystem":"normalized 0..1; x east, z south"},"terrain":"river_oasis","initialOwner":"abulkhair","adjacent":["sarysu","suzak","sauran"],"settlement":{"name":{"ru":"\u0421\u044b\u0433\u043d\u0430\u043a","kk":"\u0421\u044b\u0493\u0430\u043d\u0430\u049b","en":"Sygnak"},"kind":"fortified_city"}},{"id":"sauran","name":{"ru":"\u0421\u0430\u0443\u0440\u0430\u043d","kk":"\u0421\u0430\u0443\u0440\u0430\u043d","en":"Sauran"},"mapPosition":{"x":0.1852,"z":0.6571,"coordinateSystem":"normalized 0..1; x east, z south"},"terrain":"oasis","initialOwner":"abulkhair","adjacent":["sygnak","suzak","yasy"],"settlement":{"name":{"ru":"\u0421\u0430\u0443\u0440\u0430\u043d","kk":"\u0421\u0430\u0443\u0440\u0430\u043d","en":"Sauran"},"kind":"fortified_city"}},{"id":"yasy","name":{"ru":"\u042f\u0441\u044b","kk":"\u042f\u0441\u044b","en":"Yasy"},"mapPosition":{"x":0.2469,"z":0.7143,"coordinateSystem":"normalized 0..1; x east, z south"},"terrain":"oasis","initialOwner":"abulkhair","adjacent":["sauran","suzak","otrar"],"settlement":{"name":{"ru":"\u042f\u0441\u044b \u2014 \u0422\u0443\u0440\u043a\u0435\u0441\u0442\u0430\u043d","kk":"\u042f\u0441\u044b \u2014 \u0422\u04af\u0440\u043a\u0456\u0441\u0442\u0430\u043d","en":"Yasy \u2014 Turkestan"},"kind":"city"}},{"id":"otrar","name":{"ru":"\u041e\u0442\u0440\u0430\u0440","kk":"\u041e\u0442\u044b\u0440\u0430\u0440","en":"Otrar"},"mapPosition":{"x":0.2469,"z":0.8286,"coordinateSystem":"normalized 0..1; x east, z south"},"terrain":"river_oasis","initialOwner":"abulkhair","adjacent":["yasy","talas"],"settlement":{"name":{"ru":"\u041e\u0442\u0440\u0430\u0440","kk":"\u041e\u0442\u044b\u0440\u0430\u0440","en":"Otrar"},"kind":"fortified_city"}}],"units":{"mounted_archer":{"name":{"ru":"\u041a\u043e\u043d\u043d\u044b\u0439 \u043b\u0443\u0447\u043d\u0438\u043a","kk":"\u0410\u0442\u0442\u044b \u0441\u0430\u0434\u0430\u049b\u0448\u044b","en":"Mounted archer"},"role":"cavalry_ranged","health":100,"armor":2,"attack":8,"speed":15,"range":90,"morale":65,"cost":120,"upkeepPerTurn":8},"light_cavalry":{"name":{"ru":"\u041b\u0451\u0433\u043a\u0430\u044f \u043a\u043e\u043d\u043d\u0438\u0446\u0430","kk":"\u0416\u0435\u04a3\u0456\u043b \u0430\u0442\u0442\u044b \u04d9\u0441\u043a\u0435\u0440","en":"Light cavalry"},"role":"cavalry_melee","health":120,"armor":3,"attack":14,"speed":16,"range":2,"morale":65,"cost":105,"upkeepPerTurn":7},"heavy_cavalry":{"name":{"ru":"\u0422\u044f\u0436\u0451\u043b\u0430\u044f \u043a\u043e\u043d\u043d\u0438\u0446\u0430","kk":"\u0410\u0443\u044b\u0440 \u0430\u0442\u0442\u044b \u04d9\u0441\u043a\u0435\u0440","en":"Heavy cavalry"},"role":"cavalry_melee","health":170,"armor":7,"attack":22,"speed":12,"range":3,"morale":75,"cost":190,"upkeepPerTurn":13},"spearman":{"name":{"ru":"\u041a\u043e\u043f\u0435\u0439\u0449\u0438\u043a\u0438","kk":"\u041d\u0430\u0439\u0437\u0430\u0433\u0435\u0440\u043b\u0435\u0440","en":"Spearmen"},"role":"infantry_melee","health":110,"armor":3,"attack":12,"speed":8,"range":3,"morale":60,"cost":70,"upkeepPerTurn":4},"infantry_archer":{"name":{"ru":"\u041f\u0435\u0445\u043e\u0442\u043d\u044b\u0435 \u043b\u0443\u0447\u043d\u0438\u043a\u0438","kk":"\u0416\u0430\u044f\u0443 \u0441\u0430\u0434\u0430\u049b\u0448\u044b\u043b\u0430\u0440","en":"Foot archers"},"role":"infantry_ranged","health":80,"armor":1,"attack":9,"speed":8,"range":100,"morale":55,"cost":75,"upkeepPerTurn":4},"sabre_warrior":{"name":{"ru":"\u0412\u043e\u0438\u043d\u044b \u0441 \u0441\u0430\u0431\u043b\u044f\u043c\u0438","kk":"\u049a\u044b\u043b\u044b\u0448\u043a\u0435\u0440\u043b\u0435\u0440","en":"Sabre warriors"},"role":"infantry_melee","health":120,"armor":4,"attack":15,"speed":8,"range":2,"morale":65,"cost":90,"upkeepPerTurn":5},"khan_guard":{"name":{"ru":"\u041e\u0445\u0440\u0430\u043d\u0430 \u0445\u0430\u043d\u0430","kk":"\u0425\u0430\u043d \u0436\u0430\u0441\u0430\u0493\u044b","en":"Khan\u2019s guard"},"role":"cavalry_melee","health":190,"armor":8,"attack":24,"speed":12,"range":2,"morale":90,"cost":260,"upkeepPerTurn":18},"scout":{"name":{"ru":"\u0420\u0430\u0437\u0432\u0435\u0434\u0447\u0438\u043a\u0438","kk":"\u0411\u0430\u0440\u043b\u0430\u0443\u0448\u044b\u043b\u0430\u0440","en":"Scouts"},"role":"cavalry_ranged","health":75,"armor":1,"attack":5,"speed":18,"range":70,"morale":50,"cost":85,"upkeepPerTurn":5},"tribal_militia":{"name":{"ru":"\u041e\u043f\u043e\u043b\u0447\u0435\u043d\u0438\u0435","kk":"\u0415\u0440\u0456\u043a\u0442\u0456 \u0436\u0430\u0441\u0430\u049b","en":"Tribal levy"},"role":"infantry_melee","health":75,"armor":1,"attack":8,"speed":8,"range":3,"morale":40,"cost":40,"upkeepPerTurn":2}}};
var VERSION = 2;
// Runtime helpers are resolved at call time, after Pyrogenesis has loaded all
// simulation globals. Node uses the same modules for deterministic tests.
function politics() { return typeof KtwPolitics !== 'undefined' ? KtwPolitics : require('./KtwPolitics.js'); }
function bridge() { return typeof KtwBattleBridge !== 'undefined' ? KtwBattleBridge : require('./KtwBattleBridge.js'); }
function saves() { return typeof KtwSaveSystem !== 'undefined' ? KtwSaveSystem : require('./KtwSaveSystem.js'); }
var IMPLEMENTED_UNITS = ['mounted_archer','light_cavalry','heavy_cavalry','spearman','infantry_archer'];
var SEASONS = ['spring', 'summer', 'autumn', 'winter'];
var BUILDINGS = { pasture: { cost: 160, food: 38, silver: 0 }, market: { cost: 200, food: 0, silver: 45 }, workshop: { cost: 220, food: 0, silver: 20 } };
function fail(code) { throw new Error('KTW_' + code); }
function owns(object, key) { return Object.prototype.hasOwnProperty.call(object,key); }
function clone(value) { return JSON.parse(JSON.stringify(value)); }
function integer(value, low, high) { return Number.isInteger(value) && value >= low && value <= high; }
function faction(value) { return value === 'kazakh' || value === 'abulkhair'; }
function province(s, id) { return s.provinces.find(function(p) { return p.id === id; }); }
function army(s, id) { return s.armies.find(function(a) { return a.id === id; }); }
function soldiers(a) { return a.regiments.reduce(function(n, r) { return n + r.count; }, 0); }
function alive(a) { return !!a && soldiers(a) > 0; }
function random(s) { s.rng = (Math.imul(1664525, s.rng) + 1013904223) >>> 0; return s.rng / 4294967296; }
function log(s, key, data) { s.events.push({ id: 'event-' + s.nextEventId++, turn: s.turn, key: key, data: data || {} }); if (s.events.length > 60) s.events.shift(); }
function ready(s) { validate(s); if (s.status !== 'playing') fail('CAMPAIGN_ENDED'); if (s.pendingBattle) fail('BATTLE_PENDING'); }
function regiment(s, type, count) { return { id: 'r' + s.nextRegimentId++, type: type, count: count, morale: DATA.units[type].morale, fatigue: 0, experience: 0 }; }
function create(seed) {
  if (seed === undefined) seed = 1465;
  if (!integer(seed, 0, 4294967295)) fail('SEED');
  var s = { schemaVersion: VERSION, campaignId: DATA.campaignId, seed: seed, rng: seed, turn: 1, year: 1465, season: 'spring', status: 'playing',
    selectedArmy: 'kazakh_main', selectedProvince: 'shu', nextEventId: 1, nextBattleId: 1, nextRegimentId: 1, relation: 'war', ceasefireUntil: 0,
    treasury: { kazakh: { silver: 650, food: 900 }, abulkhair: { silver: 750, food: 900 } },
    provinces: DATA.provinces.map(function(p) { var q = clone(p); q.owner = q.initialOwner; delete q.initialOwner; q.buildings = { pasture: 0, market: 0, workshop: 0 }; return q; }),
    armies: [], pendingBattle: null, resolvedBattles: [], events: [], lastBattle: null };
  [['kazakh_main', 'kazakh', 'shu', 'kerei', [30,30,30,20,30,30]], ['abulkhair_main', 'abulkhair', 'sygnak', 'abulkhair', [25,25,30,20,30,25]]].forEach(function(row) {
    var types = ['mounted_archer','mounted_archer','light_cavalry','heavy_cavalry','spearman','infantry_archer'];
    s.armies.push({ id: row[0], faction: row[1], province: row[2], previousProvince: row[2], commander: row[3], movement: 1,
      regiments: types.map(function(type, i) { return regiment(s, type, row[4][i]); }) });
  });
  politics().initialize(s);
  log(s, 'campaign_started'); validate(s); return s;
}
function validateCore(s, version) {
  if (!s || typeof s !== 'object' || s.schemaVersion !== version || s.campaignId !== DATA.campaignId) fail('SAVE_VERSION');
  if (!integer(s.seed,0,4294967295) || !integer(s.rng,0,4294967295) || !integer(s.turn,1,100000) || s.year !== 1465 + Math.floor((s.turn-1)/4) || s.season !== SEASONS[(s.turn-1)%4]) fail('SAVE_CLOCK');
  if (!['playing','victory','defeat'].includes(s.status) || !['war','peace'].includes(s.relation) || !integer(s.ceasefireUntil,0,100000) || !integer(s.nextBattleId,1,1000000) || !integer(s.nextRegimentId,1,1000000)) fail('SAVE_STATE');
  ['kazakh','abulkhair'].forEach(function(f) { var t = s.treasury && s.treasury[f]; if (!t || !integer(t.silver,0,100000000) || !integer(t.food,0,100000000)) fail('SAVE_TREASURY'); });
  if (!Array.isArray(s.provinces) || s.provinces.length !== DATA.provinces.length) fail('SAVE_PROVINCES');
  var pids = new Set();
  s.provinces.forEach(function(p) {
    var original = DATA.provinces.find(function(x) { return x.id === p.id; });
    if (!original || pids.has(p.id) || !faction(p.owner) || JSON.stringify(p.adjacent) !== JSON.stringify(original.adjacent) || p.terrain !== original.terrain) fail('SAVE_PROVINCE');
    pids.add(p.id); Object.keys(BUILDINGS).forEach(function(b) { if (!p.buildings || !integer(p.buildings[b],0,3)) fail('SAVE_BUILDING'); });
  });
  if (!Array.isArray(s.armies) || s.armies.length !== 2) fail('SAVE_ARMIES');
  var aids = new Set(), rids = new Set();
  s.armies.forEach(function(a) {
    if (!['kazakh_main','abulkhair_main'].includes(a.id) || a.id !== a.faction + '_main' || aids.has(a.id) || !pids.has(a.province) || !pids.has(a.previousProvince) || !integer(a.movement,0,1) || !Array.isArray(a.regiments) || a.regiments.length > 24) fail('SAVE_ARMY');
    aids.add(a.id);
    a.regiments.forEach(function(r) {
      if (!/^r[1-9]\d*$/.test(r.id) || rids.has(r.id) || !owns(DATA.units,r.type) || !IMPLEMENTED_UNITS.includes(r.type) || !integer(r.count,0,30) || !integer(r.morale,0,100) || !integer(r.fatigue,0,100) || !integer(r.experience,0,1000)) fail('SAVE_REGIMENT');
      if (Number(r.id.slice(1)) >= s.nextRegimentId) fail('SAVE_COUNTER'); rids.add(r.id);
    });
  });
  if (s.selectedArmy !== null && !aids.has(s.selectedArmy)) fail('SAVE_SELECTION');
  if (!pids.has(s.selectedProvince) || !Array.isArray(s.events) || s.events.length > 60 || !Array.isArray(s.resolvedBattles) || s.resolvedBattles.length > 100000) fail('SAVE_HISTORY');
  var history = new Set();
  function validBattleId(id) { return typeof id === 'string' && /^battle-[1-9]\d*$/.test(id) && integer(Number(id.slice(7)),1,s.nextBattleId-1); }
  s.resolvedBattles.forEach(function(b) {
    if (!b || !validBattleId(b.id) || typeof b.signature !== 'string' || history.has(b.id)) fail('SAVE_HISTORY');
    var receipt;
    try { receipt = JSON.parse(b.signature); } catch (_) { fail('SAVE_HISTORY'); }
    if (!receipt || receipt.battleId !== b.id || !['kazakh','abulkhair','draw'].includes(receipt.winner) || !Array.isArray(receipt.survivors)) fail('SAVE_HISTORY');
    var ids = new Set();
    receipt.survivors.forEach(function(row) {
      if (!Array.isArray(row) || row.length !== 2 || typeof row[0] !== 'string' || !/^r[1-9]\d*$/.test(row[0]) || ids.has(row[0]) || !integer(row[1],0,30)) fail('SAVE_HISTORY');
      ids.add(row[0]);
    });
    if (receipt.deadCommanders !== undefined && (!Array.isArray(receipt.deadCommanders) || new Set(receipt.deadCommanders).size !== receipt.deadCommanders.length || receipt.deadCommanders.some(function(id) { return typeof id !== 'string' || !/^[a-z][a-z0-9_]*$/.test(id); }))) fail('SAVE_HISTORY');
    if (b.commanderIds !== undefined && (!Array.isArray(b.commanderIds) || new Set(b.commanderIds).size !== b.commanderIds.length || b.commanderIds.some(function(id) { return typeof id !== 'string' || !/^[a-z][a-z0-9_]*$/.test(id); }))) fail('SAVE_HISTORY');
    history.add(b.id);
  });
  if (s.lastBattle !== null && (!s.lastBattle || !history.has(s.lastBattle.battleId))) fail('SAVE_HISTORY');
  if (s.pendingBattle) {
    var b = s.pendingBattle;
    if (!validBattleId(b.id) || history.has(b.id) || !pids.has(b.provinceId) || !pids.has(b.attackerOrigin) || !pids.has(b.defenderOrigin) || !aids.has(b.attackerId) || !aids.has(b.defenderId) || b.attackerId === b.defenderId || !integer(b.seed,0,4294967295) || !Array.isArray(b.armies) || b.armies.length !== 2) fail('SAVE_BATTLE');
    if (b.armies[0].id !== b.attackerId || b.armies[1].id !== b.defenderId) fail('SAVE_BATTLE');
    b.armies.forEach(function(a) { if (JSON.stringify(a) !== JSON.stringify(army(s,a.id)) || !alive(a)) fail('SAVE_BATTLE_ROSTER'); });
  }
  return true;
}
function validate(s) {
  validateCore(s, VERSION);
  politics().validate(s);
  s.resolvedBattles.forEach(function(record) {
    var deaths = JSON.parse(record.signature).deadCommanders || [];
    deaths.forEach(function(id) {
      var c = getCharacter(s,id);
      if (!c || c.alive || !c.death || c.death.battleId !== record.id) fail('SAVE_CHARACTER_HISTORY');
    });
    if ((record.commanderIds || []).some(function(id) { return !getCharacter(s,id); })) fail('SAVE_CHARACTER_HISTORY');
  });
  s.characters.filter(function(c) { return !c.alive; }).forEach(function(c) {
    var record = s.resolvedBattles.find(function(b) { return b.id === c.death.battleId; });
    if (!record || !(JSON.parse(record.signature).deadCommanders || []).includes(c.id)) fail('SAVE_CHARACTER_HISTORY');
  });
  if (!integer(s.nextEventId,1,10000000)) fail('SAVE_EVENT_COUNTER');
  var eventIds = new Set();
  s.events.forEach(function(e) {
    if (!e || typeof e.id !== 'string' || !/^event-[1-9]\d*$/.test(e.id) || Number(e.id.slice(6)) >= s.nextEventId || eventIds.has(e.id) || !integer(e.turn,1,s.turn) || typeof e.key !== 'string' || !e.data || typeof e.data !== 'object' || Array.isArray(e.data)) fail('SAVE_EVENT');
    eventIds.add(e.id);
  });
  bridge().validateSnapshot(s, s.pendingBattle);
  return true;
}
function upgrade(state) {
  var s = clone(state);
  if (s.schemaVersion === 1) {
    // Reject malformed legacy saves before adding defaults. Existing casualties,
    // receipts and calendar stay unchanged; migration never invents past deaths.
    validateCore(s, 1);
    politics().initialize(s);
    s.nextEventId = 1;
    s.events.forEach(function(e) { e.id = 'event-' + s.nextEventId++; });
    s.schemaVersion = VERSION;
    if (s.pendingBattle) bridge().enrichSnapshot(s, s.pendingBattle);
  }
  validate(s);
  return s;
}
function select(s, armyId, provinceId) {
  validate(s);
  if (armyId !== undefined) { if (!army(s,armyId) || army(s,armyId).faction !== 'kazakh') fail('ARMY_SELECTION'); s.selectedArmy = armyId; }
  if (provinceId !== undefined) { if (!province(s,provinceId)) fail('PROVINCE_SELECTION'); s.selectedProvince = provinceId; }
  return s;
}
function createBattle(s, attackerId, defenderId, provinceId) {
  ready(s);
  var a = army(s,attackerId), d = army(s,defenderId), p = province(s,provinceId);
  if (!alive(a) || !alive(d) || a.faction === d.faction || !p || d.province !== p.id || !province(s,a.province).adjacent.includes(p.id) || a.movement < 1 || s.relation !== 'war') fail('INVALID_BATTLE');
  // Snapshot after spending movement, but before changing ownership or location.
  a.movement = 0;
  var b = { id: 'battle-' + s.nextBattleId++, turn: s.turn, provinceId: p.id, terrain: p.terrain, season: s.season,
    attackerId: a.id, defenderId: d.id, attackerOrigin: a.province, defenderOrigin: d.province, seed: Math.floor(random(s)*4294967296), armies: [clone(a),clone(d)] };
  bridge().enrichSnapshot(s,b);
  s.pendingBattle = b; log(s,'battle_pending',{ battleId:b.id, provinceId:p.id }); validate(s); return clone(b);
}
function moveArmy(s, armyId, provinceId, actorFaction) {
  ready(s); if (actorFaction === undefined) actorFaction = 'kazakh';
  var a = army(s,armyId), p = province(s,provinceId);
  if (!alive(a) || a.faction !== actorFaction || !p || a.movement < 1 || !province(s,a.province).adjacent.includes(p.id)) fail('INVALID_MOVE');
  if (p.owner !== a.faction && s.relation === 'peace') fail('PEACE_BORDER');
  var enemy = s.armies.find(function(x) { return alive(x) && x.faction !== a.faction && x.province === p.id; });
  if (enemy) return createBattle(s,a.id,enemy.id,p.id);
  a.previousProvince = a.province; a.province = p.id; a.movement = 0; p.owner = a.faction;
  s.selectedProvince = p.id; log(s,'army_moved',{ armyId:a.id, provinceId:p.id }); checkEnd(s); return null;
}
function recruit(s, armyId, type, count) {
  ready(s); if (count === undefined) count = 20;
  var a = army(s,armyId), u = owns(DATA.units,type) ? DATA.units[type] : null;
  if (!alive(a) || a.faction !== 'kazakh' || !u || !IMPLEMENTED_UNITS.includes(type) || !integer(count,1,30) || a.regiments.length >= 24 || province(s,a.province).owner !== 'kazakh') fail('INVALID_RECRUIT');
  var cost = Math.ceil(u.cost * count / 20), food = count * 2, t = s.treasury.kazakh;
  if (t.silver < cost || t.food < food) fail('INSUFFICIENT_RESOURCES');
  t.silver -= cost; t.food -= food; var r = regiment(s,type,count); a.regiments.push(r); log(s,'recruited',{ type:type,count:count }); return clone(r);
}
function build(s, provinceId, kind) {
  ready(s); var p = province(s,provinceId), b = owns(BUILDINGS,kind) ? BUILDINGS[kind] : null;
  if (!p || p.owner !== 'kazakh' || !b || p.buildings[kind] >= 3) fail('INVALID_BUILDING');
  var cost = b.cost * (p.buildings[kind]+1);
  if (s.treasury.kazakh.silver < cost) fail('INSUFFICIENT_RESOURCES');
  s.treasury.kazakh.silver -= cost; p.buildings[kind]++; log(s,'building_completed',{ provinceId:provinceId,kind:kind }); return p.buildings[kind];
}
function diplomacy(s, action) {
  ready(s);
  if (action === 'peace') {
    if (s.relation !== 'war') fail('ALREADY_PEACE');
    if (s.treasury.kazakh.silver < 250) fail('INSUFFICIENT_RESOURCES');
    s.treasury.kazakh.silver -= 250; s.treasury.abulkhair.silver += 250; s.relation = 'peace'; s.ceasefireUntil = s.turn + 3;
  } else if (action === 'war') { if (s.relation === 'war') fail('ALREADY_WAR'); s.relation = 'war'; s.ceasefireUntil = 0; }
  else fail('INVALID_DIPLOMACY');
  log(s,action === 'peace' ? 'truce_signed' : 'war_declared', action === 'peace' ? {reason:'tribute_accepted',payment:250,durationTurns:3} : {faction:'kazakh',reason:'player_order'}); return s.relation;
}
function findPath(s, from, to) {
  var queue = [[from]], visited = new Set([from]);
  while (queue.length) { var path = queue.shift(), last = path[path.length-1]; if (last === to) return path;
    province(s,last).adjacent.forEach(function(id) { if (!visited.has(id)) { visited.add(id); queue.push(path.concat([id])); } }); }
  return [];
}
function endTurn(s) {
  ready(s); s.turn++; s.year = 1465 + Math.floor((s.turn-1)/4); s.season = SEASONS[(s.turn-1)%4];
  ['kazakh','abulkhair'].forEach(function(f) {
    var land = s.provinces.filter(function(p) { return p.owner === f; });
    var income = land.reduce(function(n,p) { return n + 70 + p.buildings.market*45 + p.buildings.workshop*20; },0);
    var harvest = land.reduce(function(n,p) { return n + (s.season === 'winter' ? 30 : 90) + p.buildings.pasture*38; },0);
    var upkeep = 0, consumption = 0;
    s.armies.filter(function(a) { return a.faction === f; }).forEach(function(a) {
      a.movement = 1;
      a.regiments.forEach(function(r) { upkeep += Math.ceil(DATA.units[r.type].upkeepPerTurn*r.count/20); consumption += r.count; r.fatigue = Math.max(0,r.fatigue-25); r.morale = Math.min(100,r.morale+8); });
    });
    var t = s.treasury[f], shortage = Math.max(0,consumption-t.food-harvest);
    t.silver = Math.max(0,t.silver+income-upkeep); t.food = Math.max(0,t.food+harvest-consumption);
    if (shortage > 0) { s.armies.filter(function(a) { return a.faction === f; }).forEach(function(a) { a.regiments.forEach(function(r) { if (r.count > 0) r.count -= Math.max(1,Math.floor(r.count*0.08)); r.morale = Math.max(0,r.morale-15); }); }); log(s,'supply_shortage',{ faction:f }); }
  });
  if (s.relation === 'peace' && s.turn >= s.ceasefireUntil) { s.relation = 'war'; s.ceasefireUntil = 0; log(s,'truce_expired',{reason:'agreed_term_ended',expiryTurn:s.turn}); }
  log(s,'turn_started',{ season:s.season,year:s.year }); checkEnd(s);
  if (s.status !== 'playing') return null;
  if (s.relation === 'war') {
    var enemy = army(s,'abulkhair_main'), player = army(s,'kazakh_main'), path = findPath(s,enemy.province,player.province);
    if (path.length > 1) {
      log(s,'strategic_decision',{faction:'abulkhair',armyId:enemy.id,targetArmyId:player.id,provinceId:path[1],
        reason:province(s,player.province).owner === 'abulkhair' ? 'hostile_army_in_owned_province' : 'advance_against_hostile_army',
        factors:{relation:s.relation,ownSoldiers:soldiers(enemy),enemySoldiers:soldiers(player),distanceProvinces:path.length-1,path:path.slice()}});
      return moveArmy(s,enemy.id,path[1],'abulkhair');
    }
  }
  validate(s); return null;
}
function safeRetreat(s, a, b) {
  var origin = a.id === b.attackerId ? b.attackerOrigin : b.defenderOrigin;
  var enemy = s.armies.find(function(x) { return x.faction !== a.faction && alive(x); });
  var candidates = [origin].concat(province(s,b.provinceId).adjacent);
  return candidates.find(function(id) { return id !== b.provinceId && province(s,id).owner === a.faction && (!enemy || enemy.province !== id); }) || null;
}
function resolveBattle(s, result) {
  validate(s);
  var verified = bridge().validateResult(s, result);
  if (verified.alreadyApplied) return { alreadyApplied:true,battleId:result.battleId };
  // Mutate only an isolated candidate. A failed political consequence, invalid
  // report, or validation error cannot partially spend the original campaign.
  var candidate = clone(s);
  var summary = applyBattle(candidate, result, verified.signature);
  validate(candidate);
  Object.keys(s).forEach(function(key) { delete s[key]; });
  Object.keys(candidate).forEach(function(key) { s[key] = candidate[key]; });
  return clone(summary);
}
function applyBattle(s, result, signature) {
  var b = s.pendingBattle;
  var summary = { battleId:b.id,provinceId:b.provinceId,winner:result.winner,losses:{},captured:{},turn:s.turn };
  // This function operates on an isolated, validated transaction candidate.
  b.armies.forEach(function(snapshot) {
    var a = army(s,snapshot.id), before = soldiers(a);
    a.regiments.forEach(function(r) { r.count = result.survivors[r.id]; r.experience = Math.min(1000,r.experience+(result.winner === a.faction ? 10 : 3)); r.fatigue = 65; r.morale = Math.max(5,Math.min(100,r.morale+(result.winner === a.faction ? 10 : -20))); });
    a.movement = 0; summary.losses[a.faction] = before-soldiers(a); summary.captured[a.faction] = 0;
  });
  if (result.winner !== 'draw') {
    var winner = s.armies.find(function(a) { return a.faction === result.winner; });
    winner.previousProvince = winner.province; winner.province = b.provinceId; province(s,b.provinceId).owner = winner.faction;
    var loser = s.armies.find(function(a) { return a.faction !== result.winner; });
    if (alive(loser)) {
      var escape = safeRetreat(s,loser,b);
      if (escape) { loser.previousProvince = loser.province; loser.province = escape; }
      else { summary.captured[loser.faction] = soldiers(loser); loser.regiments.forEach(function(r) { r.count = 0; }); }
    }
  }
  s.resolvedBattles.push({ id:b.id,signature:signature,commanderIds:b.commanders.map(function(c) { return c.character.id; }) });
  s.pendingBattle = null;
  politics().onBattleResult(s,b,result);
  summary.deadCommanders = Object.keys(result.commanderOutcomes || {}).filter(function(id) { return result.commanderOutcomes[id] === 'dead'; }).sort();
  s.lastBattle = summary;
  log(s,'battle_resolved',clone(summary)); checkEnd(s); validate(s); return clone(summary);
}
function strength(a, terrain) {
  return a.regiments.reduce(function(n,r) {
    var u = DATA.units[r.type], terrainBonus = terrain === 'dry_steppe' && u.role.indexOf('cavalry') === 0 ? 1.12 : 1;
    return n+r.count*(u.health/25+u.attack+u.armor*2)*(0.6+r.morale/100)*(1-r.fatigue/200)*terrainBonus;
  },0);
}
function autoresolve(s) {
  validate(s); if (!s.pendingBattle) fail('NO_BATTLE');
  var b = s.pendingBattle, a = b.armies[0], d = b.armies[1];
  var localRng = { rng:b.seed }, ap = strength(a,b.terrain)*(0.9+random(localRng)*0.2), dp = strength(d,b.terrain)*1.08*(0.9+random(localRng)*0.2);
  var winner = ap >= dp ? a.faction : d.faction, result = { battleId:b.id,winner:winner,survivors:{} };
  b.armies.forEach(function(side) {
    var win = side.faction === winner, ratio = win ? Math.max(0.30,Math.min(0.80,1-Math.min(ap,dp)/Math.max(ap,dp)*0.55)) : 0.16;
    side.regiments.forEach(function(r) { result.survivors[r.id] = Math.max(0,Math.floor(r.count*ratio)); });
  });
  // Rounding must not annihilate every warrior on the computed winning side.
  // Retain one existing warrior, never more than the snapshotted roster count.
  var winningArmy = b.armies.find(function(side) { return side.faction === winner; });
  if (!winningArmy.regiments.some(function(r) { return result.survivors[r.id] > 0; })) {
    var survivor = winningArmy.regiments.find(function(r) { return r.count > 0; });
    result.survivors[survivor.id] = 1;
  }
  return resolveBattle(s,result);
}
function retreat(s) {
  validate(s); var b = s.pendingBattle; if (!b) fail('NO_BATTLE');
  var player = army(s,'kazakh_main');
  if (!safeRetreat(s,player,b)) fail('NO_RETREAT_ROUTE');
  var result = { battleId:b.id,winner:'abulkhair',survivors:{} };
  b.armies.forEach(function(a) { a.regiments.forEach(function(r) { result.survivors[r.id] = a.faction === 'kazakh' ? Math.floor(r.count*0.85) : r.count; }); });
  return resolveBattle(s,result);
}
function checkEnd(s) {
  if (!alive(army(s,'kazakh_main')) || !s.provinces.some(function(p) { return p.owner === 'kazakh'; })) s.status = 'defeat';
  else if (!alive(army(s,'abulkhair_main')) || s.provinces.every(function(p) { return p.owner === 'kazakh'; })) s.status = 'victory';
}
function serialize(s) { validate(s); return saves().encode(s); }
function restore(text) { return upgrade(saves().decode(text)); }
function restoreWithRecovery(primary, backup) { return saves().recover(primary, backup, restore); }
function getCharacter(s,id) { return s.characters.find(function(c) { return c.id === id; }); }
function getFaction(s,id) { return s.factions.find(function(f) { return f.id === id; }); }
function describeCouncil(s,id) { return politics().describeCouncil(s,id); }

return { create:create,validate:validate,upgrade:upgrade,getCharacter:getCharacter,getFaction:getFaction,describeCouncil:describeCouncil,restoreWithRecovery:restoreWithRecovery,select:select,moveArmy:moveArmy,endTurn:endTurn,recruit:recruit,build:build,diplomacy:diplomacy,createBattle:createBattle,resolveBattle:resolveBattle,autoresolve:autoresolve,retreat:retreat,serialize:serialize,restore:restore,getArmy:army,getProvince:province,soldiers:soldiers,findPath:findPath,unitTypes:clone(DATA.units),implementedUnitTypes:IMPLEMENTED_UNITS.slice(),definitions:clone(DATA),buildings:clone(BUILDINGS),seasons:SEASONS.slice() };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = KtwCampaign;

if (typeof Engine !== 'undefined') Engine.RegisterGlobal('KtwCampaign', KtwCampaign);
