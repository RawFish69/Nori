const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const feeds = require('../../map/feeds.js');
const point = { type: 'Point', coordinates: [-120, 40, 3] };
const quake = (geometry = point, properties = {}) => ({ type: 'Feature', id: 'q1', geometry, properties: { title: 'M 3 earthquake', time: 1700000000000, url: 'https://earthquake.usgs.gov/earthquakes/eventpage/q1', ...properties } });
const alert = (geometry = point, properties = {}) => ({ type: 'Feature', geometry, properties: { id: 'a1', event: 'Tornado Warning', headline: 'Warning', description: 'Take shelter', sent: '2026-10-24T12:00:00-07:00', expires: '2026-10-24T13:00:00-07:00', severity: 'Extreme', '@id': 'https://api.weather.gov/alerts/a1', ...properties } });
test('earthquakes preserve dates and return only scalar allowlisted properties', () => {
  const r = feeds.normalizeEarthquakes({ type: 'FeatureCollection', features: [quake()] });
  assert.equal(r.provider, 'usgs'); assert.equal(r.unmapped, 0); assert.equal(typeof r.fetchedAt, 'number');
  assert.match(r.coverage, /observation/i);
  assert.equal(r.features[0].properties.observed, 1700000000000);
  assert.equal(r.features[0].properties.severity, null);
  assert.deepEqual(Object.keys(r.features[0].properties).sort(), 'id title description source url category observed expires severity'.split(' ').sort());
});
test('null and invalid geometry never become invented markers', () => {
  for (const g of [null, { type: 'Point', coordinates: [181, 0] }, { type: 'Point', coordinates: [0, NaN] }, { type: 'Point', coordinates: ['1', 2] }, { type: 'Polygon', coordinates: [[[0,0],[1,0],[1,1]]] }]) {
    const r = feeds.normalizeNws({ type: 'FeatureCollection', features: [alert(g)] });
    assert.equal(r.unmapped, 1); assert.equal(r.features.length, 0);
  }
});
test('NWS preserves original dates, severity and real polygon geometry', () => {
  const g = { type: 'Polygon', coordinates: [[[0,0],[1,0],[1,1],[0,0]]] };
  const p = feeds.normalizeNws({ type: 'FeatureCollection', features: [alert(g)] }).features[0].properties;
  assert.equal(p.observed, '2026-10-24T12:00:00-07:00'); assert.equal(p.expires, '2026-10-24T13:00:00-07:00'); assert.equal(p.severity, 'Extreme'); assert.equal(p.category, 'tornado');
});
test('URLs reject executable, insecure, credentialed and malformed links without rewriting originals', () => {
  for (const url of ['javascript:alert(1)', 'http://example.org/', '//example.org', 'https://user:pass@example.org', 'garbage']) {
    assert.equal(feeds.normalizeEarthquakes({ type: 'FeatureCollection', features: [quake(point, { url })] }).features[0].properties.url, null);
  }
  const url = 'https://example.org/source?a=1#detail';
  assert.equal(feeds.normalizeEarthquakes({ type: 'FeatureCollection', features: [quake(point, { url, title: { bad: true } })] }).features[0].properties.url, url);
});
test('warning classification respects category boundaries and priority', () => {
  const cases = { 'Tornado Watch':'tornado', 'Severe Thunderstorm Warning':'storm', 'Flash Flood Warning':'flood', 'Coastal Flood Advisory':'coastal', 'Excessive Heat Warning':'heat', 'Extreme Cold Warning':'cold', 'Winter Storm Warning':'winter', 'Ice Storm Warning':'winter', 'Red Flag Warning':'fire', 'Fire Weather Watch':'fire', 'Freeze Warning':'cold', 'Hurricane Warning':'storm', 'High Surf Advisory':'coastal', 'Air Quality Alert':'other', 'Notornado Statement':'other' };
  for (const [name, category] of Object.entries(cases)) assert.equal(feeds.classifyNws(name), category, name);
  assert.equal(feeds.classifyNws(null), 'other');
});
test('EONET uses latest dated geometry, preserves date and observation distinction', () => {
  const event = { id:'e1', title:'Wildfire', categories:[{id:'wildfires'}], sources:[{url:'https://example.org/original'}], geometry:[{...point,date:'2026-10-24T00:00:00Z'}, {...point,coordinates:[2,3],date:'2026-10-23T00:00:00Z'}] };
  const r = feeds.normalizeEonet({ events:[event] });
  assert.deepEqual(r.features[0].geometry, point); assert.equal(r.features[0].properties.observed, event.geometry[0].date);
  assert.equal(r.features[0].properties.category,'fire'); assert.equal(r.features[0].properties.severity,null); assert.match(r.coverage,/not.*warning/i);
  event.geometry.push({type:'Point',coordinates:[999,0],date:'2026-10-25T00:00:00Z'});
  assert.equal(feeds.normalizeEonet({events:[event]}).unmapped,1);
});
test('malformed collections throw rather than report a false empty success', () => {
  for (const fn of [feeds.normalizeEarthquakes, feeds.normalizeNws, feeds.normalizeEonet]) assert.throws(() => fn({}));
});
test('browser export performs no network on evaluation', () => {
  const context = { window:{}, fetch(){throw Error('unexpected network');} };
  vm.runInNewContext(fs.readFileSync(require.resolve('../../map/feeds.js'),'utf8'),context);
  assert.equal(typeof context.window.NoriMapFeeds.load,'function');
});
test('load builds official requests, validates HTTP and JSON, and honors cancellation/timeout', async () => {
  const original = global.fetch;
  const timer = global.setTimeout;
  const urls = [];
  try {
    global.fetch = async (url, options) => { urls.push(String(url)); assert.ok(options.signal); return {ok:true,json:async()=>String(url).includes('eonet') ? {events:[]} : {type:'FeatureCollection',features:[]}}; };
    await feeds.load('usgs'); await feeds.load('nws');
    await feeds.load('eonet',{west:-125,east:-110,south:30,north:50});
    assert.equal(urls[0],'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson');
    assert.equal(urls[1],'https://api.weather.gov/alerts/active');
    assert.equal(new URL(urls[2]).searchParams.get('bbox'),'-125,50,-110,30');
    const wrapped = await feeds.load('eonet',{west:170,east:-170,south:-20,north:20});
    assert.equal(new URL(urls[3]).searchParams.has('bbox'),false); assert.match(wrapped.coverage,/whole.world/i);
    await assert.rejects(feeds.load('bad'),/provider/i);
    await assert.rejects(feeds.load('eonet',{west:NaN,east:0,south:0,north:1}),/bounds/i);
    global.fetch = async () => ({ok:false,status:503}); await assert.rejects(feeds.load('nws'),/503/);
    global.fetch = async () => ({ok:true,json:async()=>({})}); await assert.rejects(feeds.load('nws'),/invalid/i);
    const controller = new AbortController(); controller.abort(); await assert.rejects(feeds.load('usgs',null,controller.signal),{name:'AbortError'});
    global.fetch = (url,{signal}) => new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(signal.reason),{once:true}));
    const active = new AbortController(); const pending = feeds.load('nws',null,active.signal); active.abort(); await assert.rejects(pending,{name:'AbortError'});
    global.setTimeout = fn => timer(fn,1); await assert.rejects(feeds.load('nws'),/timeout/i);
  } finally { global.fetch=original; global.setTimeout=timer; }
});

test('EONET layer categories match volcano, landslide and dust controls', () => {
  for(const [id,expected] of [['volcanoes','volcano'],['landslides','landslide'],['dustHaze','dust']]) {
    const result=feeds.normalizeEonet({events:[{id:'event',title:id,categories:[{id}],geometry:[{...point,date:'2026-10-24T00:00:00Z'}]}]});
    assert.equal(result.features[0].properties.category,expected);
  }
});
