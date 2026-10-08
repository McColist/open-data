(function(){
var D=JSON.parse(document.getElementById('studi-data').textContent);
var FMT={'4:5':[1080,1350],'1:1':[1080,1080],'9:16':[1080,1920],'16:9':[1600,900]};
var PAL={'--bg':'#111214','--surface':'#1a1a19','--card':'#1a1a19','--ink':'#ffffff','--ink2':'#c3c2b7','--muted':'#9c9b93','--line':'#30302d',
'--grid':'#2a2a28','--axis':'#4a4a46','--s1':'#3987e5','--s2':'#d95926','--neg':'#e66767','--neutral':'#5c5c57','--context':'#4b4b47','--mute':'#9c9b93'};
var FONT='system-ui,-apple-system,"Segoe UI",Roboto,sans-serif';
function vars(s){return s.replace(/var\((--[a-z0-9]+)\)/g,function(m,k){return PAL[k]||'#888'})}
function img(src){return new Promise(function(ok,ko){var i=new Image();i.onload=function(){ok(i)};i.onerror=ko;i.src=src})}
function svgImg(svg,w,h){var c=svg.cloneNode(true);c.setAttribute('xmlns','http://www.w3.org/2000/svg');c.setAttribute('width',w);c.setAttribute('height',h);
c.setAttribute('style','font-family:'+FONT);return img('data:image/svg+xml;charset=utf-8,'+encodeURIComponent(vars(new XMLSerializer().serializeToString(c))))}
function wrap(ctx,text,x,y,maxW,lh,draw){var words=String(text).split(' '),line='',n=0;for(var i=0;i<words.length;i++){var t=line?line+' '+words[i]:words[i];
if(ctx.measureText(t).width>maxW&&line){if(draw!==false)ctx.fillText(line,x,y+n*lh);n++;line=words[i]}else line=t}if(line){if(draw!==false)ctx.fillText(line,x,y+n*lh);n++}return n*lh}
// testo che si adatta: riduce il corpo finché il blocco sta nell'altezza disponibile
function fit(ctx,text,x,y,maxW,maxH,size,min,weight,color){var s=size;for(;s>min;s-=2){ctx.font=(weight||400)+' '+s+'px '+FONT;if(wrap(ctx,text,x,y,maxW,s*1.3,false)<=maxH)break}
ctx.font=(weight||400)+' '+s+'px '+FONT;ctx.fillStyle=color||'#fff';return wrap(ctx,text,x,y,maxW,s*1.3)}
function rr(ctx,x,y,w,h,r,fill){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();ctx.fillStyle=fill;ctx.fill()}
function study(id){return D.studies.filter(function(s){return s.id===id})[0]}
// cornice comune: sfondo, logo Delta Scout, numero di slide, attribuzione StatsBomb e copyright
async function frame(st,fmt,page,tot){var W=FMT[fmt][0],H=FMT[fmt][1],P=Math.round(W*0.05);var cv=document.createElement('canvas');cv.width=W;cv.height=H;
var ctx=cv.getContext('2d');ctx.fillStyle=PAL['--bg'];ctx.fillRect(0,0,W,H);ctx.textBaseline='top';
ctx.drawImage(await img(D.logo),P,P,60,60);ctx.fillStyle='#fff';ctx.font='700 28px '+FONT;ctx.fillText('DELTA SCOUT',P+78,P+2);
ctx.fillStyle=PAL['--muted'];ctx.font='600 20px '+FONT;ctx.fillText(('Studio '+st.num+' · '+st.kicker).toUpperCase(),P+78,P+38);
if(page){ctx.textAlign='right';ctx.font='600 22px '+FONT;ctx.fillText(page+'/'+tot,W-P,P+18);ctx.textAlign='left'}
var sb=await img(D.sb),fh=56,sw=sb.width*0.8;rr(ctx,W-P-sw-20,H-P-fh+10,sw+20,40,8,'#fff');ctx.drawImage(sb,W-P-sw-10,H-P-fh+14,sw,sb.height*0.8);
ctx.fillStyle=PAL['--muted'];ctx.font='20px '+FONT;ctx.textAlign='right';ctx.fillText('Dati:',W-P-sw-32,H-P-fh+20);ctx.textAlign='left';
ctx.fillText('© Delta Scout · riproduzione vietata',P,H-P-fh+20);return {cv:cv,ctx:ctx,W:W,H:H,P:P,top:P+110,bottom:H-P-fh-20}}
async function slide(sec,fmt,page,tot){var st=study(sec.id),f=await frame(st,fmt,page,tot),ctx=f.ctx,W=f.W,H=f.H,P=f.P,wide=W>H;
var y=P+96;ctx.fillStyle='#fff';ctx.font='700 '+(wide?40:42)+'px '+FONT;y+=wrap(ctx,st.title,P,y,W-2*P,wide?48:52)+10;
ctx.fillStyle=PAL['--ink2'];ctx.font=(wide?24:27)+'px '+FONT;y+=wrap(ctx,st.headline,P,y,W-2*P,wide?32:37)+20;
var bottom=f.bottom+6;ctx.font='18px '+FONT;var foot=st.foot,footH=wrap(ctx,foot,P,0,W-2*P,24,false);bottom-=footH+14;
ctx.fillStyle=PAL['--muted'];wrap(ctx,foot,P,bottom+8,W-2*P,24);
var items=[];sec.querySelectorAll(':scope > .lg span').forEach(function(sp){var s=sp.querySelector('svg');items.push({s:s,t:sp.textContent.trim()})});
ctx.font='22px '+FONT;var lx=P,rows=items.length?1:0;items.forEach(function(it){var w=34+ctx.measureText(it.t).width+28;if(lx+w>W-P){rows++;lx=P}it.x=lx;it.r=rows-1;lx+=w});
var lh=36,legH=rows*lh;bottom-=legH;ctx.textBaseline='middle';
for(var i=0;i<items.length;i++){var it=items[i],yy=bottom+it.r*lh+lh/2;if(it.s){ctx.drawImage(await svgImg(it.s,22,22),it.x,yy-11,22,22)}ctx.fillStyle=PAL['--ink2'];ctx.fillText(it.t,it.x+32,yy)}
ctx.textBaseline='top';var svgs=[].slice.call(sec.querySelectorAll('.chart svg')),top=y,avail=bottom-top-16,aw=W-2*P;
var sm=sec.querySelector('.chart .sm'),perRow=sm&&sm.classList.contains('sm2')?2:(wide?3:2);
var cols=svgs.length>2?perRow:1,rowsN=Math.ceil(svgs.length/cols),cw=(aw-(cols-1)*24)/cols,chh=(avail-(rowsN-1)*20)/rowsN;
if(svgs.length===2&&!svgs[0].closest('.sm')){var a0=svgs[0].viewBox.baseVal,a1=svgs[1].viewBox.baseVal,h0=aw*a0.height/a0.width,h1=aw*a1.height/a1.width,sc=Math.min(1,(avail-20)/(h0+h1));
ctx.drawImage(await svgImg(svgs[0],aw*sc*2,h0*sc*2),P+(aw-aw*sc)/2,top,aw*sc,h0*sc);ctx.drawImage(await svgImg(svgs[1],aw*sc*2,h1*sc*2),P+(aw-aw*sc)/2,top+h0*sc+20,aw*sc,h1*sc)}
else for(var k=0;k<svgs.length;k++){var vb=svgs[k].viewBox.baseVal,ar=vb.width/vb.height,w=cw,h=w/ar;if(h>chh){h=chh;w=h*ar}
var cx=P+(k%cols)*(cw+24)+(cw-w)/2,cy=top+Math.floor(k/cols)*(chh+20)+(chh-h)/2;ctx.drawImage(await svgImg(svgs[k],Math.round(w*2),Math.round(h*2)),cx,cy,w,h)}
return f.cv}
// slide 1: copertina con l'aggancio
async function cover(st,fmt){var f=await frame(st,fmt,1,5),ctx=f.ctx,W=f.W,P=f.P,aw=W-2*P,wide=W>f.H;
var y=f.top+(wide?10:Math.round((f.bottom-f.top)*0.12));ctx.fillStyle=PAL['--s1'];ctx.fillRect(P,y,90,8);y+=40;
y+=fit(ctx,st.title,P,y,aw,(f.bottom-y)*0.45,wide?66:84,40,750,'#fff')+36;
y+=fit(ctx,st.hook,P,y,aw,f.bottom-y-90,wide?36:44,24,400,PAL['--ink2']);
ctx.font='600 30px '+FONT;ctx.fillStyle=PAL['--s1'];ctx.fillText('Scorri →',P,f.bottom-50);return f.cv}
// slide 3: tre cose da sapere
async function points(st,fmt){var f=await frame(st,fmt,3,5),ctx=f.ctx,W=f.W,P=f.P,aw=W-2*P-80,wide=W>f.H;
var pts=[st.headline].concat(st.body.slice(0,2));if(pts.length<3)pts.push('Attenzione: '+st.caveat);
var y=f.top;ctx.fillStyle='#fff';ctx.font='700 '+(wide?44:52)+'px '+FONT;ctx.fillText('3 cose da sapere',P,y);y+=wide?80:100;
var each=(f.bottom-y-40)/3;
for(var i=0;i<3;i++){var yy=y+i*(each+20);ctx.beginPath();ctx.arc(P+28,yy+28,28,0,2*Math.PI);ctx.fillStyle=PAL['--s1'];ctx.fill();
ctx.fillStyle='#fff';ctx.font='700 30px '+FONT;ctx.textAlign='center';ctx.fillText(String(i+1),P+28,yy+12);ctx.textAlign='left';
fit(ctx,pts[i],P+80,yy+4,aw,each-10,wide?28:34,18,i?400:600,i?PAL['--ink2']:'#fff')}return f.cv}
// slide 4: metodo e limiti
async function method(st,fmt){var f=await frame(st,fmt,4,5),ctx=f.ctx,W=f.W,P=f.P,aw=W-2*P,wide=W>f.H;var y=f.top,half=(f.bottom-f.top-140)/2;
ctx.fillStyle=PAL['--s1'];ctx.font='700 '+(wide?34:40)+'px '+FONT;ctx.fillText('Come è calcolato',P,y);y+=wide?54:64;
y+=fit(ctx,st.method,P,y,aw,half,wide?26:32,16,400,PAL['--ink2'])+40;
ctx.fillStyle=PAL['--s2'];ctx.font='700 '+(wide?34:40)+'px '+FONT;ctx.fillText('Attenzione',P,y);y+=wide?54:64;
fit(ctx,st.caveat,P,y,aw,f.bottom-y,wide?26:32,16,400,PAL['--ink2']);return f.cv}
// slide 5: chiusura
async function cta(st,fmt){var f=await frame(st,fmt,5,5),ctx=f.ctx,W=f.W,H=f.H,P=f.P,aw=W-2*P,wide=W>H;var s=wide?190:260,y=f.top+(wide?0:60);
ctx.drawImage(await img(D.logo),(W-s)/2,y,s,s);y+=s+50;ctx.textAlign='center';ctx.fillStyle='#fff';ctx.font='750 '+(wide?50:60)+'px '+FONT;
ctx.fillText('Segui Delta Scout',W/2,y);y+=wide?74:90;ctx.fillStyle=PAL['--ink2'];ctx.font=(wide?30:36)+'px '+FONT;
ctx.fillText('Uno studio sui dati del calcio ogni settimana',W/2,y);y+=wide?70:110;
if(st.next){ctx.fillStyle=PAL['--muted'];ctx.font='600 '+(wide?24:28)+'px '+FONT;ctx.fillText('LA PROSSIMA SETTIMANA',W/2,y);y+=wide?42:50;
ctx.textAlign='left';ctx.font='600 '+(wide?32:40)+'px '+FONT;var lines=[],words=st.next.split(' '),line='';
words.forEach(function(w){var t=line?line+' '+w:w;if(ctx.measureText(t).width>aw-40&&line){lines.push(line);line=w}else line=t});lines.push(line);
ctx.textAlign='center';ctx.fillStyle='#fff';lines.forEach(function(l,i){ctx.fillText(l,W/2,y+i*(wide?42:52))})}
ctx.textAlign='left';return f.cv}
async function pack(sec,fmt){var st=study(sec.id);return [await cover(st,fmt),await slide(sec,fmt,2,5),await points(st,fmt),await method(st,fmt),await cta(st,fmt)]}
function save(blob,name){var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();
setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},2000)}
function lib(src,name){return window[name]?Promise.resolve():new Promise(function(ok,ko){var s=document.createElement('script');s.src=src;s.onload=ok;s.onerror=ko;document.head.appendChild(s)})}
async function libs(){await lib('vendor/jszip.min.js','JSZip');await lib('vendor/jspdf.umd.min.js','jspdf')}
function newPdf(W,H){return new jspdf.jsPDF({orientation:W>H?'l':'p',unit:'px',format:[W,H],hotfixes:['px_scaling']})}
var NAMES=['01_copertina','02_grafico','03_tre_cose','04_metodo','05_segui'];
document.querySelectorAll('section.study .exp.one button').forEach(function(b){b.onclick=async function(){var sec=b.closest('section');b.disabled=true;
try{var cv=await slide(sec,b.dataset.f);cv.toBlob(function(bl){save(bl,'deltascout_studio_'+sec.id+'_'+b.dataset.f.replace(':','x')+'.png')},'image/png')}finally{b.disabled=false}}});
document.querySelectorAll('section.study .exp.pack button').forEach(function(b){b.onclick=async function(){var sec=b.closest('section'),st=study(sec.id),fmt=b.dataset.f,
out=sec.querySelector('.pst'),W=FMT[fmt][0],H=FMT[fmt][1],tag=fmt.replace(':','x'),base='settimana_'+String(st.week).padStart(2,'0')+'_'+st.id;b.disabled=true;
try{out.textContent='Preparo il pack…';await libs();var cvs=await pack(sec,fmt),zip=new JSZip(),pdf=newPdf(W,H);
cvs.forEach(function(cv,i){if(i)pdf.addPage([W,H],W>H?'l':'p');pdf.addImage(cv.toDataURL('image/jpeg',0.9),'JPEG',0,0,W,H);
zip.file(NAMES[i]+'_'+tag+'.png',cv.toDataURL('image/png').split(',')[1],{base64:true})});
zip.file('carosello_'+tag+'.pdf',pdf.output('blob'));zip.file('testi.txt',st.texts);
save(await zip.generateAsync({type:'blob'}),'deltascout_'+base+'_'+tag+'.zip');out.textContent='Fatto.'}catch(e){out.textContent='Errore: '+e}finally{b.disabled=false}}});
document.querySelectorAll('section.study .copy').forEach(function(b){b.onclick=function(){var t=study(b.closest('section').id).texts;
(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){b.textContent='Copiati ✓'},function(){b.textContent='Seleziona il testo qui sotto'})}});
document.querySelectorAll('#exp-all button').forEach(function(b){b.onclick=async function(){var st=document.getElementById('exp-status'),fmt=b.dataset.f;b.disabled=true;try{
await libs();var secs=document.querySelectorAll('section.study'),W=FMT[fmt][0],H=FMT[fmt][1],zip=new JSZip(),pdf=newPdf(W,H);
for(var i=0;i<secs.length;i++){st.textContent='Creo lo studio '+(i+1)+' di '+secs.length+'…';var cv=await slide(secs[i],fmt);if(i)pdf.addPage([W,H],W>H?'l':'p');
pdf.addImage(cv.toDataURL('image/jpeg',0.9),'JPEG',0,0,W,H);zip.file(String(i+1).padStart(2,'0')+'_'+secs[i].id+'.png',cv.toDataURL('image/png').split(',')[1],{base64:true})}
zip.file('deltascout_studi_'+fmt.replace(':','x')+'.pdf',pdf.output('blob'));save(await zip.generateAsync({type:'blob'}),'deltascout_studi_'+fmt.replace(':','x')+'.zip');
st.textContent='Fatto: '+secs.length+' studi esportati.'}catch(e){st.textContent='Errore: '+e}finally{b.disabled=false}}});
})();
