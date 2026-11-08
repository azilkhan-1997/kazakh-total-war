const KtwTestTick=KtwController.prototype.Tick;
KtwController.prototype.Tick=function(){KtwTestTick.call(this);if(this.elapsed===1 || this.elapsed%30===0 || this.transition) {warn("KTW_QA "+JSON.stringify({time:this.elapsed,stats:this.battleStats,transition:this.transition,result:this.lastResult,error:this.error}));} };
