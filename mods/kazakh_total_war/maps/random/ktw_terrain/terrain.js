// SPDX-License-Identifier: GPL-2.0-or-later
// Original schematic Central Asian terrain. Coordinates are game-scale, not a GIS border claim.
function KtwGenerateTerrain(settings, battle)
{
    const size = settings.Size || 256;
    const state = settings.KtwCampaign || {};
    const winter = state.season === "winter";
    const terrain = state.pendingBattle ? state.pendingBattle.terrain : "river_steppe";
    const dry = terrain === "dry_steppe" || terrain === "oasis";
    const grass = winter ? "alpine_grass_snow_50" : dry ? "steppe_grass_dirt_01" : "steppe_grass_02";
    const map = new RandomMap(20, grass);
    const towns = KtwLocations.map(p => ({id:p.id, x:p.x*size,z:p.z*size,adjacent:p.adjacent}));
    const byId = Object.fromEntries(towns.map(p => [p.id,p]));
    const routes=[];
    if (!battle)
        for (const a of towns)
            for (const id of a.adjacent)
                if (a.id < id) routes.push([a,byId[id]]);
    const distanceToSegment = (x,z,a,b) => {
        const dx=b.x-a.x,dz=b.z-a.z;
        const t=Math.max(0,Math.min(1,((x-a.x)*dx+(z-a.z)*dz)/(dx*dx+dz*dz)));
        return Math.hypot(x-a.x-t*dx,z-a.z-t*dz);
    };
    const ground = (x,z) => {
        const nx=x/size,nz=z/size;
        const ripple=Math.sin(nx*19+1.5)*Math.cos(nz*21)*1.8+Math.sin(nx*47+nz*31)*0.55;
        const edge=Math.pow(Math.max(0,(0.16-Math.min(nx,1-nx,nz,1-nz))/0.16),2);
        const peaks=22+45*Math.pow(Math.sin(nx*17.5+nz*7.2),2);
        let h=20+ripple+edge*peaks;
        if (!battle) {
            const ridge=Math.exp(-Math.pow((nz-(0.88-0.25*nx))/0.065,2));
            h+=ridge*(12+17*Math.pow(Math.sin(nx*22),2));
            // A schematic river corridor, deliberately separated from the town markers.
            const riverX=0.10+0.07*nz+0.015*Math.sin(nz*16);
            const river=Math.exp(-Math.pow((nx-riverX)/0.009,2));
            h-=river*13;
            for(const p of towns) {
                const d=Math.hypot(x-p.x,z-p.z);
                if(d<11) h=h*(d/11)+20*(1-d/11);
            }
            // Trade roads double as gentle traversable passes.
            for(const [a,b] of routes) {
                const d=distanceToSegment(x,z,a,b);
                if(d<2.5)h=h*(d/2.5)+20*(1-d/2.5);
            }
        }
        return h;
    };
    for(let x=0;x<=size;++x)
        for(let z=0;z<=size;++z)
            map.setHeight(new Vector2D(x,z),ground(x,z));
    for(let x=0;x<size;++x)
        for(let z=0;z<size;++z) {
            const h=map.getHeight(new Vector2D(x,z));
            let texture=grass;
            if(h>47)texture="alpine_snow_01";
            else if(h>30)texture="alpine_rock_02";
            else if(h<15.5)texture="steppe_river_rocks_wet";
            else if(Math.sin(x*.085)*Math.cos(z*.071)>.35)texture=winter?"alpine_snow_02":"steppe_grass_04";
            if(!battle) {
                const closest=towns.map(p=>Math.hypot(x-p.x,z-p.z)).sort((a,b)=>a-b);
                if(closest[1]-closest[0]<0.50 && h>16 && h<30)texture="steppe_rocks_dirt_01";
                if(routes.some(([a,b])=>distanceToSegment(x,z,a,b)<0.8))texture="steppe_grass_dirt_03";
                if(towns.some(p=>Math.hypot(x-p.x,z-p.z)<3))texture="desert_city_tile_pers_dirt";
            }
            map.setTexture(new Vector2D(x,z),texture);
        }
    // Visual-only flora has no collision and does not alter combat pathfinding.
    for(let i=0;i<(battle?1100:450);++i) {
        const x=randFloat(9,size-9), z=randFloat(9,size-9);
        const h=ground(x,z);
        if(h<17 || h>35 || (!battle && towns.some(p=>Math.hypot(x-p.x,z-p.z)<9)))continue;
        const actor=i%11===0?"props/flora/bush_desert_dry_a.xml":"props/flora/grass_soft_dry_small.xml";
        if(!winter)map.placeEntityAnywhere("actor|"+actor,0,new Vector2D(x,z),randFloat(0,2*Math.PI));
    }
    setSkySet("sunny");
    setSunColor(1.05,0.91,0.73);
    setSunElevation(battle?0.55:0.75);
    setSunRotation(-0.55);
    setAmbientColor(0.42,0.46,0.50);
    setWaterHeight(14);
    setWaterColor(0.14,0.32,0.36);
    setWaterTint(0.22,0.43,0.46);
    setWaterWaviness(0.8);
    setWaterMurkiness(0.60);
    setFogColor(0.68,0.69,0.64);
    setFogFactor(battle ? 0.08 : 0.015);
    setFogThickness(0.25);
    setPPEffect("hdr");
    setPPContrast(0.56);
    setPPSaturation(0.47);
    setPPBloom(0.15);
    g_Camera.Position={x:size*2,y:battle?120:430,z:battle?size*3.3:size*4.5};
    g_Camera.Rotation=Math.PI;
    g_Camera.Declination=battle?0.60:0.93;
    return map;
}
