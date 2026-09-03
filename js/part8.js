(function(){
  fetch('assets/data/part8_summary.json').then(function(r){return r.json();}).then(function(s){
    var status=document.querySelector('[data-p8-status]'); if(status) status.textContent=s.status||'INPUT_BLOCKED';
    var technical=document.querySelector('[data-p8-technical]'); if(technical) technical.textContent=s.technical_status||'MONITORING_FRAMEWORK_READY';
    var validation=s.validation||{};
    document.querySelectorAll('[data-p8-pass]').forEach(function(x){x.textContent=validation.pass==null?'—':validation.pass;});
    document.querySelectorAll('[data-p8-blocked]').forEach(function(x){x.textContent=validation.blocked==null?'—':validation.blocked;});
    document.querySelectorAll('[data-p8-fail]').forEach(function(x){x.textContent=validation.fail==null?'—':validation.fail;});
  }).catch(function(){});
})();
