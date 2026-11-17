"""Web version of the Casa 01 lookbook with the interactive 3D viewer.
Called from build.py; writes casa01/lookbook/web/index.html (+ img/)."""
import json
import os
import shutil

import design as D
from build import (A, FACTS, MOVES, SWATCHES, HERE, WEB, quantities, room_rows, svg_inline)

WEB_CSS = r"""
:root{--bg:#f6f4ee;--fg:#1d2520;--muted:#646a63;--line:#dcd8cd;--card:#ffffff;--sage:#5f7458;--gold:#a8844a;--chip:#ece5d4;
--serif:'Cormorant Garamond',Georgia,'Times New Roman',serif;--sans:'Lato','Helvetica Neue',Arial,sans-serif}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141916;--fg:#ece8de;--muted:#a5aa9f;--line:#2f3832;--card:#1c221e;--sage:#9db493;--gold:#d2b47c;--chip:#2a312c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141916;--fg:#ece8de;--muted:#a5aa9f;--line:#2f3832;--card:#1c221e;--sage:#9db493;--gold:#d2b47c;--chip:#2a312c;color-scheme:dark}
*{box-sizing:border-box}
[hidden]{display:none!important}
body{background:var(--bg);color:var(--fg);font-family:var(--sans);font-size:15px;line-height:1.55;margin:0}
.wrap{max-width:1240px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header.top{padding-block:28px 18px}
.eyebrow{font:700 11.5px/1.2 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--sage)}
h1{font-family:var(--serif);font-weight:500;font-size:clamp(40px,6vw,72px);line-height:1;margin:8px 0 0;text-wrap:balance}
h2{font-family:var(--serif);font-weight:500;font-size:clamp(28px,3.6vw,42px);line-height:1.05;margin:6px 0 0;text-wrap:balance}
.lede{max-width:62ch;color:var(--muted);margin:12px 0 0;font-size:16px}
.facts{display:flex;flex-wrap:wrap;border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-top:22px}
.facts div{flex:1 1 140px;padding:12px 16px 12px 0}
.facts .n{font-family:var(--serif);font-size:32px;line-height:1}
.facts .l{font:700 10px/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-top:4px}
.viewer{position:relative;height:min(74vh,760px);min-height:440px;background:#cfdde6;border-radius:4px;overflow:hidden;margin-top:22px}
.viewer canvas{display:block;width:100%;height:100%;touch-action:none;cursor:grab}
.vbar{position:absolute;left:12px;right:12px;top:12px;display:flex;flex-wrap:wrap;gap:6px;pointer-events:none}
.vbar button,.vctl select{pointer-events:auto;font:700 11px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;border:0;background:rgba(246,244,238,.92);color:#1d2520;padding:9px 11px;border-radius:2px;cursor:pointer}
.vbar button[aria-pressed="true"]{background:#1d2520;color:#f3efe4}
.vbar button:focus-visible,.vctl select:focus-visible,.vctl input:focus-visible{outline:2px solid #b8955a;outline-offset:2px}
.vctl{position:absolute;left:12px;right:12px;bottom:12px;display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;background:rgba(29,37,32,.84);color:#f3efe4;padding:10px 12px;border-radius:2px}
.vctl label{font:700 10.5px/1 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:#d8c9a4}
.vctl input[type=range]{flex:1 1 160px;min-width:120px;accent-color:#b8955a}
.vctl .time{font:700 13px/1 var(--sans);font-variant-numeric:tabular-nums;min-width:118px}
.vctl select{padding:7px 8px}
.pick{position:absolute;right:12px;top:64px;max-width:min(320px,calc(100% - 24px));background:rgba(246,244,238,.96);color:#1d2520;padding:12px 14px;border-radius:2px;font-size:13px;line-height:1.4;box-shadow:0 4px 18px rgba(0,0,0,.15);cursor:pointer}
.pick b{display:block;font:700 12px/1.2 var(--sans);letter-spacing:.06em;text-transform:uppercase}
.pick i{font-family:var(--serif);font-size:15px;color:#8a6a35}
.pano .loading{background:#1d2520;color:#f3efe4}
.loading{position:absolute;inset:0;display:grid;place-items:center;font:700 12px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:#1d2520;background:#cfdde6;text-align:center;padding:20px}
.hint{font-size:12.5px;color:var(--muted);margin-top:8px}
.pano{position:relative;height:min(70vh,700px);min-height:400px;background:#1d2520;border-radius:4px;overflow:hidden;margin-top:22px}
.pano canvas{display:block;width:100%;height:100%;touch-action:none;cursor:grab}
section.block{padding-block:56px 8px}
.gal{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:22px}
.gal figure{margin:0;min-width:0}
.gal figure.wide{grid-column:1/-1}
.gal img{width:100%;height:auto;display:block;border-radius:2px;background:var(--chip)}
figcaption{font-size:13.5px;color:var(--muted);margin-top:8px;max-width:75ch}
figcaption b{color:var(--fg);font:700 11px/1 var(--sans);letter-spacing:.1em;text-transform:uppercase;margin-right:8px}
.paper{background:#fff;border:1px solid var(--line);border-radius:2px;padding:10px;overflow-x:auto}
.paper svg{display:block;width:100%;height:auto;min-width:640px}
.dwgs{display:grid;gap:22px;margin-top:22px}
.dwgs .two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.dwgs .two>div{min-width:0}
.dwgs h3{font:700 11.5px/1.2 var(--sans);letter-spacing:.12em;text-transform:uppercase;margin:0 0 8px;color:var(--fg)}
.sw{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:18px;margin-top:22px}
.sw img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;border:1px solid var(--line)}
.sw h4{margin:8px 0 0;font:700 13px/1.25 var(--sans)}
.sw .br{font-family:var(--serif);font-style:italic;color:var(--gold);font-size:16px;line-height:1.15}
.sw .sp{font-size:12px;color:var(--muted);line-height:1.35}
.cols{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:32px;margin-top:22px}
.tbl{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{font:700 10.5px/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px;border-bottom:1px solid var(--fg)}
td{padding:8px;border-bottom:1px solid var(--line);vertical-align:top}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.kv{display:grid;grid-template-columns:1fr auto;border-top:1px solid var(--line);font-size:14px}
.kv div{padding:8px 0;border-bottom:1px solid var(--line)}
.kv div:nth-child(2n){text-align:right;font-weight:700;font-variant-numeric:tabular-nums;padding-left:12px}
.note{background:var(--chip);padding:14px 16px;font-size:13.5px;margin-top:16px;border-radius:2px}
.note b{display:block;font:700 10.5px/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--sage);margin-bottom:6px}
.moves{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;margin-top:22px}
.moves h3{margin:0;font:700 15px/1.25 var(--sans)}
.moves p{margin:6px 0 0;color:var(--muted);font-size:14px}
.moves .k{font-family:var(--serif);font-size:34px;color:var(--gold);line-height:1}
footer{padding-block:48px 40px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--line);margin-top:56px}
@media (max-width:760px){.gal,.dwgs .two,.cols,.moves{grid-template-columns:1fr}.viewer{height:68vh;min-height:420px}.vctl .time{min-width:auto}}
"""

VIEWER_JS = r"""
(function(){
const M=0.3048, el=document.getElementById('viewer'), canvas=el.querySelector('canvas');
const T=p=>new THREE.Vector3(p[0]*M,p[2]*M,-p[1]*M);
const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const MODEL='__MODEL__', LMAPS=__LIGHTMAPS__, SKY_AZ=__SKYAZ__, CB=__COBOGO__;
let renderer;
try{renderer=new THREE.WebGLRenderer({canvas,antialias:true});}catch(e){document.getElementById('loading').textContent='3D needs WebGL, which this browser has turned off. The renders and plans below still work.';return}
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.outputEncoding=THREE.sRGBEncoding;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
const scene=new THREE.Scene();scene.background=new THREE.Color('#bcd3e4');scene.fog=new THREE.Fog(new THREE.Color('#c9d6df'),110,330);
const camera=new THREE.PerspectiveCamera(50,1,0.1,900);
const controls=new THREE.OrbitControls(camera,canvas);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*0.495;controls.minDistance=0.5;controls.maxDistance=180;
const hemi=new THREE.HemisphereLight(0xdfe8ee,0x8c7b62,LMAPS?0.0:0.65);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xfff0d8,2.6);sun.castShadow=true;
const small=Math.min(window.innerWidth,window.innerHeight)<700;
sun.shadow.mapSize.set(small?2048:4096,small?2048:4096);
const C=T([32,62,0]);const sc=sun.shadow.camera;sc.left=-26;sc.right=26;sc.top=26;sc.bottom=-26;sc.near=1;sc.far=150;sun.shadow.bias=-0.0003;sun.shadow.normalBias=0.025;
sun.target.position.copy(C);scene.add(sun);scene.add(sun.target);
const night=[];[[36,33.4,10],[42,46,3],[27,86,10],[30,70,10],[14,72,10],[25.4,45,10],[31,106,2]].forEach(p=>{const l=new THREE.PointLight(0xffb36b,0,15,1.6);l.position.copy(T(p));scene.add(l);night.push(l)});
const VIEWS={street:[[55,-5.5,5.2],[30.5,30,6.6]],entry:[[47.2,34.6,5.85],[26,32.5,5.6]],patio:[[52.5,58.9,6.25],[30,40,6]],room:[[29.6,61,5.5],[41,71.5,4.6]],veranda:[[41.8,90.4,5.8],[20.5,83.8,5.4]],aerial:[[96,-38,72],[31,58,0]],plan:[[30.5,55,118],[30.5,56,0]]};
const roofObjs=[],hit=[],baked=[],lit=[];const info=__FINISHES__;
const pickEl=document.getElementById('pick'),loadEl=document.getElementById('loading');
const TL=new THREE.TextureLoader();
function tex(url,srgb,flip){const t=TL.load(url);if(srgb)t.encoding=THREE.sRGBEncoding;t.flipY=!!flip;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=renderer.capabilities.getMaxAnisotropy();return t}
// photographed sky on a big dome (rotated so its sun sits where the live sun is)
let skyMat=null,skyMesh=null;
if(LMAPS){const st=TL.load('tex/sky_day.jpg',t=>{const pm=new THREE.PMREMGenerator(renderer);scene.environment=pm.fromEquirectangular(t).texture;pm.dispose()});
  st.encoding=THREE.sRGBEncoding;st.mapping=THREE.EquirectangularReflectionMapping;
  const dome=TL.load('tex/sky_day.jpg');dome.encoding=THREE.sRGBEncoding;dome.wrapS=THREE.RepeatWrapping;dome.repeat.x=-1;dome.offset.x=0.5;
  skyMat=new THREE.MeshBasicMaterial({map:dome,side:THREE.BackSide,fog:false,depthWrite:false});
  skyMesh=new THREE.Mesh(new THREE.SphereGeometry(420,48,24),skyMat);skyMesh.renderOrder=-1;scene.add(skyMesh)}
const NM={web_limestone:['limestone',0.9],web_pavers:['limestone',0.6],web_stucco:['stucco',0.5],web_cedar_z:['cedar_rot',0.6],web_cedar_y:['cedar_rot',0.5],
  web_cedar_x:['cedar',0.5],web_fence:['cedar',0.6],web_floor:['concrete',0.25],web_concrete:['concrete',0.6],web_dg:['dg',0.9],web_bark:['bark',1.0],
  web_lawn_soil:['grass',0.8],web_asphalt:['asphalt',0.6],web_oak:['oak',0.3]};
const nmCache={};function nmap(k){return nmCache[k]||(nmCache[k]=tex('tex/'+k+'_n.jpg',false,false))}
function onModel(g){
  const root=g.scene;
  root.traverse(o=>{if(/^(Roof|Cedar_soffits|Cedar soffits)/.test(o.name))o.traverse(c=>roofObjs.push(c));
    if(!o.isMesh)return;o.castShadow=true;o.receiveShadow=true;hit.push(o);
    (Array.isArray(o.material)?o.material:[o.material]).forEach(m=>{const n=m.name||'';
      if(n==='web_glass'){m.color.set(0x0b1214);m.transparent=true;m.opacity=0.34;m.depthWrite=false;m.metalness=0;m.roughness=0.02;m.envMapIntensity=0.9;o.castShadow=false}
      if(n==='web_cobogo'||n.startsWith('web_leafcard')){m.alphaTest=0.5;m.transparent=false;m.side=THREE.DoubleSide}
      if(n.startsWith('web_leafcard')){o.receiveShadow=true}
      if(LMAPS&&NM[n]&&!m.normalMap){m.normalMap=nmap(NM[n][0]);m.normalScale=new THREE.Vector2(NM[n][1],NM[n][1])}
      if(n==='web_floor'){m.roughness=0.22}
      if(m.map){m.map.anisotropy=renderer.capabilities.getMaxAnisotropy()}});});
  // the cobogó: 210 real 12x12x4 blocks (one extruded block, instanced) instead of a flat cut-out
  // picture, so the screen has depth and blocks the view at an angle like the real thing
  root.traverse(o=>{if(/^Cobogo_screen/.test(o.name))o.traverse(c=>{c.visible=false})});
  {const b=CB.block*M,h=b/2,rc=0.24*b,re=0.085*b,PI=Math.PI,sh=new THREE.Shape();
    sh.moveTo(-h+rc,-h);sh.lineTo(-re,-h);sh.absarc(0,-h,re,PI,0,true);
    sh.lineTo(h-rc,-h);sh.absarc(h,-h,rc,PI,PI/2,true);
    sh.lineTo(h,-re);sh.absarc(h,0,re,1.5*PI,PI/2,true);
    sh.lineTo(h,h-rc);sh.absarc(h,h,rc,1.5*PI,PI,true);
    sh.lineTo(re,h);sh.absarc(0,h,re,0,-PI,true);
    sh.lineTo(-h+rc,h);sh.absarc(-h,h,rc,0,-PI/2,true);
    sh.lineTo(-h,re);sh.absarc(-h,0,re,PI/2,-PI/2,true);
    sh.lineTo(-h,-h+rc);sh.absarc(-h,-h,rc,PI/2,0,true);
    const hole=new THREE.Path();hole.absarc(0,0,0.30*b,0,2*PI,false);sh.holes.push(hole);
    const geo=new THREE.ExtrudeGeometry(sh,{depth:CB.t*M,bevelEnabled:false,curveSegments:14});
    const mat=new THREE.MeshStandardMaterial({name:'web_cobogo',color:new THREE.Color(0xd9d4c8),roughness:0.92,metalness:0});
    const nx=Math.round((CB.x1-CB.x0)/CB.block),nz=Math.round((CB.z1-CB.z0)/CB.block);
    const im=new THREE.InstancedMesh(geo,mat,nx*nz),mx=new THREE.Matrix4();let k=0;
    for(let i=0;i<nx;i++)for(let j=0;j<nz;j++){mx.makeScale(0.985,0.985,1);
      mx.setPosition((CB.x0+(i+0.5)*CB.block)*M,(CB.z0+(j+0.5)*CB.block)*M,-(CB.y+CB.t)*M);im.setMatrixAt(k++,mx)}
    im.castShadow=true;im.receiveShadow=true;im.name='Cobogo_blocks';root.add(im);hit.push(im)}
  // baked sky + bounce light: each baked object gets its own material copies with its lightmap
  if(LMAPS){root.traverse(o=>{const key=LMAPS.maps[o.name];if(!key)return;const lm=tex('lm/'+key,true,false);
    o.traverse(c=>{if(!c.isMesh||!c.geometry.attributes.uv2)return;
      const ms=(Array.isArray(c.material)?c.material:[c.material]).map(m=>{const k=m.clone();k.lightMap=lm;k.lightMapIntensity=1;k.envMapIntensity=0.2;baked.push(k);return k});
      c.material=Array.isArray(c.material)?ms:ms[0];})});
    root.traverse(o=>{if(!o.isMesh)return;(Array.isArray(o.material)?o.material:[o.material]).forEach(m=>{if(!m.lightMap&&!lit.includes(m))lit.push(m)})})}
  scene.add(root);loadEl.hidden=true;go('street',true);setSun();}
function failed(){loadEl.textContent='The 3D model did not load. Reload the page to try again.'}
// The page may not fetch data: or blob: URLs, so the model ships as glTF JSON with a base64
// buffer. Decode it here, rebuild a binary GLB in memory, and parse that (no extra requests).
(async()=>{try{
  const res=await fetch(MODEL);if(!res.ok)throw new Error(res.status);
  const total=+res.headers.get('content-length')||0;const reader=res.body.getReader();const chunks=[];let got=0;
  for(;;){const {done,value}=await reader.read();if(done)break;chunks.push(value);got+=value.length;
    if(total)loadEl.textContent='Loading 3D model '+Math.round(got/total*100)+'%'}
  loadEl.textContent='Building the scene';
  const txt=new TextDecoder().decode(await new Blob(chunks).arrayBuffer());
  const j=JSON.parse(txt);const uri=j.buffers[0].uri;delete j.buffers[0].uri;
  const b64=atob(uri.slice(uri.indexOf(',')+1));const bin=new Uint8Array(b64.length);
  for(let i=0;i<b64.length;i++)bin[i]=b64.charCodeAt(i);
  j.buffers[0].byteLength=bin.length;
  let js=new TextEncoder().encode(JSON.stringify(j));
  const jl=Math.ceil(js.length/4)*4,bl=Math.ceil(bin.length/4)*4;
  const glb=new ArrayBuffer(12+8+jl+8+bl),dv=new DataView(glb),u8=new Uint8Array(glb);
  dv.setUint32(0,0x46546C67,true);dv.setUint32(4,2,true);dv.setUint32(8,glb.byteLength,true);
  dv.setUint32(12,jl,true);dv.setUint32(16,0x4E4F534A,true);u8.fill(0x20,20,20+jl);u8.set(js,20);
  dv.setUint32(20+jl,bl,true);dv.setUint32(24+jl,0x004E4942,true);u8.set(bin,28+jl);
  const cib=window.createImageBitmap;try{window.createImageBitmap=undefined}catch(e){}
  new THREE.GLTFLoader().parse(glb,'',g=>{try{window.createImageBitmap=cib}catch(e){}onModel(g)},
    e=>{try{window.createImageBitmap=cib}catch(_){}console.error(e);failed()});
  try{window.createImageBitmap=cib}catch(e){}
}catch(e){console.error(e);failed()}})();
function size(){const w=el.clientWidth,h=el.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
new ResizeObserver(size).observe(el);size();
let tween=null,roofOn=true;const roofBtn=document.getElementById('roofbtn');
function setRoof(on){roofObjs.forEach(o=>o.visible=on);roofBtn.setAttribute('aria-pressed',String(!on));roofBtn.textContent=on?'Lift roof':'Put roof back'}
function go(name,instant){const v=VIEWS[name],p=T(v[0]),t=T(v[1]);
  if(name==='plan'){roofOn=false}else if(name!=='aerial'){roofOn=true}setRoof(roofOn);
  document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));
  if(instant||reduce){camera.position.copy(p);controls.target.copy(t);controls.update();return}
  tween={p0:camera.position.clone(),t0:controls.target.clone(),p1:p,t1:t,s:performance.now(),d:1100}}
roofBtn.addEventListener('click',()=>{roofOn=!roofOn;setRoof(roofOn)});
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>go(b.dataset.view)));
const timeEl=document.getElementById('t'),dateEl=document.getElementById('d'),tlab=document.getElementById('tl');
const skyDay=new THREE.Color('#bcd3e4'),skyDusk=new THREE.Color('#33415a'),skyGold=new THREE.Color('#efc79d');
function setSun(){const N=+dateEl.value,hrs=+timeEl.value,lat=30.27*Math.PI/180;
  const dec=23.44*Math.PI/180*Math.sin(2*Math.PI*(284+N)/365),h=(hrs-12)*15*Math.PI/180;
  const alt=Math.asin(Math.sin(lat)*Math.sin(dec)+Math.cos(lat)*Math.cos(dec)*Math.cos(h));
  const az=Math.atan2(Math.sin(h),Math.cos(h)*Math.sin(lat)-Math.tan(dec)*Math.cos(lat))+Math.PI;
  const d=new THREE.Vector3(Math.sin(az)*Math.cos(alt),Math.sin(alt),-Math.cos(az)*Math.cos(alt));
  sun.position.copy(C).addScaledVector(d,80);
  const e=Math.max(0,Math.sin(alt));
  sun.intensity=(LMAPS?3.0:2.8)*Math.min(1,e*2.2);sun.color.setHSL(0.09,0.85-0.55*Math.min(1,e*2),0.5+0.42*Math.min(1,e*1.6));
  const day=Math.min(1,e*3.2),skyLevel=0.04+0.96*Math.min(1,e*4);
  hemi.intensity=LMAPS?0.0:0.14+0.55*day;
  const sky=skyDusk.clone().lerp(skyGold,Math.min(1,e*9)).lerp(skyDay,Math.min(1,Math.max(0,(e-0.07)*6)));
  scene.background.copy(sky);scene.fog.color.copy(sky).lerp(new THREE.Color('#ffffff'),0.12);
  if(LMAPS){baked.forEach(m=>{m.lightMapIntensity=1.15*skyLevel;m.envMapIntensity=0.18*skyLevel});
    lit.forEach(m=>{if(m.name!=='web_glass')m.envMapIntensity=1.5*skyLevel});
    if(skyMesh){skyMesh.rotation.y=(SKY_AZ-az*180/Math.PI)*Math.PI/180;
      const dusk=new THREE.Color(1,1,1).lerp(new THREE.Color('#ffbe8a'),Math.max(0,1-e*6)*0.6).multiplyScalar(0.1+0.9*Math.min(1,e*5));
      skyMat.color.copy(dusk);skyMesh.visible=e>0.005}}
  const nightAmt=Math.max(0,1-e*8);night.forEach(l=>l.intensity=nightAmt*2.4);
  const hh=Math.floor(hrs),mm=Math.round((hrs-hh)*60)%60;
  tlab.textContent=((hh+11)%12+1)+':'+String(mm).padStart(2,'0')+(hrs<12?' am':' pm')+(alt<0?' · dark':'')}
timeEl.addEventListener('input',setSun);dateEl.addEventListener('change',setSun);
const ray=new THREE.Raycaster(),ptr=new THREE.Vector2();let down=null;
canvas.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];tween=null});
canvas.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
  const r=canvas.getBoundingClientRect();ptr.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(ptr,camera);
  const hs=ray.intersectObjects(hit.filter(o=>o.visible&&(o.parent?o.parent.visible:true)),false);if(!hs.length)return;
  let m=hs[0].object.material;if(Array.isArray(m))m=m[0];const f=info[(m.name||'').replace('web_','').replace(/_[ab]$/,'')];
  if(!f){pickEl.hidden=true;return}
  pickEl.innerHTML='<b>'+f[0]+'</b>'+(f[1]?'<i>Brazilian reference: '+f[1]+'</i><br>':'')+f[2];pickEl.hidden=false});
pickEl.addEventListener('click',()=>pickEl.hidden=true);
function loop(now){requestAnimationFrame(loop);if(tween){let k=Math.min(1,(now-tween.s)/tween.d);k=k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2;
  camera.position.lerpVectors(tween.p0,tween.p1,k);controls.target.lerpVectors(tween.t0,tween.t1,k);if(k>=1)tween=null}
  if(skyMesh)skyMesh.position.copy(camera.position);
  controls.update();renderer.render(scene,camera)}
requestAnimationFrame(loop);
})();
"""

PANO_JS = r"""
(function(){
const el=document.getElementById('pano');if(!el)return;const canvas=el.querySelector('canvas'),lo=document.getElementById('pload');
let renderer;try{renderer=new THREE.WebGLRenderer({canvas,antialias:true})}catch(e){lo.textContent='The 360° tour needs WebGL.';return}
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));renderer.outputEncoding=THREE.sRGBEncoding;
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(72,1,0.1,100);camera.position.set(0.01,0,0);
const geo=new THREE.SphereGeometry(50,96,48);geo.scale(-1,1,1);
const mat=new THREE.MeshBasicMaterial({color:0x222222});scene.add(new THREE.Mesh(geo,mat));
const controls=new THREE.OrbitControls(camera,canvas);controls.enableZoom=false;controls.enablePan=false;controls.rotateSpeed=-0.32;controls.enableDamping=true;
const TL=new THREE.TextureLoader();const cache={};
function show(k){document.querySelectorAll('[data-pano]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.pano===k)));
  lo.hidden=false;lo.textContent='Loading view';
  const done=t=>{mat.map=t;mat.color.set(0xffffff);mat.needsUpdate=true;lo.hidden=true;camera.position.set(0.01,0,0);controls.update()};
  if(cache[k])return done(cache[k]);
  TL.load('pano/'+k+'.jpg',t=>{t.encoding=THREE.sRGBEncoding;t.anisotropy=renderer.capabilities.getMaxAnisotropy();cache[k]=t;done(t)},undefined,()=>{lo.textContent='This view did not load. Try again.'})}
document.querySelectorAll('[data-pano]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.pano)));
canvas.addEventListener('wheel',e=>{e.preventDefault();camera.fov=Math.max(30,Math.min(95,camera.fov+e.deltaY*0.04));camera.updateProjectionMatrix()},{passive:false});
let pinch=null;const pts=new Map();
canvas.addEventListener('pointerdown',e=>pts.set(e.pointerId,[e.clientX,e.clientY]));
canvas.addEventListener('pointermove',e=>{if(!pts.has(e.pointerId))return;pts.set(e.pointerId,[e.clientX,e.clientY]);
  if(pts.size===2){const [a,b]=[...pts.values()];const d=Math.hypot(a[0]-b[0],a[1]-b[1]);if(pinch){camera.fov=Math.max(30,Math.min(95,camera.fov*pinch/d));camera.updateProjectionMatrix()}pinch=d}});
const up=e=>{pts.delete(e.pointerId);if(pts.size<2)pinch=null};canvas.addEventListener('pointerup',up);canvas.addEventListener('pointercancel',up);
function size(){const w=el.clientWidth,h=el.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
new ResizeObserver(size).observe(el);size();
let visible=false;new IntersectionObserver(es=>{visible=es[0].isIntersecting;if(visible&&!mat.map)show(document.querySelector('[data-pano]').dataset.pano)}).observe(el);
(function loop(){requestAnimationFrame(loop);if(!visible)return;controls.update();renderer.render(scene,camera)})();
})();
"""

FINISH_INFO = {
    "limestone": ["Lueders limestone", "pedra São Tomé", "Sawn-face ashlar in three course heights. One street wall only."],
    "pavers": ["Limestone pavers", "São Tomé paving", "24x36 thermal-finish pavers on the pátio and veranda."],
    "calcada": ["Black stone mosaic", "calçada portuguesa", "50 sf of black basalt setts (or Techo-Bloc Antika Onyx Black) in the shaded entry, framed by light concrete."],
    "ladrilho": ["Patterned cement-look tile", "ladrilho hidráulico", "8x8 terracotta, bone and green, primary bath floor."],
    "zellige": ["Green glazed tile", "azulejo", "2.5x8 handmade-look tile, shower floor to ceiling."],
    "cobogo": ["Concrete cobogó", "the Recife cobogó (1929)", "12x12x4 precast breeze block, white cement, 210 blocks."],
    "cedar_z": ["Western red cedar slats", "freijó / brise-soleil", "2x4 slats at 5\" on center on a steel frame."],
    "cedar_y": ["Cedar T&G ceiling + soffit", "freijó ceilings", "Clear 1x6 tongue and groove, natural oil. Runs inside and out."],
    "cedar_x": ["Teak outdoor furniture", "", "Outdoor dining set."],
    "fence": ["Horizontal cedar fence", "", "6' privacy fence on side and rear lot lines."],
    "stucco": ["Warm-white stucco", "white mineral plaster", "Smooth three-coat stucco over 2x6 framing."],
    "paint": ["Interior walls", "", "Warm-white matte paint on gypsum board."],
    "floor": ["Polished concrete", "cimento queimado", "The slab is the finished floor: light grind, densifier, seal."],
    "concrete": ["Cast concrete", "", "Cobogó curb, driveway ribbons, entry step."],
    "bronze": ["Dark bronze aluminum", "slim steel frames", "15\" fascia, window frames, gate frame and posts."],
    "roof": ["Low-slope TPO roof", "", "1/4\" per foot to scuppers, hidden behind the thin fascia."],
    "glass": ["Glass", "", "9' sliding glass walls, low-E, dark bronze frames."],
    "oak": ["Rift white oak", "tauari interiors", "Kitchen cabinets, credenza, desks."],
    "granite": ["Honed black granite", "Brazilian dark stone", "Island with waterfall ends, counters."],
    "tile": ["Green glazed tile", "azulejo", "4x4 backsplash behind the range and sink."],
    "dark_wood": ["Walnut", "freijó / jacarandá furniture", "Dining and coffee tables."],
    "dg": ["Decomposed granite", "terra batida", "Stabilized DG paths and meadow mulch."],
    "mulch": ["Planting bed", "", "Courtyard garden bed: palmetto, fern, muhly."],
    "lawn_soil": ["Buffalo grass lawn", "", "Low-water native lawn under the oak."],
    "linen": ["Linen upholstery", "linho", "Sofa, bed and outdoor cushions."],
    "leaf": ["Live oak", "tropical canopy", "Heritage live oak, kept and protected."],
    "leaf_dark": ["Live oak", "tropical canopy", "Courtyard and street trees."],
    "bark": ["Live oak", "", "Quercus virginiana."],
    "agave": ["Agave", "bromeliads", "Agave americana and A. ovatifolia in the front meadow."],
    "feather": ["Mexican feather grass", "", "Nassella tenuissima, front meadow drifts."],
    "grass": ["Muhly + sotol", "", "Lindheimer muhly and Texas sotol."],
    "palm": ["Dwarf palmetto", "tropical palms", "Sabal minor: native, cold-hardy, tropical-looking."],
}

PANOS = [("street", "Street"), ("entry", "Covered entry"), ("patio", "Pátio"), ("room", "Great room"),
         ("veranda", "Veranda")]

GALLERY = [
    ("street", "Street", "Limestone wall, cedar pivot gate, cobogó and the sliding cedar carport gate under one long roof edge. Native meadow instead of lawn.", True),
    ("street_dusk", "Dusk", "Lights behind the cobogó and the carport slats turn the front into a lantern; grazers rake the limestone.", True),
    ("entry", "Covered entry", "Black calçada portuguesa underfoot, the cobogó beside you, the cedar pivot door ahead. You arrive here from the carport through a cedar gate.", False),
    ("courtyard", "Pátio", "One L-shaped pátio: palmetto, ferns and muhly under a limbed-up oak, lined by the gallery glass and cedar slat screens.", False),
    ("interior", "Great room", "Cedar ceiling, polished concrete, a walnut-framed linen sofa. Courtyard to the south, veranda to the north.", True),
    ("kitchen", "Kitchen", "Rift white oak, honed black granite island, green glazed tile.", False),
    ("bath", "Primary bath", "Curbless walk-in shower in green zellige-look tile with a skylight in the middle; concrete floor, floating oak vanity, brass.", True),
    ("bath2", "Hall bath", "Terracotta zellige-look tile around the house's one tub, a fixed glass panel, a skylight above, pill mirror, oak and limestone.", True),
    ("gallery", "Gallery", "The bedroom hall is a 30-foot glass wall on the pátio, with rift-oak doors to the bedrooms and hall bath.", False),
    ("veranda", "Veranda", "276 sf under the oak. The cedar ceiling runs straight out from the great room.", False),
    ("rear", "Rear yard", "The house sits forward on the lot to protect the heritage live oak.", False),
    ("aerial", "Aerial", "An L-shaped house wrapped around an open-sky pátio.", True),
]


def glb_to_json(glb, out):
    """GLB -> self-contained glTF JSON (buffer as base64 data URI), servable as .json."""
    import base64
    import struct
    b = open(glb, "rb").read()
    jlen = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + jlen])
    off = 20 + jlen
    blen = struct.unpack("<I", b[off:off + 4])[0]
    binchunk = b[off + 8:off + 8 + blen]
    j["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binchunk).decode()
    with open(out, "w") as f:
        json.dump(j, f, separators=(",", ":"))
    return out


def write_web(img):
    glb = os.path.join(WEB, "casa01.glb")
    if os.path.exists(glb):
        glb_to_json(glb, os.path.join(WEB, "casa01.gltf.json"))
    # realistic v2 model (baked lightmaps) when available
    glb2 = os.path.join(WEB, "casa01_v2.glb")
    lmj = os.path.join(WEB, "lightmaps.json")
    v2 = os.path.exists(glb2) and os.path.exists(lmj)
    if v2:
        glb_to_json(glb2, os.path.join(WEB, "casa01_v2.gltf.json"))
    model = "casa01_v2.gltf.json" if v2 else "casa01.gltf.json"
    lmaps = json.load(open(lmj)) if v2 else None
    # 360° panoramas -> web/pano/*.jpg
    from PIL import Image
    pano_src = os.path.join(os.path.dirname(HERE), "renders", "pano")
    panos = []
    os.makedirs(os.path.join(WEB, "pano"), exist_ok=True)
    for k, label in PANOS:
        src = os.path.join(pano_src, f"pano_{k}.png")
        if os.path.exists(src):
            dst = os.path.join(WEB, "pano", f"{k}.jpg")
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
                Image.open(src).convert("RGB").save(dst, quality=84, optimize=True, progressive=True)
            panos.append((k, label))
    facts = "".join(f'<div><div class="n">{a}</div><div class="l">{b}</div></div>' for a, b in FACTS)
    moves = "".join(f'<div><div class="k">{i + 1}</div><h3>{t}</h3><p>{p}</p></div>' for i, (t, p) in enumerate(MOVES))
    gal = "".join(
        f'<figure class="{"wide" if w else ""}"><img src="{img[k]}" alt="{t}. {c}" loading="lazy" width="1600" height="900">'
        f'<figcaption><b>{t}</b>{c}</figcaption></figure>' for k, t, c, w in GALLERY if k in img)
    sw = "".join(f'<div><img src="{img["sw_" + k]}" alt="{n} sample" loading="lazy"><h4>{n}</h4><div class="br">{br}</div>'
                 f'<div class="sp">{sp}</div></div>' for k, n, br, sp in SWATCHES if "sw_" + k in img)
    rr = "".join(f"<tr><td>{a}</td><td>{b}</td><td class='num'>{c}</td></tr>" for a, b, c in room_rows())
    q = "".join(f"<tr><td>{a}</td><td class='num'>{b}</td><td>{c}</td></tr>" for a, b, c in quantities())
    lo, hi = 325 * A["conditioned"], 425 * A["conditioned"]
    kv = (f"<div>Construction at $325–$425 / sf</div><div>${lo / 1000:,.0f}K–${hi / 1000:,.0f}K</div>"
          f"<div>Site work + utilities</div><div>$20K–$50K</div><div>Design, engineering, permits</div><div>$25K–$50K</div>"
          f"<div>Entry calçada allowance (designer)</div><div>$1K–$4.5K</div>"
          f"<div>Contingency (~10%)</div><div>${lo * 0.1 / 1000:,.0f}K–${hi * 0.1 / 1000:,.0f}K</div>"
          f"<div>Total, excluding land</div><div>${(lo * 1.1 + 46000) / 1000:,.0f}K–${(hi * 1.1 + 104500) / 1000:,.0f}K</div>")

    def dwg(f):
        return f'<div class="paper">{svg_inline(f)}</div>'

    from build import ft, DRAW
    sch = json.load(open(os.path.join(DRAW, "schedules.json")))
    drows = "".join(f"<tr><td><b>{d['tag']}</b></td><td>{d['name']}</td><td>{ft(d['w'])} x {ft(d['h'])}</td><td>{d['type']}</td></tr>"
                    for d in sch["doors"])
    wg = {}
    for w in sch["windows"]:
        g = wg.setdefault(w["tag"], dict(w=w["w"], h=w["h"], kind=w["kind"], n=0))
        g["n"] += 1
    wrows = "".join(f"<tr><td><b>{t}</b></td><td class='num'>{g['n']}</td><td>{ft(g['w'])} x {ft(g['h'])}</td>"
                    f"<td>{'sliding' if g['kind'] == 'slider' else g['kind']}</td></tr>" for t, g in sorted(wg.items()))
    knotes = "".join(f"<li>{k}</li>" for k in sch["keynotes"])
    bf = "".join(f"<tr><td>{a}</td><td><i>{b}</i></td><td>{c}</td></tr>" for a, b, c in D.BATH_FINISHES)
    bath_sec = ('<section class="block"><div class="eyebrow">Primary bath</div><h2>A spa-style wet room</h2>'
                '<p class="lede">7\'-10" square: walk-in shower along the window wall, floating oak vanity, patterned cement-look tile.</p>'
                f'<div class="cols"><div class="paper">{svg_inline("09_bath_plan.svg")}</div>'
                f'<div class="tbl"><table><tr><th>Element</th><th>Brazilian ref.</th><th>Austin spec</th></tr>{bf}</table></div></div></section>'
                ) if img.get("bath") else ""
    land_sec = ""
    if img.get("ortho_site_render"):
        rows = json.load(open(os.path.join(DRAW, "plant_schedule.json")))
        tr = "".join(f"<tr><td><b>{c}</b></td><td>{cm}<br><i style='color:var(--muted)'>{bt}</i></td><td>{sz}</td>"
                     f"<td class='num'>{q if q else 'area'}</td><td>{w}</td></tr>" for c, cm, bt, sz, w, nt, q in rows)
        land_sec = ('<section class="block"><div class="eyebrow">Landscape</div><h2>L-100 Landscape plan</h2>'
                    '<p class="lede">Xeriscape meadow in front, a shady tropical-looking pátio of native palmetto and fern, '
                    'buffalo-grass lawn under the heritage oak. Quantities are counted from the 3D model.</p>'
                    f'<div class="cols"><div class="paper">{svg_inline("21_landscape_plan.svg")}</div>'
                    f'<div class="tbl"><table><tr><th>Key</th><th>Plant</th><th>Size</th><th style="text-align:right">Qty</th>'
                    f'<th>Water</th></tr>{tr}</table></div></div></section>')

    js = (VIEWER_JS.replace("__FINISHES__", json.dumps(FINISH_INFO)).replace("__MODEL__", model)
          .replace("__LIGHTMAPS__", json.dumps(lmaps)).replace("__SKYAZ__", "304.2")
          .replace("__COBOGO__", json.dumps({k: D.COBOGO[k] for k in ("x0", "x1", "y", "t", "z0", "z1")} | {"block": D.BLOCK})))
    pbtn = "".join(f'<button data-pano="{k}" aria-pressed="false">{lab}</button>' for k, lab in panos)
    tour = ('<section class="block" id="tour"><div class="eyebrow">360° tour</div><h2>Stand inside the renders</h2>'
            '<p class="lede">Full photoreal 360° views from the render engine. Drag to look around in every direction; '
            'scroll or pinch to zoom.</p>'
            f'<div class="pano" id="pano"><canvas aria-label="360 degree photoreal view. Drag to look around."></canvas>'
            f'<div class="vbar" role="toolbar" aria-label="360 views">{pbtn}</div>'
            '<div class="loading" id="pload">Loading view</div></div></section>') if panos else ""
    viewer = [
        '<div class="viewer" id="viewer"><canvas aria-label="Interactive 3D model of Casa 01. Drag to orbit, scroll or pinch to zoom."></canvas>',
        '<div class="vbar" role="toolbar" aria-label="Camera views">',
        '<button data-view="street" aria-pressed="true">Street</button><button data-view="entry" aria-pressed="false">Entry</button>'
        '<button data-view="patio" aria-pressed="false">Pátio</button><button data-view="room" aria-pressed="false">Great room</button>'
        '<button data-view="veranda" aria-pressed="false">Veranda</button><button data-view="aerial" aria-pressed="false">Aerial</button>'
        '<button data-view="plan" aria-pressed="false">Plan</button><button id="roofbtn" aria-pressed="false">Lift roof</button></div>',
        '<div class="pick" id="pick" hidden></div>',
        '<div class="vctl"><label for="d">Sun</label><select id="d"><option value="172">June 21</option>'
        '<option value="80">March 21</option><option value="355">Dec 21</option></select>'
        '<input id="t" type="range" min="5.5" max="20.5" step="0.05" value="16.5" aria-label="Time of day, solar time">'
        '<span class="time" id="tl">4:30 pm</span></div>',
        '<div class="loading" id="loading">Loading 3D model</div></div>',
        '<p class="hint">Drag to orbit, scroll or pinch to zoom, right-drag or two-finger drag to pan. Tap any surface to see its finish. '
        'Slide the sun to watch the eaves and the cobogó work through a June or December day. Soft sky light and bounce light are '
        'pre-computed by the photoreal renderer; the sun and its shadows stay live.</p>',
    ]
    parts = [
        '<meta charset="utf-8">',
        '<title>Casa 01 Casa Pátio</title>',
        '<meta name="claude:viewport-fit-sides" content="cover">',
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Lato:wght@400;700;900&display=swap">',
        f'<style>{WEB_CSS}</style>',
        '<div class="wrap">',
        '<header class="top"><div class="eyebrow">Brazilian Modern Homes / Concept design / November 2026</div>',
        '<h1>Casa 01 · Casa Pátio</h1>',
        '<p class="lede">A 1,620 sf, three-bedroom courtyard house for an Austin infill lot. One thin roof, one private garden, '
        'one limestone wall, built with ordinary Texas framing. Every image, plan and number on this page comes from the same 3D model.</p>',
        f'<div class="facts">{facts}</div></header>',
        *viewer,
        tour,
        f'<section class="block"><div class="eyebrow">The idea</div><h2>Three moves make the house</h2><div class="moves">{moves}</div></section>',
        f'<section class="block"><div class="eyebrow">Renders</div><h2>What it looks like</h2><div class="gal">{gal}</div></section>',
        bath_sec,
        land_sec,
        '<section class="block"><div class="eyebrow">Presentation drawings</div><h2>Rendered plan and elevations</h2><div class="dwgs">',
        f'<div><h3>A-100 Floor plan, rendered (cut at 5\'-6")</h3>{dwg("20_plan_rendered.svg")}</div>',
        f'<div class="tbl"><table><tr><th>Room</th><th>Clear size</th><th style="text-align:right">sf</th></tr>{rr}</table></div>',
        f'<div><h3>A-200 South elevation (street)</h3>{dwg("22_elev_s.svg")}</div>',
        f'<div><h3>A-200 North elevation (veranda)</h3>{dwg("22_elev_n.svg")}</div>',
        f'<div class="two"><div><h3>A-201 East elevation</h3>{dwg("22_elev_e.svg")}</div><div><h3>A-201 West elevation</h3>{dwg("22_elev_w.svg")}</div></div>',
        '</div></section>',
        '<section class="block"><div class="eyebrow">Construction drawings</div><h2>Plans, schedules, elevations, section</h2><div class="dwgs">',
        f'<div><h3>A-101 Floor plan</h3>{dwg("30_floor_plan_cd.svg")}</div>',
        f'<div class="two"><div class="tbl"><h3>Door schedule</h3><table><tr><th>No.</th><th>Location</th><th>Size</th><th>Type</th></tr>{drows}</table></div>'
        f'<div class="tbl"><h3>Window schedule</h3><table><tr><th>Mark</th><th style="text-align:right">Qty</th><th>Size</th><th>Type</th></tr>{wrows}</table>'
        f'<h3 style="margin-top:18px">Keynotes</h3><ol style="margin:0;padding-left:20px;font-size:13px;color:var(--muted)">{knotes}</ol></div></div>',
        f'<div class="two"><div><h3>A-102 Roof plan</h3>{dwg("31_roof_plan_cd.svg")}</div><div><h3>A-102 Site plan</h3>{dwg("01_site_plan.svg")}</div></div>',
        f'<div><h3>A-202 South elevation</h3>{dwg("32_elev_s_cd.svg")}</div>',
        f'<div><h3>A-202 North elevation</h3>{dwg("33_elev_n_cd.svg")}</div>',
        f'<div class="two"><div><h3>A-203 East elevation</h3>{dwg("34_elev_e_cd.svg")}</div><div><h3>A-203 West elevation</h3>{dwg("35_elev_w_cd.svg")}</div></div>',
        f'<div><h3>A-300 Section A-A with Austin sun angles</h3>{dwg("07_section_aa.svg")}</div>',
        f'<div><h3>A-500 Cobogó block</h3>{dwg("08_cobogo_detail.svg")}</div></div></section>',
        ('<section class="block"><div class="eyebrow">Finishes</div><h2>Brazilian look, Austin materials</h2>'
         '<p class="lede">Each sample uses the same material as the renders. Gold italics name the Brazilian reference it stands in for.</p>'
         f'<div class="sw">{sw}</div></section>') if sw else '',
        '<section class="block"><div class="eyebrow">For the builder</div><h2>Quantities and planning budget</h2>',
        f'<div class="cols"><div class="tbl"><table><tr><th>Signature element</th><th style="text-align:right">Qty</th><th>Notes</th></tr>{q}</table></div>',
        f'<div><div class="kv">{kv}</div><div class="note"><b>Planning numbers, not bids</b>Ranges carry over from the earlier '
        'feasibility notes. Next step: price these quantities with two Austin builders, then adapt the plan to a real lot.</div></div></div></section>',
        '<footer>Concept study for discussion, not for construction. Zoning, structure, energy code and site conditions need a '
        'licensed local team. Renders are computer visualizations of this design, with scanned CC0 textures from Poly Haven and ambientCG.</footer>',
        '</div>',
        '<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/loaders/GLTFLoader.js"></script>',
        f'<script>{js}</script>',
        f'<script>{PANO_JS}</script>' if panos else '',
    ]
    write_house(facts, viewer, tour, moves, gal, sw, js, panos)
    os.makedirs(os.path.join(WEB, "img", "ortho"), exist_ok=True)
    out = os.path.join(WEB, "index.html")
    with open(out, "w") as f:
        f.write("\n".join(parts))
    for k, rel in img.items():
        shutil.copy(os.path.join(HERE, rel), os.path.join(WEB, rel))
    return out


HOUSE_CSS = """
.site{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:16px 0;border-bottom:1px solid var(--line);margin-bottom:26px}
.site .brand{font-family:var(--serif);font-size:22px;color:var(--fg);text-decoration:none}
.site nav{display:flex;gap:18px;align-items:center}
.site nav a{color:var(--fg);text-decoration:none;font-size:12px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
.site nav a:hover{color:var(--gold)}
.site nav a.pill{border:1px solid var(--fg);padding:9px 13px}
@media (max-width:640px){.site .lg{display:none}.site .brand{font-size:18px}.site nav{gap:14px}}
.cta{background:var(--card);border:1px solid var(--gold);padding:clamp(24px,4vw,44px)}
.ctas{display:flex;flex-wrap:wrap;gap:12px;margin-top:20px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 22px;background:var(--fg);color:var(--bg);
  text-decoration:none;font-size:12px;font-weight:900;letter-spacing:.14em;text-transform:uppercase;border-radius:2px;border:1px solid var(--fg)}
.btn.ghost{background:transparent;color:var(--fg)}
"""


def write_house(facts, viewer, tour, moves, gal, sw, js, panos):
    """Public 'Explore the house' page for the Vercel site (served at /house/)."""
    parts = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
        '<base href="/house/">',
        '<title>Explore Casa Pátio</title>',
        '<meta name="description" content="Walk around Casa Pátio in 3D, slide the Austin sun, and stand inside the renders in 360°.">',
        '<meta property="og:title" content="Explore Casa Pátio · Brazilian Modern Homes"><meta property="og:image" content="img/street.jpg">',
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Lato:wght@400;700;900&display=swap">',
        f'<style>body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}{WEB_CSS}{HOUSE_CSS}</style></head><body>',
        '<div class="wrap">',
        '<header class="site"><a class="brand" href="/">Brazilian Modern Homes</a><nav aria-label="Site">'
        '<a class="lg" href="/">Home</a><a class="lg" href="/Casa01_Lookbook.pdf" target="_blank" rel="noopener">Lookbook PDF</a>'
        '<a class="pill" href="/#join">Join<span class="lg"> the early list</span></a></nav></header>',
        '<header class="top"><div class="eyebrow">Casa 01 · Explore the house</div><h1>Casa Pátio</h1>',
        '<p class="lede">Walk around the house, slide the sun through an Austin day, and stand inside the renders. '
        'Every view comes from the same 3D model as the plans.</p>',
        f'<div class="facts">{facts}</div></header>',
        *viewer,
        tour,
        f'<section class="block"><div class="eyebrow">The idea</div><h2>Three moves make the house</h2><div class="moves">{moves}</div></section>',
        f'<section class="block"><div class="eyebrow">Renders</div><h2>Day to dusk</h2><div class="gal">{gal}</div></section>',
        ('<section class="block"><div class="eyebrow">Finishes</div><h2>Brazilian look, Texas materials</h2>'
         f'<div class="sw">{sw}</div></section>') if sw else '',
        '<section class="block"><div class="cta"><div class="eyebrow">Build it on your lot</div><h2>Want Casa Pátio on your land?</h2>'
        '<p class="lede">Join the early list for a Lot Fit Study: a site plan and renderings of the house on your actual lot, '
        'before you commit.</p><div class="ctas"><a class="btn" href="/#join">Join the early list</a>'
        '<a class="btn ghost" href="/Casa01_Lookbook.pdf" target="_blank" rel="noopener">Download the lookbook (PDF)</a></div></div></section>',
        '<footer>Brazilian Modern Homes · Austin, Texas. Renderings are computer visualizations of the Casa 01 concept design; '
        'prices and specifications may change.</footer>',
        '</div>',
        '<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/build/three.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/controls/OrbitControls.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/three@0.147.0/examples/js/loaders/GLTFLoader.js"></script>',
        f'<script>{js}</script>',
        f'<script>{PANO_JS}</script>' if panos else '',
        '</body></html>',
    ]
    with open(os.path.join(WEB, "house.html"), "w") as f:
        f.write("\n".join(parts))
