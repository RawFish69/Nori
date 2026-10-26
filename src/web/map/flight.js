(function(root){'use strict';
function classify(feature){
 const p=feature.properties||{};
 if(p.ruleType==='ground'||String(p.category||'').startsWith('ground-'))return{status:'ground-restricted',label:p.category==='ground-nps'?'National park: launch restrictions':p.category==='ground-refuges'?'Wildlife refuge: launch restrictions':'Wilderness: launch restrictions',reason:'Red hatching marks a ground-use restriction. Launching, landing or operating from this land is generally prohibited without an applicable exception. Read the linked agency policy; this is separate from FAA airspace.'};
 if(p.category==='launch-site')return{status:'site',label:'Designated flying site',reason:'The operator documents a flying site here. Use the designated drone area and check current field rules; this marker is not an approved flight boundary.'};
 if(p.category==='faa-prohibited')return{status:'restricted',label:'Prohibited airspace',reason:'Published prohibited area. Read the source for vertical limits and applicable exceptions before planning a flight.'};
 if(p.category==='faa-security')return{status:'restricted',label:'UAS security restriction',reason:'Published UAS security restriction. Check the official restriction, vertical limits and any authorized exceptions.'};
 if(p.category==='faa-uasfm')return{status:'reference',label:'Authorization request guidance',reason:'This grid is reference information, not an authorization boundary. Its ceiling guides an FAA request where authorization is required; it does not independently make the whole cell permission-required.'};
 if(p.category==='faa-controlled'){
  let lower=p.lowerAltitude;if(typeof lower==='string'){try{lower=JSON.parse(lower)}catch{lower=null}}
  const type=String(p.airspaceClass||'').toUpperCase(),subtype=(String(p.title||'')+' '+String(p.airspaceType||'')).match(/\b(?:CLASS\s+)?E([2-6])\b/i)?.[1];
  if(type==='E'&&['3','4','5','6'].includes(subtype))return{status:'reference',label:'Class E reference area',reason:'This is not an airport Class E2 authorization surface. It is shown as reference rather than a blanket ground-level authorization requirement. Check the source and any overlapping restrictions.'};
  const value=lower?.value,ref=String(lower?.reference||'').toUpperCase();
  const surface=Number.isFinite(value)&&value===0&&['SFC','AGL','GND','SURFACE'].includes(ref);
  if(surface&&(['B','C','D'].includes(type)||type==='E'&&subtype==='2'))return{status:'review',label:'Surface authorization zone',reason:'Published surface Class '+(type==='E'?'E2':type)+' airspace. Check operating hours and obtain applicable FAA authorization before flight.'};
  if(Number.isFinite(value)&&value>0&&['MSL','SFC','AGL'].includes(ref))return{status:'reference',label:'Elevated airspace boundary',reason:'This airspace starts above its published vertical datum, not automatically at ground level. It is outlined for reference; compare the source floor with terrain and your planned altitude.'};
  return{status:'unknown',label:'Vertical limits need checking',reason:'The source does not establish a surface authorization requirement for this feature. Inspect the classification and vertical limits before relying on a color.'};
 }
 if(p.category==='faa-special-use')return{status:'review',label:'Check activity and restrictions',reason:'Special-use boundaries do not establish current activation. Read the source and check current notices.'};
 return{status:'unknown',label:'Not assessed',reason:'This dataset does not establish takeoff or flight permission.'};
}
const sites={type:'FeatureCollection',features:[{type:'Feature',geometry:{type:'Point',coordinates:[-118.481821,34.175355]},properties:{id:'apollo-xi',title:'Apollo XI Model Aircraft Field',category:'launch-site',source:'San Fernando Valley Flyers',url:'https://www.valleyflyers.com/menu2/column1/listing1',description:'The field operator lists a designated drone racing and obstacle-course area. This marker uses the operator-published field coordinates; it does not outline the drone area. Check the designated-area map, field schedule, current rules and airspace arrangements before launch.',reviewed:'2026-10-24'}}]};
// Green describes queried data coverage, not a legal permission assessment.
const requiredLayers=['faa-prohibited','faa-security','faa-controlled','faa-special-use','ground-nps','ground-refuges','ground-wilderness'];
function coverageBounds(records,now=Date.now()){
 if(!Array.isArray(records)||records.length!==requiredLayers.length)return null;
 const boxes=[];
 for(const id of requiredLayers){const r=records.find(r=>r.id===id);if(!r||!r.enabled||r.error||r.limited||!Number.isFinite(r.fetchedAt)||now-r.fetchedAt>600000)return null;const b=r.loadedBounds;if(!b||![b.west,b.south,b.east,b.north].every(Number.isFinite)||b.west>=b.east||b.south>=b.north)return null;boxes.push(b)}
 const b={west:Math.max(...boxes.map(b=>b.west)),east:Math.min(...boxes.map(b=>b.east)),south:Math.max(...boxes.map(b=>b.south)),north:Math.min(...boxes.map(b=>b.north))};return b.west<b.east&&b.south<b.north?b:null;
}
function clipRing(ring,b){
 let out=ring.slice(0,-1);
 for(const [axis,edge,greater]of [[0,b.west,true],[0,b.east,false],[1,b.south,true],[1,b.north,false]]){
  const input=out;out=[];if(!input.length)break;
  const inside=p=>greater?p[axis]>=edge:p[axis]<=edge;
  for(let i=0;i<input.length;i++){const a=input[i],z=input[(i+1)%input.length],ai=inside(a),zi=inside(z);if(ai)out.push(a);if(ai!==zi){const t=(edge-a[axis])/(z[axis]-a[axis]);out.push([a[0]+t*(z[0]-a[0]),a[1]+t*(z[1]-a[1])]);}}
 }
 if(out.length<3)return null;out.push(out[0]);return out;
}
function coverageFeatures(records,regions,now=Date.now()){
 const b=coverageBounds(records,now);if(!b)return{type:'FeatureCollection',features:[]};
 const country=regions.find(r=>r.name==='United States of America');const rings=(country?.polygons||[]).map(r=>clipRing(r,b)).filter(Boolean);
 return{type:'FeatureCollection',features:rings.map(r=>({type:'Feature',properties:{category:'queried-coverage'},geometry:{type:'Polygon',coordinates:[r]}}))};
}
const api={classify,sites,requiredLayers,coverageBounds,coverageFeatures};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NoriFlight=api;
})(globalThis);
