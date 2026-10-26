(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.NoriAviation = api;
})(typeof window !== 'undefined' ? window : null, function () {
  'use strict';
  const base = 'https://services6.arcgis.com/ssFJjBXIUyZDrSYZ/arcgis/rest/services/';
  const sourcePage = 'https://www.faa.gov/uas/commercial_operators/uas_facility_maps';
  const reference = 'https://faa.maps.arcgis.com/apps/webappviewer/index.html?id=9c2e4406710048e19806ebf6a06754ad';
  const notice = 'Informational only; this map does not authorize flight. Check current FAA requirements, restrictions and NOTAMs.';
  const definitions = [
    ['faa-uasfm', 'UAS facility grids', 'FAA_UAS_FacilityMap_Data', 12,
      'Maximum altitude for an authorization request without additional safety analysis; not an authorization or a global no-fly layer.',
      'OBJECTID,CEILING,UNIT,MAP_EFF,LAST_EDIT,APT1_NAME,APT1_FAAID'],
    ['faa-controlled', 'Controlled airspace', 'Class_Airspace', 10,
      'Published Class B, C, D and E airspace boundaries; vertical limits matter and are not a determination of permission to fly.',
      'OBJECTID,NAME,CLASS,TYPE_CODE,LOWER_VAL,LOWER_UOM,LOWER_CODE,LOWER_DESC,UPPER_VAL,UPPER_UOM,UPPER_CODE,UPPER_DESC'],
    ['faa-special-use', 'Special use airspace', 'Special_Use_Airspace', 10,
      'Published special use airspace, including restricted areas; published boundaries do not establish current activation.',
      'OBJECTID,NAME,TYPE_CODE,CLASS,LOWER_VAL,LOWER_UOM,LOWER_CODE,LOWER_DESC,UPPER_VAL,UPPER_UOM,UPPER_CODE,UPPER_DESC,TIMESOFUSE,REMARKS'],
    ['faa-prohibited', 'Prohibited areas', 'Prohibited_Areas', 10,
      'Published prohibited airspace boundaries and vertical limits; consult current official restrictions.',
      'OBJECTID,NAME,TYPE_CODE,CLASS,LOWER_VAL,LOWER_UOM,LOWER_CODE,LOWER_DESC,UPPER_VAL,UPPER_UOM,UPPER_CODE,UPPER_DESC,TIMESOFUSE,REMARKS'],
    ['faa-security', 'National security UAS restrictions', 'DoD_Mar_13', 11,
      'Published national security UAS restrictions; this layer is not a complete inventory of temporary or part-time restrictions.',
      'OBJECTID,Facility,Base,FAA_ID,Reason,Floor,Ceiling']
  ];
  const catalog = Object.freeze(definitions.map(([id,label,service,minZoom,description]) => Object.freeze({
    id, label, coverage:'United States', minZoom, url:base + service + '/FeatureServer/0/query',
    sourcePage:id === 'faa-uasfm' ? sourcePage : reference, description, available:true
  })));
  const byId = new Map(catalog.map((entry,i) => [entry.id, { entry, fields:definitions[i][5] }]));
  // Accept flat W/S/E/N, MapLibre toArray(), or a MapLibre LngLatBounds object.
  // Refuse wide/invalid bounds instead of silently querying a different viewport.
  function envelope(bounds) {
    let values = bounds;
    if (bounds && typeof bounds.getWest === 'function') {
      values = [bounds.getWest(),bounds.getSouth(),bounds.getEast(),bounds.getNorth()];
    } else if (Array.isArray(bounds) && bounds.length === 2 && bounds.every(Array.isArray)) {
      values = [...bounds[0],...bounds[1]];
    }
    if (!Array.isArray(values) || values.length !== 4 || !values.every(v => typeof v === 'number' && Number.isFinite(v))) {
      throw new Error('Invalid viewport bounds: expected finite west, south, east, north');
    }
    const [xmin,ymin,xmax,ymax] = values;
    if (xmin < -180 || xmax > 180 || ymin < -90 || ymax > 90 || xmin >= xmax || ymin >= ymax || xmax-xmin > 2 || ymax-ymin > 2) {
      throw new Error('Invalid or oversized viewport bounds: use at most 2 degrees per axis; split antimeridian views');
    }
    return {xmin,ymin,xmax,ymax,spatialReference:{wkid:4326}};
  }
  function text(value) { return value == null ? null : String(value).slice(0,2000); }
  function numeric(value) {
    if (value == null || String(value).trim() === '') return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  function boundary(p, prefix) {
    return { value:numeric(p[prefix+'_VAL']), unit:text(p[prefix+'_UOM']), reference:text(p[prefix+'_CODE']),
      descriptor:text(p[prefix+'_DESC']), meaning:'Published '+prefix.toLowerCase()+' airspace boundary' };
  }
  function boundaryText(a) {
    return [a.value == null ? 'value not supplied' : a.value, a.unit, a.reference, a.descriptor].filter(v=>v !== null).join(' ');
  }
  function normalize(feature, entry) {
    const p = feature.properties || {};
    const sourceId = p.OBJECTID ?? feature.id;
    const properties = {
      id:sourceId == null ? null : entry.id+':'+text(sourceId),
      title:text(p.APT1_NAME || p.NAME || p.Facility || p.Base || entry.label),
      description:entry.description+' '+notice, source:'FAA', url:entry.sourcePage,
      category:entry.id, observed:null, expires:null,
      // Severity indicates review context, never current activation or legality.
      severity:entry.id === 'faa-uasfm' ? 'info' : 'caution'
    };
    if (entry.id === 'faa-uasfm') {
      properties.altitude = {value:numeric(p.CEILING),unit:text(p.UNIT),reference:'AGL',
        meaning:'Maximum altitude for an authorization request without additional safety analysis'};
      const a = properties.altitude;
      properties.description += ' Request-guidance altitude: '+(a.value == null ? 'not supplied' : a.value+' '+(a.unit || '(unit not supplied)')+' AGL')+'.';
      // Preserve date-only source strings without manufacturing observation/expiry instants.
      properties.effectiveDate = text(p.MAP_EFF);
      properties.lastEdited = text(p.LAST_EDIT);
      properties.airportId = text(p.APT1_FAAID);
    } else if (entry.id === 'faa-security') {
      properties.floor = text(p.Floor);
      properties.ceiling = text(p.Ceiling);
      properties.reason = text(p.Reason);
      properties.description += ' Published floor: '+(properties.floor || 'not supplied')+'; ceiling: '+(properties.ceiling || 'not supplied')+'.';
    } else {
      properties.lowerAltitude = boundary(p,'LOWER');
      properties.upperAltitude = boundary(p,'UPPER');
      properties.airspaceClass = text(p.CLASS);
      properties.airspaceType = text(p.TYPE_CODE);
      properties.timesOfUse = text(p.TIMESOFUSE);
      properties.remarks = text(p.REMARKS);
      properties.description += ' Published lower boundary: '+boundaryText(properties.lowerAltitude)+'; upper boundary: '+boundaryText(properties.upperAltitude)+'.';
    }
    return { type:'Feature', id:properties.id, geometry:feature.geometry, properties };
  }
  async function query(id, bounds, signal) {
    const config = byId.get(id);
    if (!config || !config.entry.available) throw new Error('Unknown or unavailable FAA dataset: '+id);
    const geometry = envelope(bounds);
    const params = new URLSearchParams({
      where:id === 'faa-controlled' ? "CLASS IN ('B','C','D','E')" : '1=1',
      geometry:JSON.stringify(geometry), geometryType:'esriGeometryEnvelope',
      spatialRel:'esriSpatialRelIntersects', inSR:'4326', outSR:'4326',
      outFields:config.fields, returnGeometry:'true', returnZ:'false', returnM:'false',
      resultRecordCount:'400', orderByFields:'OBJECTID ASC', f:'geojson'
    });
    const response = await fetch(config.entry.url+'?'+params, {signal,mode:'cors',credentials:'omit'});
    if (!response.ok) throw new Error('FAA query HTTP '+response.status);
    const data = await response.json();
    if (data && data.error) {
      const e = data.error;
      throw new Error('FAA ArcGIS '+e.code+': '+text(e.message)+' '+(Array.isArray(e.details) ? e.details.map(text).join('; ') : ''));
    }
    if (!data || data.type !== 'FeatureCollection' || !Array.isArray(data.features) ||
        data.features.some(f => !f || f.type !== 'Feature' || !f.geometry || !['Polygon','MultiPolygon'].includes(f.geometry.type) || !Array.isArray(f.geometry.coordinates))) {
      throw new Error('FAA query returned invalid GeoJSON');
    }
    return { features:data.features.slice(0,400).map(f=>normalize(f,config.entry)), provider:'FAA', coverage:'United States',
      fetchedAt:new Date().toISOString(), limited:data.exceededTransferLimit === true ||
        data.properties?.exceededTransferLimit === true || data.features.length >= 400 };
  }
  return Object.freeze({catalog, query});
});
