const {test}=require('node:test'),assert=require('node:assert/strict'),P=require('../../map/preferences.js');
test('Chinese UI text and dynamic status preserve numbers and coordinates',()=>{assert.equal(P.t('zh','Layers'),'图层');assert.equal(P.t('en','Layers'),'Layers');assert.equal(P.t('zh','Wuxi'),'无锡');assert.equal(P.t('zh','Zoom to 12 to load local detail'),'放大至 12 级以加载本地详情');assert.equal(P.t('zh','Browser-reported accuracy: ±35 m'),'浏览器报告的位置精度：±35 米');assert.equal(P.t('zh','Pin: 34 N, 118 W'),'标记：34 N, 118 W');assert.equal(P.t('zh','Unknown official report'),'Unknown official report')});
test('Chinese map labels prefer native Chinese and fall back to available names',()=>{const e=P.labelExpression('zh');assert.deepEqual(e[1],['get','name:zh-Hans']);assert(e.some(v=>Array.isArray(v)&&v[1]==='name:en'));assert.deepEqual(P.labelExpression('en')[1],['get','name:en'])});
test('color basemap distinguishes water, parks and road hierarchy in light and dark',()=>{for(const dark of [false,true]){const s={layers:[{id:'background',type:'background'},{id:'water',type:'fill'},{id:'park',type:'fill'},{id:'highway_minor',type:'line'},{id:'highway_motorway_inner',type:'line'}]};P.colorize(s,dark);assert.notEqual(s.layers[1].paint['fill-color'],s.layers[2].paint['fill-color']);assert.notEqual(s.layers[3].paint['line-color'],s.layers[4].paint['line-color']);assert.equal(s.layers.length,5)}});

test('static translations can switch repeatedly without losing their original language',()=>{
 let language='en',i=0;const nodes=['Layers','Color'].map(nodeValue=>({nodeValue,parentElement:{closest:()=>null}}));
 const root={ownerDocument:{createTreeWalker:()=>({nextNode:()=>nodes[i++]||null})},querySelectorAll:()=>[]};const render=P.bindStatic(root,()=>language);
 render();language='zh';render();assert.deepEqual(nodes.map(n=>n.nodeValue),['图层','彩色']);language='en';render();assert.deepEqual(nodes.map(n=>n.nodeValue),['Layers','Color']);
});
