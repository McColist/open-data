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
function rr(ctx,x,y,w,h,r,fill){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();ctx.fillStyle=fill;ctx.fill()}
async function slide(sec,fmt){var st=D.studies.filter(function(s){return s.id===sec.id})[0],W=FMT[fmt][0],H=FMT[fmt][1],P=Math.round(W*0.05),wide=W>H;
var cv=document.createElement('canvas');cv.width=W;cv.height=H;var ctx=cv.getContext('2d');ctx.fillStyle=PAL['--bg'];ctx.fillRect(0,0,W,H);ctx.textBaseline='top';
ctx.drawImage(await img(D.logo),P,P,60,60);ctx.fillStyle='#fff';ctx.font='700 28px '+FONT;ctx.fillText('DELTA SCOUT',P+78,P+2);
ctx.fillStyle=PAL['--muted'];ctx.font='600 20px '+FONT;ctx.fillText(('Studi · '+st.kicker).toUpperCase(),P+78,P+38);
var y=P+96;ctx.fillStyle='#fff';ctx.font='700 '+(wide?40:42)+'px '+FONT;y+=wrap(ctx,st.title,P,y,W-2*P,wide?48:52)+10;
ctx.fillStyle=PAL['--ink2'];ctx.font=(wide?24:27)+'px '+FONT;y+=wrap(ctx,st.headline,P,y,W-2*P,wide?32:37)+20;
var sb=await img(D.sb),fh=56,bottom=H-P-fh;
ctx.font='18px '+FONT;var foot=st.foot,footH=wrap(ctx,foot,P,0,W-2*P,24,false);bottom-=footH+14;
ctx.fillStyle=PAL['--muted'];wrap(ctx,foot,P,bottom+8,W-2*P,24);
var items=[];sec.querySelectorAll(':scope > .lg span').forEach(function(sp){var s=sp.querySelector('svg');items.push({s:s,t:sp.textContent.trim()})});
ctx.font='22px '+FONT;var lx=P,rows=items.length?1:0;items.forEach(function(it){var w=34+ctx.measureText(it.t).width+28;if(lx+w>W-P){rows++;lx=P}it.x=lx;it.r=rows-1;lx+=w});
var lh=36,legH=rows*lh;bottom-=legH;ctx.textBaseline='middle';
for(var i=0;i<items.length;i++){var it=items[i],yy=bottom+it.r*lh+lh/2;if(it.s){ctx.drawImage(await svgImg(it.s,22,22),it.x,yy-11,22,22)}ctx.fillStyle=PAL['--ink2'];ctx.fillText(it.t,it.x+32,yy)}
ctx.textBaseline='top';var svgs=[].slice.call(sec.querySelectorAll('.chart svg')),top=y,avail=bottom-top-16,aw=W-2*P;
var cols=svgs.length>2?(wide?3:2):1,rowsN=Math.ceil(svgs.length/cols),cw=(aw-(cols-1)*24)/cols,chh=(avail-(rowsN-1)*20)/rowsN;
if(svgs.length===2&&!svgs[0].closest('.sm')){var a0=svgs[0].viewBox.baseVal,a1=svgs[1].viewBox.baseVal,h0=aw*a0.height/a0.width,h1=aw*a1.height/a1.width,sc=Math.min(1,(avail-20)/(h0+h1));
ctx.drawImage(await svgImg(svgs[0],aw*sc*2,h0*sc*2),P+(aw-aw*sc)/2,top,aw*sc,h0*sc);ctx.drawImage(await svgImg(svgs[1],aw*sc*2,h1*sc*2),P+(aw-aw*sc)/2,top+h0*sc+20,aw*sc,h1*sc)}
else for(var k=0;k<svgs.length;k++){var vb=svgs[k].viewBox.baseVal,ar=vb.width/vb.height,w=cw,h=w/ar;if(h>chh){h=chh;w=h*ar}
var cx=P+(k%cols)*(cw+24)+(cw-w)/2,cy=top+Math.floor(k/cols)*(chh+20)+(chh-h)/2;ctx.drawImage(await svgImg(svgs[k],Math.round(w*2),Math.round(h*2)),cx,cy,w,h)}
var sw=sb.width*0.8;rr(ctx,W-P-sw-20,H-P-fh+10,sw+20,40,8,'#fff');ctx.drawImage(sb,W-P-sw-10,H-P-fh+14,sw,sb.height*0.8);
ctx.fillStyle=PAL['--muted'];ctx.font='20px '+FONT;ctx.textAlign='right';ctx.fillText('Dati:',W-P-sw-32,H-P-fh+20);ctx.textAlign='left';
ctx.fillText('© Delta Scout · riproduzione vietata',P,H-P-fh+20);return cv}
function save(blob,name){var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.appendChild(a);a.click();
setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},2000)}
function lib(src,name){return window[name]?Promise.resolve():new Promise(function(ok,ko){var s=document.createElement('script');s.src=src;s.onload=ok;s.onerror=ko;document.head.appendChild(s)})}
document.querySelectorAll('section.study .exp button').forEach(function(b){b.onclick=async function(){var sec=b.closest('section');b.disabled=true;
try{var cv=await slide(sec,b.dataset.f);cv.toBlob(function(bl){save(bl,'deltascout_studio_'+sec.id+'_'+b.dataset.f.replace(':','x')+'.png')},'image/png')}finally{b.disabled=false}}});
document.querySelectorAll('#exp-all button').forEach(function(b){b.onclick=async function(){var st=document.getElementById('exp-status'),fmt=b.dataset.f;b.disabled=true;try{
await lib('vendor/jszip.min.js','JSZip');await lib('vendor/jspdf.umd.min.js','jspdf');var secs=document.querySelectorAll('section.study'),W=FMT[fmt][0],H=FMT[fmt][1],
zip=new JSZip(),pdf=new jspdf.jsPDF({orientation:W>H?'l':'p',unit:'px',format:[W,H],hotfixes:['px_scaling']});
for(var i=0;i<secs.length;i++){st.textContent='Creo lo studio '+(i+1)+' di '+secs.length+'…';var cv=await slide(secs[i],fmt);if(i)pdf.addPage([W,H],W>H?'l':'p');
pdf.addImage(cv.toDataURL('image/jpeg',0.9),'JPEG',0,0,W,H);zip.file(String(i+1).padStart(2,'0')+'_'+secs[i].id+'.png',cv.toDataURL('image/png').split(',')[1],{base64:true})}
zip.file('deltascout_studi_'+fmt.replace(':','x')+'.pdf',pdf.output('blob'));save(await zip.generateAsync({type:'blob'}),'deltascout_studi_'+fmt.replace(':','x')+'.zip');
st.textContent='Fatto: '+secs.length+' studi esportati.'}catch(e){st.textContent='Errore: '+e}finally{b.disabled=false}}});
})();
