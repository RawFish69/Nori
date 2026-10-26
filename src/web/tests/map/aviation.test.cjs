const { test, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const originalFetch = global.fetch;
afterEach(() => { global.fetch = originalFetch; });
const api = () => require('../../map/aviation.js');
const polygon = { type: 'Polygon', coordinates: [[[-122.5,37.5],[-122.4,37.5],[-122.4,37.6],[-122.5,37.5]]] };
const feature = properties => ({ type: 'Feature', id: 7, geometry: polygon, properties });
function respond(features = [], extra = {}) {
  global.fetch = async () => ({ ok: true, json: async () => ({ type: 'FeatureCollection', features, ...extra }) });
}
test('browser global and CommonJS expose the same public contract', () => {
  const context = { window: {}, URL, URLSearchParams };
  vm.runInNewContext(fs.readFileSync(require.resolve('../../map/aviation.js'), 'utf8'), context);
  assert.equal(typeof context.window.NoriAviation.query, 'function');
  assert.ok(api().catalog.length >= 5);
});
test('query sends a viewport envelope, bounded fields, record cap and abort signal', async () => {
  const controller = new AbortController();
  let sent, options;
  global.fetch = async (url, opts) => { sent = new URL(url); options = opts; return { ok: true, json: async () => ({ type: 'FeatureCollection', features: [] }) }; };
  const result = await api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7], controller.signal);
  const p = sent.searchParams;
  assert.deepEqual(JSON.parse(p.get('geometry')), { xmin:-122.6,ymin:37.4,xmax:-122.3,ymax:37.7,spatialReference:{wkid:4326} });
  for (const [k,v] of Object.entries({ geometryType:'esriGeometryEnvelope', inSR:'4326', outSR:'4326', f:'geojson', resultRecordCount:'400', spatialRel:'esriSpatialRelIntersects' })) assert.equal(p.get(k),v);
  assert.equal(p.get('outFields').includes('*'), false);
  assert.ok(p.get('outFields').includes('CEILING'));
  assert.equal(options.signal, controller.signal);
  assert.equal(options.mode, 'cors');
  assert.equal(options.credentials, 'omit');
  assert.equal(result.provider, 'FAA');
  assert.equal(result.coverage, 'United States');
  assert.ok(Number.isFinite(Date.parse(result.fetchedAt)));
});
test('grid zero ceiling is preserved as request guidance in feet AGL, never permission', async () => {
  respond([feature({ OBJECTID:7, CEILING:0, UNIT:'Feet', APT1_NAME:'Example Airport', MAP_EFF:'10/1/2026', LAST_EDIT:'4/27/2017' })]);
  const { features:[f] } = await api().query('faa-uasfm', [[-122.6,37.4],[-122.3,37.7]]);
  assert.equal(f.properties.id, 'faa-uasfm:7');
  assert.equal(f.properties.title, 'Example Airport');
  assert.deepEqual(f.properties.altitude, { value:0,unit:'Feet',reference:'AGL',meaning:'Maximum altitude for an authorization request without additional safety analysis' });
  assert.match(f.properties.description, /0 Feet AGL/);
  assert.match(f.properties.description, /does not authorize/i);
  assert.equal(f.properties.observed, null);
  assert.equal(f.properties.expires, null);
  assert.equal(f.properties.effectiveDate, '10/1/2026');
  assert.deepEqual(f.geometry, polygon);
});
test('missing or empty altitude remains unknown rather than zero', async () => {
  for (const CEILING of [null, undefined, '', '  ', 'unknown']) {
    respond([feature({ CEILING })]);
    const r = await api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7]);
    assert.equal(r.features[0].properties.altitude.value, null);
    assert.match(r.features[0].properties.description, /not supplied/i);
  }
});
test('airspace retains vertical units, references, descriptors and class without inventing activity', async () => {
  respond([feature({ NAME:'Example', CLASS:'B', LOWER_VAL:0, LOWER_UOM:'FT', LOWER_CODE:'SFC', UPPER_VAL:10000, UPPER_UOM:'FT', UPPER_CODE:'MSL', UPPER_DESC:'TNI' })]);
  const r = await api().query('faa-controlled', { getWest:()=>-122.6,getSouth:()=>37.4,getEast:()=>-122.3,getNorth:()=>37.7 });
  const p = r.features[0].properties;
  assert.deepEqual(p.upperAltitude, { value:10000,unit:'FT',reference:'MSL',descriptor:'TNI',meaning:'Published upper airspace boundary' });
  assert.equal(p.lowerAltitude.reference, 'SFC');
  assert.equal(p.airspaceClass, 'B');
  assert.equal(p.observed, null);
  assert.equal(p.expires, null);
});
test('controlled query excludes service Mode C and other non-class records', async () => {
  let where;
  global.fetch = async url => {
    where = new URL(url).searchParams.get('where');
    return {ok:true,json:async()=>({type:'FeatureCollection',features:[]})};
  };
  await api().query('faa-controlled', [-122.6,37.4,-122.3,37.7]);
  assert.equal(where, "CLASS IN ('B','C','D','E')");
});
test('missing altitude units and vertical references are never guessed', async () => {
  respond([feature({ CEILING:100 })]);
  let r = await api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7]);
  assert.equal(r.features[0].properties.altitude.unit,null);
  assert.match(r.features[0].properties.description,/unit not supplied/);
  respond([feature({UPPER_VAL:'4500'})]);
  r = await api().query('faa-special-use', [-122.6,37.4,-122.3,37.7]);
  assert.equal(r.features[0].properties.upperAltitude.value,4500);
  assert.equal(r.features[0].properties.upperAltitude.unit,null);
  assert.equal(r.features[0].properties.upperAltitude.reference,null);
});
test('security floor and ceiling remain source text with explicit restriction context', async () => {
  respond([feature({ Facility:'Example facility', Reason:'National Security', Floor:'Surface', Ceiling:"400' AGL" })]);
  const r = await api().query('faa-security', [-122.6,37.4,-122.3,37.7]);
  assert.equal(r.features[0].properties.floor, 'Surface');
  assert.equal(r.features[0].properties.ceiling, "400' AGL");
  assert.match(r.features[0].properties.description, /400' AGL/);
});
test('HTTP 200 ArcGIS errors reject rather than appearing as empty airspace', async () => {
  global.fetch = async () => ({ ok:true,json:async()=>({error:{code:400,message:'Invalid query',details:['bad field']}}) });
  await assert.rejects(api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7]), /400.*Invalid query.*bad field/);
});
test('HTTP failure, invalid JSON shape and abort propagate', async () => {
  global.fetch = async () => ({ok:false,status:503});
  await assert.rejects(api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7]), /503/);
  global.fetch = async () => ({ok:true,json:async()=>({features:[]})});
  await assert.rejects(api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7]), /GeoJSON/);
  global.fetch = async () => { throw new DOMException('Aborted','AbortError'); };
  await assert.rejects(api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7]), {name:'AbortError'});
});
test('malformed feature geometry rejects instead of masquerading as useful map data', async () => {
  for (const geometry of [null, {type:'Point',coordinates:[-122.5,37.5]}, {type:'Polygon'}]) {
    respond([{...feature({}),geometry}]);
    await assert.rejects(api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7]), /GeoJSON/);
  }
});
test('both ArcGIS transfer-limit locations and a full result page report limited', async () => {
  for (const extra of [{exceededTransferLimit:true},{properties:{exceededTransferLimit:true}}]) {
    respond([],extra);
    assert.equal((await api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7])).limited,true);
  }
  respond(Array.from({length:401},(_,i)=>feature({OBJECTID:i})));
  const r = await api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7]);
  assert.equal(r.features.length,400);
  assert.equal(r.limited,true);
  respond(Array.from({length:400},(_,i)=>feature({OBJECTID:i})));
  assert.equal((await api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7])).limited,true);
  respond();
  assert.equal((await api().query('faa-uasfm', [-122.6,37.4,-122.3,37.7])).limited,false);
});
test('invalid, global, reversed and antimeridian bounds reject before any network', async () => {
  global.fetch = async () => { assert.fail('must not fetch'); };
  for (const bounds of [null,[],[-180,-90,180,90],[-123,37,-120,38],[-122,38,-123,37],[179,37,-179,38],[-181,0,-180,1],[0,90,1,91],[0,0,NaN,1],[0,0,0,1],['0',0,1,1]]) {
    await assert.rejects(api().query('faa-uasfm', bounds), /bounds|viewport/i);
  }
  await assert.rejects(api().query('missing', [0,0,1,1]), /unavailable|unknown/i);
});
