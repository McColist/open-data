<script>(function(){
var DS=JSON.parse(document.getElementById('ds-export').textContent);
var FMT={'4:5':[1080,1350],'1:1':[1080,1080],'9:16':[1080,1920],'16:9':[1600,900]};
var PAL={'--bg':'#111214','--card':'#1d2125','--ink':'#e8eaed','--mute':'#9aa3ad','--line':'#30363d','--pitch':'#1f2a22','--pl':'#3f5244'};
var FONT='system-ui,-apple-system,"Segoe UI",Roboto,sans-serif';
function vars(s){return s.replace(/var\((--[a-z]+)\)/g,function(m,k){return PAL[k]||'#888'})}
function img(src){return new Promise(function(ok,ko){var i=new Image();i.onload=function(){ok(i)};i.onerror=ko;i.src=src})}
function svgImg(svg,w,h){var c=svg.cloneNode(true);c.setAttribute('xmlns','http://www.w3.org/2000/svg');c.setAttribute('style','font-family:'+FONT);if(w){c.setAttribute('width',w);c.setAttribute('height',h)}
var sym=document.getElementById('dslogo');if(sym&&c.innerHTML.indexOf('#dslogo')>=0){var d=document.createElementNS('http://www.w3.org/2000/svg','defs');d.appendChild(sym.cloneNode(true));c.insertBefore(d,c.firstChild)}
return img('data:image/svg+xml;charset=utf-8,'+encodeURIComponent(vars(new XMLSerializer().serializeToString(c))))}
function wrap(ctx,text,x,y,maxW,lh,draw){var words=String(text).split(' '),line='',n=0;for(var i=0;i<words.length;i++){var t=line?line+' '+words[i]:words[i];
if(ctx.measureText(t).width>maxW&&line){if(draw!==false)ctx.fillText(line,x,y+n*lh);n++;line=words[i]}else line=t}if(line){if(draw!==false)ctx.fillText(line,x,y+n*lh);n++}return n*lh}
function rr(ctx,x,y,w,h,r,fill){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();ctx.fillStyle=fill;ctx.fill()}
function vcol(v){return v>=8?'#1c7ed6':v>=7?'#2f9e44':v>=6.5?'#94b51f':v>=6?'#f08c00':'#e03131'}
async function frame(fmt,title,page,tot){var W=FMT[fmt][0],H=FMT[fmt][1],P=Math.round(W*0.05),cv=document.createElement('canvas');cv.width=W;cv.height=H;
var ctx=cv.getContext('2d');ctx.fillStyle=PAL['--bg'];ctx.fillRect(0,0,W,H);ctx.textBaseline='top';
ctx.drawImage(await img(DS.logo),P,P,64,64);ctx.fillStyle='#fff';ctx.font='700 30px '+FONT;ctx.fillText('DELTA SCOUT',P+82,P+2);
ctx.fillStyle=PAL['--mute'];ctx.font='22px '+FONT;ctx.fillText(DS.title+' · '+DS.sub,P+82,P+40);
if(page){ctx.textAlign='right';ctx.fillText(page+'/'+tot,W-P,P+2);ctx.textAlign='left'}
var y=P+100;if(title){ctx.fillStyle='#7cc4f2';ctx.font='700 36px '+FONT;y+=wrap(ctx,title,P,y,W-2*P,44)}
var sb=await img(DS.sb),fh=60,sw=sb.width*0.85;rr(ctx,W-P-sw-20,H-P-fh+12,sw+20,40,8,'#fff');ctx.drawImage(sb,W-P-sw-10,H-P-fh+15,sw,sb.height*0.85);
ctx.fillStyle=PAL['--mute'];ctx.font='20px '+FONT;ctx.textAlign='right';ctx.fillText('Dati:',W-P-sw-32,H-P-fh+22);ctx.textAlign='left';
ctx.fillText('© Delta Scout · riproduzione vietata',P,H-P-fh+22);return {cv:cv,ctx:ctx,W:W,H:H,P:P,top:y+20,bottom:H-P-fh}}
async function legend(card){var out=[];if(!card)return out;var lgs=card.querySelectorAll('.lg');for(var i=0;i<lgs.length;i++){var sp=lgs[i].querySelectorAll(':scope > span');
for(var j=0;j<sp.length;j++){var s=sp[j].querySelector('svg'),im=null;if(s){try{im=await svgImg(s,44,24)}catch(e){}}out.push({im:im,t:sp[j].textContent.slice(s?s.textContent.length:0).trim()})}}return out}
function cardTitle(el){var card=el.closest('.card'),h2=card&&card.querySelector('h2'),t=h2?h2.textContent.trim():'',n=el;
while(n&&n!==card){var h3=n.querySelector&&n.querySelector(':scope > h3');if(h3){t+=' – '+h3.textContent.trim();break}n=n.parentElement}return t}
async function slideSvg(svg,fmt){var card=svg.closest('.card'),F=await frame(fmt,cardTitle(svg)),ctx=F.ctx,items=await legend(card);
ctx.font='21px '+FONT;var x=F.P,rows=items.length?1:0;items.forEach(function(it){var w=(it.im?52:0)+ctx.measureText(it.t).width+26;if(x+w>F.W-F.P){rows++;x=F.P}it.x=x;it.r=rows-1;x+=w});
var lh=36,legH=rows*lh,vb=svg.viewBox.baseVal,ar=vb.width/vb.height,aw=F.W-2*F.P,ah=F.bottom-F.top-legH-24,w=aw,h=w/ar;if(h>ah){h=ah;w=h*ar}
ctx.drawImage(await svgImg(svg,Math.round(w*2),Math.round(h*2)),(F.W-w)/2,F.top+(ah-h)/2,w,h);
var ly=F.bottom-legH-8;ctx.textBaseline='middle';items.forEach(function(it){var yy=ly+it.r*lh+lh/2,xx=it.x;if(it.im){ctx.drawImage(it.im,xx,yy-12,44,24);xx+=52}
ctx.fillStyle=PAL['--mute'];ctx.fillText(it.t,xx,yy)});return F.cv}
async function slideCover(fmt){var c=DS.cover,F=await frame(fmt,''),ctx=F.ctx,W=F.W,wide=fmt==='16:9',y=F.top+(fmt==='9:16'?160:20),mid=W/2;
ctx.textAlign='center';ctx.fillStyle=PAL['--mute'];ctx.font='600 28px '+FONT;ctx.fillText(c.comp,mid,y);ctx.font='24px '+FONT;ctx.fillText(c.info,mid,y+40);y+=110;
ctx.font='700 '+(wide?44:46)+'px '+FONT;ctx.fillStyle=DS.col[0];ctx.fillText(c.home,W*0.25,y);ctx.fillStyle=DS.col[1];ctx.fillText(c.away,W*0.75,y);
ctx.fillStyle='#fff';ctx.font='800 '+(wide?120:150)+'px '+FONT;ctx.fillText(c.gh+' – '+c.ga,mid,y+60);y+=wide?200:240;
ctx.fillStyle=PAL['--mute'];ctx.font='30px '+FONT;ctx.fillText('xG  '+c.xgh+'  –  '+c.xga,mid,y);y+=80;
if(c.best){rr(ctx,F.P,y,W-2*F.P,96,16,'#1d2125');ctx.textAlign='left';ctx.fillStyle=PAL['--mute'];ctx.font='22px '+FONT;ctx.fillText('Migliore in campo · voto Delta Scout',F.P+28,y+16);
ctx.fillStyle='#fff';ctx.font='700 32px '+FONT;ctx.fillText(c.best[0]+' ('+c.best[1]+')',F.P+28,y+48);rr(ctx,W-F.P-136,y+20,108,56,12,vcol(+c.best[2]));
ctx.fillStyle='#fff';ctx.textAlign='center';ctx.font='800 32px '+FONT;ctx.fillText(c.best[2],W-F.P-82,y+32)}
ctx.textAlign='center';ctx.fillStyle='#7cc4f2';ctx.font='600 26px '+FONT;ctx.fillText('Report completo Delta Scout  →',mid,F.bottom-50);return F.cv}
async function slideText(fmt){var F=await frame(fmt,'Analisi'),ctx=F.ctx,y=F.top,mw=F.W-2*F.P,big=fmt!=='16:9';ctx.fillStyle=PAL['--ink'];
ctx.font=(big?28:24)+'px '+FONT;y+=wrap(ctx,DS.text,F.P,y,mw,big?40:32)+24;ctx.fillStyle='#7cc4f2';ctx.font='700 30px '+FONT;ctx.fillText('Giocatori chiave',F.P,y);y+=48;
ctx.font=(big?25:21)+'px '+FONT;for(var i=0;i<DS.keys.length;i++){var lh=big?34:28,need=wrap(ctx,DS.keys[i],F.P+24,y,mw-24,lh,false);if(y+need>F.bottom-10)break;
ctx.fillStyle='#7cc4f2';ctx.fillText('•',F.P,y);ctx.fillStyle=PAL['--ink'];y+=wrap(ctx,DS.keys[i],F.P+24,y,mw-24,lh)+12}return F.cv}
async function slideStats(fmt){var F=await frame(fmt,'Statistiche di squadra'),ctx=F.ctx,W=F.W,mid=W/2,y=F.top+10,st=DS.stats,step=Math.min(84,(F.bottom-y-60)/st.length),bw=W-2*F.P;
ctx.font='700 28px '+FONT;ctx.textAlign='left';ctx.fillStyle=DS.col[0];ctx.fillText(DS.cover.home,F.P,y);ctx.textAlign='right';ctx.fillStyle=DS.col[1];ctx.fillText(DS.cover.away,W-F.P,y);y+=56;
st.forEach(function(s,i){var ty=y+i*step,vh=Math.abs(+s[1]||0),va=Math.abs(+s[2]||0),ph=vh+va?vh/(vh+va):0.5;ctx.font='700 '+Math.min(28,step*0.4)+'px '+FONT;
ctx.fillStyle='#fff';ctx.textAlign='left';ctx.fillText(s[1],F.P,ty);ctx.textAlign='right';ctx.fillText(s[2],W-F.P,ty);ctx.textAlign='center';ctx.fillStyle=PAL['--mute'];
ctx.font=Math.min(24,step*0.34)+'px '+FONT;ctx.fillText(s[0],mid,ty+2);var by=ty+step*0.46;rr(ctx,F.P,by,bw,8,4,'#30363d');rr(ctx,F.P,by,bw*ph,8,4,DS.col[0]);rr(ctx,F.P+bw*ph,by,bw*(1-ph),8,4,DS.col[1])});return F.cv}
async function slideTop(fmt){var F=await frame(fmt,'Pagelle – voto Delta Scout'),ctx=F.ctx,W=F.W,y=F.top+6,list=DS.top,cols=fmt==='16:9'?2:1,per=Math.ceil(list.length/cols),
step=Math.min(64,(F.bottom-y)/per),cw=(W-2*F.P-(cols-1)*40)/cols;ctx.textBaseline='middle';
list.forEach(function(p,i){var c=Math.floor(i/per),r=i%per,x=F.P+c*(cw+40),yy=y+r*step+step/2;rr(ctx,x,yy-step*0.42,cw,step*0.84,10,'#1d2125');
ctx.fillStyle=DS.col[p[2]];ctx.beginPath();ctx.arc(x+26,yy,9,0,7);ctx.fill();ctx.fillStyle='#fff';ctx.textAlign='left';ctx.font='600 '+Math.min(26,step*0.42)+'px '+FONT;
ctx.fillText(p[0],x+48,yy);ctx.fillStyle=PAL['--mute'];ctx.font=Math.min(20,step*0.32)+'px '+FONT;ctx.textAlign='right';ctx.fillText(p[1],x+cw-104,yy);
rr(ctx,x+cw-88,yy-step*0.3,72,step*0.6,8,vcol(+p[3]));ctx.fillStyle='#fff';ctx.textAlign='center';ctx.font='800 '+Math.min(24,step*0.4)+'px '+FONT;ctx.fillText(p[3],x+cw-52,yy)});return F.cv}
function charts(){var out=[];document.querySelectorAll('main svg[role="img"]').forEach(function(s){if(s.closest('.pl')||s.closest('#individuali')||s.closest('#calore'))return;
if(!s.getClientRects().length)return;out.push(s)});return out}
function lib(src,name){return window[name]?Promise.resolve():new Promise(function(ok,ko){var s=document.createElement('script');s.src=src;s.onload=ok;s.onerror=ko;document.head.appendChild(s)})}
async function exportAll(fmt,btn){var st=document.getElementById('exp-status');try{
await lib('vendor/jszip.min.js','JSZip').catch(function(){return lib('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js','JSZip')});
await lib('vendor/jspdf.umd.min.js','jspdf').catch(function(){return lib('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js','jspdf')});
var makers=[slideCover,slideText,slideStats,slideTop].concat(charts().map(function(s){return function(f){return slideSvg(s,f)}})),cvs=[];
for(var i=0;i<makers.length;i++){st.textContent='Creo la slide '+(i+1)+' di '+makers.length+'…';cvs.push(await makers[i](fmt))}
var W=FMT[fmt][0],H=FMT[fmt][1],pdf=new jspdf.jsPDF({orientation:W>H?'l':'p',unit:'px',format:[W,H],hotfixes:['px_scaling']}),zip=new JSZip();
for(var j=0;j<cvs.length;j++){var data=cvs[j].toDataURL('image/png');if(j)pdf.addPage([W,H],W>H?'l':'p');pdf.addImage(cvs[j].toDataURL('image/jpeg',0.9),'JPEG',0,0,W,H);
zip.file('slide_'+String(j+1).padStart(2,'0')+'.png',data.split(',')[1],{base64:true})}
zip.file('deltascout_'+DS.slug+'_'+fmt.replace(':','x')+'.pdf',pdf.output('blob'));st.textContent='Comprimo…';
var blob=await zip.generateAsync({type:'blob'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='deltascout_'+DS.slug+'_social_'+fmt.replace(':','x')+'.zip';
document.body.appendChild(a);a.click();setTimeout(function(){URL.revokeObjectURL(a.href);a.remove()},2000);st.textContent='Fatto: '+cvs.length+' slide (PNG) + PDF nello zip scaricato.'}
catch(e){st.textContent='Errore: '+e}}
var box=document.getElementById('exp-box');if(box)box.querySelectorAll('button').forEach(function(b){b.onclick=function(){box.querySelectorAll('button').forEach(function(x){x.disabled=true});
exportAll(b.dataset.f).finally(function(){box.querySelectorAll('button').forEach(function(x){x.disabled=false})})}});
})()</script>
