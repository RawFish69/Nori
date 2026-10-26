const {test}=require('node:test'),assert=require('node:assert/strict'),F=require('../../map/flight.js');
test('a grid is never permission or automatic prohibition, including zero ceilings',()=>{for(const value of [0,100,400,null])assert.equal(F.classify({properties:{category:'faa-uasfm',altitude:{value}}}).status,'reference')});
test('only published restriction datasets become red; unknown remains unassessed',()=>{for(const category of ['faa-prohibited','faa-security'])assert.equal(F.classify({properties:{category}}).status,'restricted');assert.equal(F.classify({properties:{category:'faa-special-use'}}).status,'review');assert.equal(F.classify({properties:{category:'faa-controlled'}}).status,'unknown');assert.equal(F.classify({properties:{}}).status,'unknown')});
test('documented launch-site marker does not invent an allowed flight polygon',()=>{assert.equal(F.sites.features.length,1);const site=F.sites.features[0];assert.equal(site.geometry.type,'Point');assert.equal(F.classify(site).status,'site');assert.match(site.properties.description,/does not outline/);assert.equal(new URL(site.properties.url).protocol,'https:')});

const now=1000000,box={west:-101,east:-99,south:39,north:41};
const records=()=>F.requiredLayers.map(id=>({id,enabled:true,limited:false,fetchedAt:now,loadedBounds:{...box}}));
test('green coverage requires all restriction layers, fresh successful uncapped queries',()=>{
 assert.deepEqual(F.coverageBounds(records(),now),box);
 for(const patch of [{enabled:false},{error:true},{limited:true},{fetchedAt:0},{loadedBounds:null}]){const r=records();Object.assign(r[0],patch);assert.equal(F.coverageBounds(r,now),null)}
 assert.equal(F.coverageBounds(records().slice(1),now),null);
});
test('green uses only intersecting queried coverage and clips to US land',()=>{
 const r=records();r[0].loadedBounds.west=-100;assert.equal(F.coverageBounds(r,now).west,-100);
 const regions=[{name:'United States of America',polygons:[[[-102,38],[-98,38],[-98,42],[-102,42],[-102,38]]]}];
 const features=F.coverageFeatures(r,regions,now).features;assert.equal(features.length,1);
 for(const [lon,lat]of features[0].geometry.coordinates[0]){assert(lon>=-100&&lon<=-99&&lat>=39&&lat<=41)}
 assert.equal(F.coverageFeatures(r,[{name:'Other country',polygons:regions[0].polygons}],now).features.length,0);
});

test('Class E transition areas and E3/E4 extensions do not blanket the surface yellow',()=>{
 for(const subtype of ['E3','E4','E5','E6'])assert.equal(F.classify({properties:{category:'faa-controlled',airspaceClass:'E',title:'AIRPORT CLASS '+subtype,lowerAltitude:{value:subtype==='E5'?700:0,reference:'SFC',unit:'FT'}}}).status,'reference');
 assert.equal(F.classify({properties:{category:'faa-controlled',airspaceClass:'E',title:'AIRPORT CLASS E2',lowerAltitude:{value:0,reference:'SFC',unit:'FT'}}}).status,'review');
});
test('surface B/C/D need review, elevated shelves are reference and unknown limits stay unknown',()=>{
 for(const airspaceClass of ['B','C','D']){
  assert.equal(F.classify({properties:{category:'faa-controlled',airspaceClass,lowerAltitude:{value:0,reference:'SFC',unit:'FT'}}}).status,'review');
  assert.equal(F.classify({properties:{category:'faa-controlled',airspaceClass,lowerAltitude:{value:2500,reference:'MSL',unit:'FT'}}}).status,'reference');
  assert.equal(F.classify({properties:{category:'faa-controlled',airspaceClass}}).status,'unknown');
 }
});

test('ground-use rules are distinct from airspace restrictions and missing ground layers prevent green',()=>{
 for(const category of ['ground-nps','ground-refuges','ground-wilderness']){
  assert.equal(F.classify({properties:{category,ruleType:'ground'}}).status,'ground-restricted');
  const r=records();r.find(v=>v.id===category).enabled=false;assert.equal(F.coverageBounds(r,now),null);
 }
});
