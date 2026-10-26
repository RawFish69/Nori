/* Browser-only public feeds. Importing this module never fetches.
 * EONET metadata describes observations, not official warnings:
 * https://eonet.gsfc.nasa.gov/docs/v3
 * NWS alert semantics: https://www.weather.gov/documentation/services-web-alerts
 * Callers own caching, filtering and rendering; render text as text, never HTML.
 */
(function (root) {
  'use strict';
  const text = value => typeof value === 'string' ? value : null;
  const scalar = value => text(value) ?? (typeof value === 'number' && Number.isFinite(value) ? value : null);
  function safeUrl(value) {
    if (typeof value !== 'string' || !/^https:\/\//i.test(value) || /[\s\u0000-\u001f\u007f]/.test(value)) return null;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && url.hostname && !url.username && !url.password ? value : null;
    } catch (_) { return null; }
  }
  function position(p) {
    return Array.isArray(p) && p.length >= 2 && p.length <= 3 && p.every(n => typeof n === 'number' && Number.isFinite(n)) && Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 90;
  }
  const line = p => Array.isArray(p) && p.length >= 2 && p.every(position);
  const ring = p => line(p) && p.length >= 4 && p[0].length === p[p.length - 1].length && p[0].every((n, i) => n === p[p.length - 1][i]);
  const polygon = p => Array.isArray(p) && p.length > 0 && p.every(ring);
  function geometry(g) {
    if (!g || typeof g !== 'object') return null;
    const c = g.coordinates;
    const many = check => Array.isArray(c) && c.length > 0 && c.every(check);
    const valid = g.type === 'Point' ? position(c) : g.type === 'MultiPoint' ? many(position) : g.type === 'LineString' ? line(c) : g.type === 'MultiLineString' ? many(line) : g.type === 'Polygon' ? polygon(c) : g.type === 'MultiPolygon' ? many(polygon) : false;
    return valid ? { type: g.type, coordinates: JSON.parse(JSON.stringify(c)) } : null;
  }
  function classifyNws(name) {
    const s = typeof name === 'string' ? name.toLowerCase() : '';
    if (/\btornado\b/.test(s)) return 'tornado';
    if (/\b(coastal|lakeshore|surf|rip current|tsunami|storm surge)\b/.test(s)) return 'coastal';
    if (/\b(winter|snow|blizzard|ice|freezing rain)\b/.test(s)) return 'winter';
    if (/\b(flood|flooding|rain|rainstorm|rainfall)\b/.test(s)) return 'flood';
    if (/\b(heat)\b/.test(s)) return 'heat';
    if (/\b(cold|freeze|frost|wind chill)\b/.test(s)) return 'cold';
    if (/\b(fire|red flag)\b/.test(s)) return 'fire';
    if (/\b(fog|visibility)\b/.test(s)) return 'fog';
    if (/\bdrought\b/.test(s)) return 'drought';
    if (/\b(thunderstorm|storm|hurricane|typhoon|wind|gale|squall|lightning|hail|monsoon)\b/.test(s)) return 'storm';
    return 'other';
  }
  const coverage = {
    usgs: 'Global M2.5+ past-day earthquake observations; not official warnings.',
    eonet: 'NASA EONET open natural-event observations from the past 30 days, limited to 150 events; metadata is not a warning.',
    nws: 'Current US NWS watches, warnings, advisories and other active alert products; alerts without valid geometry are unmapped.'
  };
  function collection(data, key) {
    if (!data || !Array.isArray(data[key]) || (key === 'features' && data.type !== 'FeatureCollection')) throw new TypeError('Invalid feed response');
    return data[key];
  }
  function normalize(data, provider, key, convert) {
    const result = { features: [], unmapped: 0, provider, fetchedAt: Date.now(), coverage: coverage[provider] };
    for (const item of collection(data, key)) {
      const mapped = convert(item || {});
      const g = geometry(mapped.geometry);
      if (!g) { result.unmapped++; continue; }
      result.features.push({ type: 'Feature', geometry: g, properties: mapped.properties });
    }
    return result;
  }
  function properties(p) {
    return { id: scalar(p.id), title: text(p.title), description: text(p.description), source: text(p.source), url: safeUrl(p.url), category: text(p.category), observed: scalar(p.observed), expires: scalar(p.expires), severity: text(p.severity) };
  }
  function normalizeEarthquakes(data) {
    return normalize(data, 'usgs', 'features', f => {
      const p = f.properties || {};
      return { geometry: f.geometry, properties: properties({ id: f.id, title: p.title, description: p.place, source: 'USGS', url: p.url, category: 'earthquake', observed: p.time }) };
    });
  }
  function normalizeEonet(data) {
    return normalize(data, 'eonet', 'events', e => {
      // Choose by date, never array order; do not fall back to stale geometry.
      const dated = (Array.isArray(e.geometry) ? e.geometry : []).filter(g => g && typeof g.date === 'string' && Number.isFinite(Date.parse(g.date)));
      const latest = dated.reduce((a, b) => !a || Date.parse(b.date) > Date.parse(a.date) ? b : a, null);
      const categories = Array.isArray(e.categories) ? e.categories.map(c => c && c.id) : [];
      const category = categories.includes('wildfires') ? 'fire' : categories.includes('severeStorms') ? 'storm' : categories.includes('floods') ? 'flood' : categories.includes('earthquakes') ? 'earthquake' : categories.includes('volcanoes') ? 'volcano' : categories.includes('landslides') ? 'landslide' : categories.includes('dustHaze') ? 'dust' : 'other';
      const sources = Array.isArray(e.sources) ? e.sources : [];
      const url = sources.map(s => safeUrl(s && s.url)).find(Boolean) || safeUrl(e.link);
      return { geometry: latest, properties: properties({ id: e.id, title: e.title, description: e.description, source: 'NASA EONET', url, category, observed: latest && latest.date }) };
    });
  }
  function normalizeNws(data) {
    return normalize(data, 'nws', 'features', f => {
      const p = f.properties || {};
      return { geometry: f.geometry, properties: properties({ id: p.id ?? f.id, title: p.headline ?? p.event, description: p.description, source: 'NWS', url: safeUrl(p['@id']) || safeUrl(f.id) || safeUrl(p.id), category: classifyNws(p.event), observed: p.sent, expires: p.expires, severity: p.severity }) };
    });
  }
  function normalizeHko(data, now=Date.now()) {
    const keys=['WFIRE','WFROST','WHOT','WCOLD','WMSGNL','WRAIN','WFNTSA','WL','WTCSGNL','WTMW','WTS'];
    if(!data||Array.isArray(data)||typeof data!=='object'||Object.keys(data).some(k=>!keys.includes(k)))throw new TypeError('Invalid HKO response');
    const active=[];
    for(const p of Object.values(data)){
      if(!p||typeof p.name!=='string'||typeof p.code!=='string'||!['ISSUE','REISSUE','CANCEL','EXTEND','UPDATE'].includes(p.actionCode))throw new TypeError('Invalid HKO warning');
      if(p.actionCode==='CANCEL'||p.code==='CANCEL')continue;
      if(!Number.isFinite(Date.parse(p.issueTime))||!Number.isFinite(Date.parse(p.updateTime||p.issueTime)))throw new TypeError('Invalid HKO source date');
      if(p.expireTime){if(!Number.isFinite(Date.parse(p.expireTime)))throw new TypeError('Invalid HKO expiry');if(Date.parse(p.expireTime)<=now)continue;}
      active.push(p);
    }
    const geometryNote='Regional summary: this marker is a Hong Kong reference point, not a hazard location or affected boundary. Read the source for affected areas and signal meaning.';
    const categories={WFIRE:'fire',WFROST:'cold',WHOT:'heat',WCOLD:'cold',WMSGNL:'storm',WRAIN:'flood',WFNTSA:'flood',WL:'landslide',WTCSGNL:'storm',WTMW:'coastal',WTS:'storm'};
    const grouped=new Map();
    for(const [key,p] of Object.entries(data)){if(!active.includes(p))continue;const category=categories[key];if(!grouped.has(category))grouped.set(category,[]);grouped.get(category).push(p)}
    const features=[...grouped].map(([category,signals])=>{const latest=signals.slice().sort((a,b)=>Date.parse(b.updateTime||b.issueTime)-Date.parse(a.updateTime||a.issueTime))[0];const description=signals.map(p=>[p.name,p.type,p.code,'Issued: '+p.issueTime,'Updated: '+(p.updateTime||p.issueTime),p.expireTime?'Expires: '+p.expireTime:''].filter(Boolean).join(' · ')).join('\n\n');return {type:'Feature',geometry:{type:'Point',coordinates:[114.1694,22.3193]},properties:{...properties({id:'hko-'+category,title:'Hong Kong · '+signals.map(p=>p.name).join(', '),description,source:'Hong Kong Observatory',url:'https://www.hko.gov.hk/en/wxinfo/warn.htm',category,observed:latest.updateTime||latest.issueTime}),scope:'regional-summary',regionLabel:'Hong Kong',reportCount:signals.length,geometryNote}}});
    return {provider:'hko',fetchedAt:now,unmapped:0,reportCount:active.length,coverage:'Hong Kong warning signals only; categorized regional summaries, no hazard footprints.',features};
  }

  function normalizeChina(data){
    if(!Number.isFinite(data?.fetchedAt)||Date.now()-data.fetchedAt>900000||data.type!=='FeatureCollection'||!Array.isArray(data.features)||data.features.length>500)throw new TypeError('Invalid China relay response');
    const result=normalize(data,'cma','features',f=>({geometry:f.geometry,properties:{...properties(f.properties||{}),scope:text(f.properties?.scope),snapshotExpiresAt:data.fetchedAt+900000,regionLabel:text(f.properties?.regionLabel)||text(f.properties?.province),reportCount:Number.isFinite(f.properties?.reportCount)?f.properties.reportCount:0,geometryNote:text(f.properties?.geometryNote)}}));
    if(data.stale===true)for(const feature of result.features)feature.properties.geometryNote=(feature.properties.geometryNote||'Regional summary.')+' Stale cached snapshot; last fetched '+new Date(data.fetchedAt).toISOString()+'.';
    return {...result,fetchedAt:data.fetchedAt,stale:data.stale===true,limited:data.limited===true,reportCount:Number.isFinite(data.reportCount)?data.reportCount:0,unmapped:result.unmapped+(Number.isFinite(data.unmapped)?data.unmapped:0),coverage:text(data.coverage)||'Mainland China recent reports; not an active-warning inventory.'};
  }
  async function load(provider, bounds, signal) {
    const normalizers = { usgs: normalizeEarthquakes, eonet: normalizeEonet, nws: normalizeNws, hko: normalizeHko, cma: normalizeChina };
    if (!Object.prototype.hasOwnProperty.call(normalizers, provider)) throw new TypeError('Unknown provider');
    let url = provider==='hko'?'https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=warnsum&lang=en':provider==='cma'?'https://nori.fish/api/map/china-alerts':provider === 'usgs' ? 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson' : provider === 'nws' ? 'https://api.weather.gov/alerts/active' : 'https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=30&limit=150';
    let wrapped = false;
    if (provider === 'eonet' && bounds != null) {
      const { west, east, south, north } = bounds;
      if (![west,east,south,north].every(n => typeof n === 'number' && Number.isFinite(n)) || Math.abs(west) > 180 || Math.abs(east) > 180 || Math.abs(south) > 90 || Math.abs(north) > 90 || south > north) throw new TypeError('Invalid bounds');
      wrapped = west > east;
      // Wrapped bounds deliberately query the whole world, capped at 150.
      // Caller filters results; a single bbox cannot represent this viewport.
      if (!wrapped) url += '&bbox=' + [west,north,east,south].join(',');
    }
    const controller = new AbortController();
    const abort = () => controller.abort(signal.reason);
    if (signal && signal.aborted) { signal.throwIfAborted(); }
    if (signal) signal.addEventListener('abort', abort, { once: true });
    const timer = setTimeout(() => controller.abort(new DOMException('Feed request timeout', 'TimeoutError')), 15000);
    // Race also bounds JSON parsing and fetch implementations that ignore abort.
    let onAbort;
    const interrupted = new Promise((_, reject) => {
      onAbort = () => reject(controller.signal.reason);
      controller.signal.addEventListener('abort', onAbort, { once: true });
    });
    try {
      const result = await Promise.race([interrupted, (async () => {
        const response = await fetch(url, { signal: controller.signal, headers: { Accept: 'application/geo+json, application/json' } });
        if (!response || !response.ok) throw new Error('Feed HTTP error ' + (response && response.status));
        const data = await response.json();
        return normalizers[provider](data);
      })()]);
      if (wrapped) result.coverage += ' Antimeridian viewport: whole-world query; caller must filter.';
      return result;
    } finally {
      clearTimeout(timer);
      controller.signal.removeEventListener('abort', onAbort);
      if (signal) signal.removeEventListener('abort', abort);
    }
  }
  const api = { normalizeEarthquakes, normalizeEonet, normalizeNws, normalizeHko, normalizeChina, classifyNws, load };
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.NoriMapFeeds = api;
})(typeof window === 'object' ? window : null);
