// Test-only observation wrapper: does not modify health, orders or results.
const KtwQaOriginalTick=KtwController.prototype.Tick;
KtwController.prototype.Tick=function() {
 KtwQaOriginalTick.call(this);
 if (this.ktwQaLoggedFinal) return;
 if (this.elapsed===1 || this.elapsed % 30===0 || this.transition)
  warn("KTW_V02_HEADLESS "+JSON.stringify({seconds:this.elapsed,stats:this.battleStats,transition:this.transition,result:this.lastResult,error:this.error,state:this.transition?this.state:null,commanders:this.commanders}));
 if(this.transition) this.ktwQaLoggedFinal=true;
};
