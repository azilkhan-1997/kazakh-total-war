/* SPDX-License-Identifier: GPL-2.0-or-later
 * Deterministic campaign invariant stress check, not native engine/performance QA.
 * Run: node tools/fuzz_campaign.cjs --report docs/fuzz-v0.2.json
 */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const projectRoot=path.resolve(__dirname,'..');
const C=require(path.join(projectRoot,'mods/kazakh_total_war/simulation/helpers/KtwCampaign.js'));
const reportIndex=process.argv.indexOf('--report');
if(reportIndex!==-1 && !process.argv[reportIndex+1]) throw new Error('Provide --report path');
let operations=0,saveLoads=0,battles=0,replays=0,corruptRecoveries=0,rejections=0;
let failures=[];
for(let seed=1;seed<=1000;seed++){
 let rng=seed,history=[];function random(n){rng=(Math.imul(rng,1664525)+1013904223)>>>0;return rng%n;}
 let s=C.create(seed),last=null;
 for(let step=0;step<100;step++){
  let action='',before=JSON.stringify(s);
  try{
   if(random(5)===0){
    action='save/load';s=C.restore(C.serialize(s));assert.equal(JSON.stringify(s),before);saveLoads++;
    if(random(4)===0){let recovery=C.restoreWithRecovery('{broken',C.serialize(s));assert.equal(JSON.stringify(recovery.state),before);assert.equal(recovery.recovered,true);corruptRecoveries++;}
   }else if(last && random(8)===0){
    action='replay';assert.equal(C.resolveBattle(s,last).alreadyApplied,true);assert.equal(JSON.stringify(s),before);replays++;
   }else if(s.status!=='playing')break;
   else if(s.pendingBattle){
    if(random(3)===0){action='autoresolve';C.autoresolve(s);last=null;}
    else if(random(5)===0){action='retreat';C.retreat(s);last=null;}
    else{
     action='tactical_result';let b=s.pendingBattle,r={battleId:b.id,winner:['kazakh','abulkhair','draw'][random(3)],survivors:{},commanderOutcomes:{}};
     for(let a of b.armies)for(let reg of a.regiments)r.survivors[reg.id]=random(reg.count+1);
     if(r.winner!=='draw'){let win=b.armies.find(a=>a.faction===r.winner);if(!win.regiments.some(reg=>r.survivors[reg.id]>0)){let live=win.regiments.find(reg=>reg.count>0);r.survivors[live.id]=1;}}
     for(let cmd of b.commanders){let a=b.armies.find(a=>a.id===cmd.armyId);r.commanderOutcomes[cmd.character.id]=random(3)===0&&a.regiments.some(reg=>r.survivors[reg.id]<reg.count)?'dead':'alive';}
     C.resolveBattle(s,r);last=JSON.parse(JSON.stringify(r));
    }
    battles++;
   }else{
    switch(random(7)){
     case 0:case 1: action='endTurn';C.endTurn(s);break;
     case 2: action='move';let a=C.getArmy(s,'kazakh_main'),p=C.getProvince(s,a.province);C.moveArmy(s,a.id,p.adjacent[random(p.adjacent.length)]);break;
     case 3: action='recruit';C.recruit(s,'kazakh_main',C.implementedUnitTypes[random(5)],1+random(30));break;
     case 4: action='build';C.build(s,s.provinces[random(s.provinces.length)].id,['pasture','market','workshop'][random(3)]);break;
     case 5: action='diplomacy';C.diplomacy(s,s.relation==='war'?'peace':'war');break;
     case 6: action='select';C.select(s,'kazakh_main',s.provinces[random(s.provinces.length)].id);break;
    }
   }
   C.validate(s);operations++;history.push(action);
  }catch(e){
   try{assert.equal(JSON.stringify(s),before);C.validate(s);}catch(invariant){failures.push({seed,step,action,error:String(e),invariant:String(invariant),history});break;}
   if(!/^KTW_(INVALID_MOVE|PEACE_BORDER|INSUFFICIENT_RESOURCES|INVALID_RECRUIT|INVALID_BUILDING|NO_RETREAT_ROUTE)$/.test(e.message)){failures.push({seed,step,action,error:String(e),history});break;}
   rejections++;history.push(action+':'+e.message);
  }
 }
}
const sourceFiles=['KtwCampaign.js','KtwBattleBridge.js','KtwPolitics.js','KtwSaveSystem.js'];
const sourceHashes=Object.fromEntries(sourceFiles.map(file=>[file,crypto.createHash('sha256').update(fs.readFileSync(path.join(projectRoot,'mods/kazakh_total_war/simulation/helpers',file))).digest('hex')]));
const report={scope:'Pure JavaScript campaign state invariants; not native engine, graphical, Windows or performance validation',seedRange:{first:1,last:1000},seeds:1000,maxSteps:100,operations,saveLoads,battles,replays,corruptRecoveries,rejections,failures,passed:failures.length===0,sourceHashes};
const output=JSON.stringify(report,null,2)+'\n';
if(reportIndex!==-1){const target=path.resolve(process.argv[reportIndex+1]);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,output);}
process.stdout.write(output);
process.exitCode=report.passed?0:1;
