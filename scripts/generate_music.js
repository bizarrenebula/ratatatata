const fs=require('fs'),path=require('path');
const SR=22050,TAU=Math.PI*2;
function midi(n){return 440*Math.pow(2,(n-69)/12);}
function noise(i,seed){let x=(i+seed*7919)|0;x=(x<<13)^x;return 1-((x*(x*x*15731+789221)+1376312589)&0x7fffffff)/1073741824;}
function wave(type,p,duty=.5){p-=Math.floor(p);if(type==='pulse')return p<duty?1:-1;if(type==='tri')return 1-4*Math.abs(p-.5);return Math.sin(TAU*p);}
function addNote(a,start,dur,note,vol,type='pulse',duty=.5,seed=1){
  let s=Math.floor(start*SR),e=Math.min(a.length,Math.floor((start+dur)*SR)),f=midi(note);
  for(let i=s;i<e;i++){let t=(i-s)/SR,u=t/dur,env=Math.min(1,t/.012)*Math.min(1,(1-u)/.10);
    a[i]+=wave(type,t*f,duty)*vol*env+(type==='pulse'?noise(i,seed)*vol*.018:0);}
}
function kick(a,t,v=.45){let s=t*SR,e=Math.min(a.length,s+.18*SR);for(let i=s;i<e;i++){let q=(i-s)/SR;a[i]+=Math.sin(TAU*(92-260*q)*q)*v*Math.exp(-22*q);}}
function snare(a,t,v=.25,seed=3){let s=t*SR,e=Math.min(a.length,s+.13*SR);for(let i=s;i<e;i++){let q=(i-s)/SR;a[i]+=noise(i,seed)*v*Math.exp(-25*q);}}
function hat(a,t,v=.09,seed=7){let s=t*SR,e=Math.min(a.length,s+.045*SR);for(let i=s;i<e;i++){let q=(i-s)/SR;a[i]+=noise(i,seed)*v*Math.exp(-65*q)*(i%2?1:-1);}}
function drums(a,start,beats,beat,intense=false,seed=1){for(let b=0;b<beats;b++){let t=start+b*beat;kick(a,t,b%4===0?.48:.32);if(b%4===1||b%4===3)snare(a,t,.25,seed+b);hat(a,t,.08,seed+b);hat(a,t+beat/2,intense?.11:.065,seed+b+40);}}
function master(a){let peak=.01;for(let v of a)peak=Math.max(peak,Math.abs(v));let k=.72/peak;for(let i=0;i<a.length;i++)a[i]=Math.tanh(a[i]*k*.94)*.62;}
function wav(a,file){let b=Buffer.alloc(44+a.length*2);b.write('RIFF');b.writeUInt32LE(36+a.length*2,4);b.write('WAVE',8);b.write('fmt ',12);b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*2,28);b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(a.length*2,40);for(let i=0;i<a.length;i++)b.writeInt16LE(Math.max(-32767,Math.min(32767,a[i]*32767)),44+i*2);fs.writeFileSync(file,b);}
function menu(){let bpm=132,beat=60/bpm,beats=32,a=new Float32Array(Math.ceil(beats*beat*SR)),root=50;
  let bass=[0,0,3,0,5,5,3,7],mel=[12,15,19,17,15,12,10,12,12,15,20,19,17,15,12,10];
  drums(a,0,beats,beat,false,11);
  for(let b=0;b<beats;b++){addNote(a,b*beat,beat*.82,root+bass[b%8],.18,'tri');for(let k=0;k<4;k++)addNote(a,b*beat+k*beat/4,beat*.22,root+[0,3,7,10][(b+k)%4]+12,.075,'pulse',.25,2);}
  for(let i=0;i<mel.length*2;i++)addNote(a,i*beat/2,beat*.42,root+mel[i%mel.length],.16,'pulse',.5,5);
  master(a);return a;}
function ambient(){let bpm=80,beat=60/bpm,segBeats=12,segments=10,a=new Float32Array(Math.ceil(segBeats*segments*beat*SR));
  const roots=[34,38,36,33,40,35,39,31,37,32],scales=[[0,3,7,10],[0,2,7,9],[0,3,5,10],[0,3,7,8],[0,2,5,9],[0,3,6,10],[0,4,7,11],[0,1,6,8],[0,3,7,10],[0,1,5,8]];
  for(let s=0;s<segments;s++){let off=s*segBeats*beat,root=roots[s],sc=scales[s];
    for(let b=0;b<segBeats;b+=3){addNote(a,off+b*beat,beat*2.75,root+sc[(b/3)%4],.12,'sine');addNote(a,off+b*beat,beat*2.7,root+12+sc[(b/3+2)%4],.055,'tri');}
    for(let b=1;b<segBeats;b+=2)addNote(a,off+b*beat,beat*.42,root+24+sc[(b+s)%4],.032,'pulse',.25,90+s);
    for(let i=Math.floor(off*SR);i<Math.min(a.length,Math.floor((off+segBeats*beat)*SR));i++)a[i]+=noise(i,120+s)*.009*(.35+.65*Math.sin((i/SR)*Math.PI/3)**2);
  }master(a);return {a,segmentSeconds:segBeats*beat};}
function bossMusic(){let bpm=166,beat=60/bpm,beats=32,a=new Float32Array(Math.ceil(beats*beat*SR)),root=38,sc=[0,3,5,7,10];
  drums(a,0,beats,beat,true,211);
  for(let b=0;b<beats;b++){addNote(a,b*beat,beat*.85,root+sc[(b+(b>>2))%5],.22,'tri');
    for(let k=0;k<4;k++)addNote(a,b*beat+k*beat/4,beat*.19,root+12+sc[(k+b)%5]+(b>23?12:0),.105,'pulse',.25,230+b);}
  let lead=[12,15,17,19,17,15,10,12,12,15,22,19,17,15,12,10];
  for(let i=0;i<32;i++)addNote(a,i*beat,beat*.68,root+lead[i%lead.length],.14,'pulse',.5,270+i);
  master(a);return a;}
const out=path.join(__dirname,'..','assets','audio');fs.mkdirSync(out,{recursive:true});
wav(menu(),path.join(out,'menu-theme.wav'));let amb=ambient();wav(amb.a,path.join(out,'ambient-themes.wav'));wav(bossMusic(),path.join(out,'boss-theme.wav'));
fs.writeFileSync(path.join(out,'music-meta.json'),JSON.stringify({sampleRate:SR,ambientSegmentSeconds:amb.segmentSeconds,
  segments:['sewer-main','old-downtown','tenement','service-sewers','warehouse-stacks','warehouse-floor','corporate-avenue','ventilation','hallways','directors-office'],boss:'retro-arcade'},null,2));
console.log(`Generated menu, 10 ambient themes, and boss theme; ambient segment=${amb.segmentSeconds.toFixed(6)}s`);
