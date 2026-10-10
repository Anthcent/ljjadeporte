/* JavaScript ligero sin dependencias. */
(() => {
  const $=(q,root=document)=>root.querySelector(q);
  const $$=(q,root=document)=>Array.from(root.querySelectorAll(q));
  const menu=$('#toggleSidebar');
  if(menu)menu.addEventListener('click',()=>$('#sidebar')?.classList.toggle('open'));
  document.addEventListener('keydown',(ev)=>{
    if(ev.key==='Escape')$('#sidebar')?.classList.remove('open');
  });
  const print=$('#printQr');
  if(print)print.addEventListener('click',()=>window.print());
  $$('form[data-confirm]').forEach(f=>f.addEventListener('submit',ev=>{
    if(!window.confirm(f.dataset.confirm || '¿Continuar?'))ev.preventDefault();
  }));
  $$('form.stack-form').forEach(form=>form.addEventListener('submit',()=>{
    const submit=$('button[type="submit"], button:not([type])',form);
    if(submit && form.checkValidity()){
      submit.disabled=true;
      submit.setAttribute('aria-busy','true');
      // Submit native form explicitly after disabling.
      setTimeout(()=>form.submit(),0);
    }
  }));
  const fmt=(n,decimals=2)=>Number.isFinite(n)?n.toLocaleString('es-VE',{maximumFractionDigits:decimals,minimumFractionDigits:decimals}):'—';
  $$('[data-calculator]').forEach(card=>{
    const number=(key)=>{
      const el=card.querySelector(`[data-in="${key}"]`);
      return el && el.value!=='' ? Number(el.value):NaN;
    };
    const result=$('[data-out]',card);
    function update(){
      let val='—';let extra='';
      const type=card.dataset.calculator;
      if(type==='imc'){
        const w=number('weight'),h=number('height');
        if(w>0&&h>0)val=fmt(w/(h/100)**2);
      }else if(type==='rcc'){
        const w=number('waist'),h=number('hip');
        if(w>0&&h>0)val=fmt(w/h,3);
      }else if(type==='heart'){
        const p=number('pulse'),s=number('seconds');
        if(p>=0&&s>0)val=`${fmt(p*60/s,0)} lpm`;
      }else if(type==='pace'){
        const d=number('distance'),s=number('duration');
        if(d>0&&s>0){
          const pace=s/(d/1000),m=Math.floor(pace/60),sec=Math.round(pace%60);
          val=`${m+Math.floor(sec/60)}:${String(sec%60).padStart(2,'0')} min/km`;
          extra=`Velocidad media: ${fmt((d/1000)/(s/3600))} km/h`;
        }
      }
      result.textContent=val;
      const extraEl=$('[data-extra]',card);
      if(extraEl)extraEl.textContent=extra||'Velocidad media — km/h';
    }
    $$('input,select',card).forEach(x=>x.addEventListener('input',update));
    update();
  });
  const measurement=$('#measurementForm');
  if(measurement){
    function recalc(){
      const w=Number(measurement.elements.weight_kg.value);
      const h=Number(measurement.elements.height_cm.value);
      const box=$('#liveMeasure');
      if(w>0&&h>0){
        box.textContent=`IMC descriptivo: ${fmt(w/(h/100)**2)} · Cálculo automático. No es un diagnóstico ni una clasificación de salud.`;
        box.classList.add('active');
      }else{
        box.textContent='Introduce peso y estatura para ver el cálculo del IMC.';
        box.classList.remove('active');
      }
    }
    ['weight_kg','height_cm'].forEach(n=>measurement.elements[n].addEventListener('input',recalc));
  }
})();

/* Herramientas de cronometraje: usan performance.now para una medición de intervalo
   estable, independientemente de cambios del reloj de la computadora. */
(() => {
  const $=id=>document.getElementById(id);
  if(!$('watchDisplay'))return;
  let running=false, elapsed=0, started=0, laps=[];
  const readable=ms=>{
    const cent=Math.floor(ms/10)%100;
    const secs=Math.floor(ms/1000)%60;
    const mins=Math.floor(ms/60000);
    return `${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}.${String(cent).padStart(2,'0')}`;
  };
  const current=()=>running?elapsed+(performance.now()-started):elapsed;
  $('watchStart').addEventListener('click',()=>{
    if(running){elapsed=current();running=false;$('watchStart').textContent='Reanudar';}
    else{started=performance.now();running=true;$('watchStart').textContent='Pausar';}
  });
  $('watchReset').addEventListener('click',()=>{
    running=false;elapsed=0;laps=[];$('watchDisplay').textContent='00:00.00';
    $('watchStart').textContent='Iniciar';$('watchLaps').innerHTML='<li class="muted-small">Todavía no hay vueltas registradas.</li>';
  });
  $('watchLap').addEventListener('click',()=>{
    if(!running)return;
    laps.push(current());
    const el=$('watchLaps');el.replaceChildren();
    laps.forEach((time,i)=>{
      const li=document.createElement('li');li.textContent=`Vuelta ${i+1}: ${readable(time)}`;el.appendChild(li);
    });
  });
  let countRunning=false,countRemaining=60000,countStart=0;
  const fmtCount=ms=>{
    const s=Math.max(0,Math.ceil(ms/1000));
    return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
  };
  const countCurrent=()=>countRunning?Math.max(0,countRemaining-(performance.now()-countStart)):countRemaining;
  $('countdownSeconds').addEventListener('change',()=>{
    if(!countRunning){countRemaining=Math.max(1,Math.min(3600,Number($('countdownSeconds').value)||60))*1000;$('countdownDisplay').textContent=fmtCount(countRemaining);}
  });
  $('countdownStart').addEventListener('click',()=>{
    if(countRunning){countRemaining=countCurrent();countRunning=false;$('countdownStart').textContent='Reanudar';}
    else{
      if(countRemaining===0)countRemaining=Math.max(1,Number($('countdownSeconds').value)||60)*1000;
      countStart=performance.now();countRunning=true;$('countdownStart').textContent='Pausar';
    }
  });
  $('countdownReset').addEventListener('click',()=>{
    countRunning=false;countRemaining=Math.max(1,Math.min(3600,Number($('countdownSeconds').value)||60))*1000;
    $('countdownDisplay').textContent=fmtCount(countRemaining);$('countdownStart').textContent='Iniciar / Pausar';
  });
  function tick(){
    if(running)$('watchDisplay').textContent=readable(current());
    if(countRunning){
      let remaining=countCurrent();$('countdownDisplay').textContent=fmtCount(remaining);
      if(remaining===0){countRunning=false;countRemaining=0;$('countdownStart').textContent='Iniciar / Pausar';}
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();
