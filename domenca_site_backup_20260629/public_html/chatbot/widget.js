// HD Web Design Chatbot Widget
(function() {
    const CONFIG = {
        apiUrl: '/chatbot/chat.php',
        position: 'bottom-right',
        primaryColor: '#6366f1',
        secondaryColor: '#8b5cf6',
        botName: 'HD Assistant',
        welcomeMessage: 'Zdravo! 👋 Sem HD Web Design asistent. Kako vam lahko pomagam?',
        placeholder: 'Vpišite vprašanje...',
        errorSporočilo: 'Ups, nekaj je šlo narobe. Poskusite znova ali nam pišite na hercegdarko@hd-webdesign.si',
    };

    let isOpen = false;
    let history = [];
    let isTyping = false;

    // Inject CSS
    const css = document.createElement('style');
    css.textContent = `
        .hd-chatbot * { box-sizing: border-box; margin: 0; padding: 0; }
        
        .hd-chat-toggle {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, ${CONFIG.primaryColor}, ${CONFIG.secondaryColor});
            color: white;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .hd-chat-toggle:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 28px rgba(99, 102, 241, 0.5);
        }
        .hd-chat-toggle .chat-icon { display: none; }
        .hd-chat-toggle.active .chat-icon { display: block; }
        .hd-chat-toggle .close-icon { display: block; }
        .hd-chat-toggle.active .close-icon { display: none; }
        
        .hd-chat-window {
            position: fixed;
            bottom: 96px;
            right: 24px;
            width: 380px;
            max-width: calc(100vw - 48px);
            height: 520px;
            max-height: calc(100vh - 140px);
            background: #0f172a;
            border-radius: 16px;
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            z-index: 9999;
            overflow: hidden;
            opacity: 0;
            transform: translateY(20px) scale(0.95);
            pointer-events: none;
            transition: opacity 0.3s, transform 0.3s;
        }
        .hd-chat-window.open {
            opacity: 1;
            transform: translateY(0) scale(1);
            pointer-events: all;
        }
        
        .hd-chat-header {
            background: linear-gradient(135deg, ${CONFIG.primaryColor}, ${CONFIG.secondaryColor});
            color: white;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .hd-chat-header-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        .hd-chat-header-info h3 { font-size: 15px; font-weight: 600; }
        .hd-chat-header-info span { font-size: 12px; opacity: 0.85; }
        
        .hd-chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .hd-chat-messages::-webkit-scrollbar { width: 4px; }
        .hd-chat-messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        
        .hd-msg {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
            word-wrap: break-word;
            animation: hdFadeIn 0.2s ease;
        }
        @keyframes hdFadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        
        .hd-msg.user {
            align-self: flex-end;
            background: linear-gradient(135deg, ${CONFIG.primaryColor}, ${CONFIG.secondaryColor});
            color: white;
            border-bottom-right-radius: 4px;
        }
        .hd-msg.bot {
            align-self: flex-start;
            background: #1e293b;
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        
        .hd-typing {
            align-self: flex-start;
            background: #1e293b;
            padding: 10px 14px;
            border-radius: 12px;
            display: none;
        }
        .hd-typing.show { display: flex; gap: 4px; }
        .hd-typing span {
            width: 6px;
            height: 6px;
            background: #64748b;
            border-radius: 50%;
            animation: hdBounce 1.4s infinite;
        }
        .hd-typing span:nth-child(2) { animation-delay: 0.2s; }
        .hd-typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes hdBounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
        
        .hd-chat-input {
            padding: 12px 16px;
            border-top: 1px solid #1e293b;
            display: flex;
            gap: 8px;
            background: #0f172a;
        }
        .hd-chat-input input {
            flex: 1;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 10px 14px;
            color: #e2e8f0;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        .hd-chat-input input:focus { border-color: ${CONFIG.primaryColor}; }
        .hd-chat-input input::placeholder { color: #64748b; }
        .hd-chat-input button {
            width: 42px;
            height: 42px;
            border-radius: 10px;
            background: linear-gradient(135deg, ${CONFIG.primaryColor}, ${CONFIG.secondaryColor});
            color: white;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: transform 0.2s;
            flex-shrink: 0;
        }
        .hd-chat-input button:hover { transform: scale(1.05); }
        .hd-chat-input button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
        .hd-chat-footer {
            text-align: center;
            padding: 6px;
            font-size: 10px;
            color: #475569;
            background: #0f172a;
        }
        
        @media (max-width: 480px) {
            .hd-chat-window {
                bottom: 0;
                right: 0;
                width: 100%;
                height: 100%;
                max-height: 100%;
                border-radius: 0;
            }
            .hd-chat-toggle { bottom: 16px; right: 16px; }
        }
    `;
    document.head.appendChild(css);

    // Build HTML
    const container = document.createElement('div');
    container.className = 'hd-chatbot';
    container.innerHTML = `
        <button class="hd-chat-toggle" id="hdChatToggle" aria-label="Odpri klepet">
            <span class="chat-icon">💬</span>
            <span class="close-icon">✕</span>
        </button>
        <div class="hd-chat-window" id="hdChatWindow">
            <div class="hd-chat-header">
                <div class="hd-chat-header-avatar">🤖</div>
                <div class="hd-chat-header-info">
                    <h3>${CONFIG.botName}</h3>
                    <span>HD Web Design</span>
                </div>
            </div>
            <div class="hd-chat-messages" id="hdChatMessages">
                <div class="hd-msg bot">${CONFIG.welcomeMessage}</div>
                <div class="hd-typing" id="hdTyping">
                    <span></span><span></span><span></span>
                </div>
            </div>
            <div class="hd-chat-input">
                <input type="text" id="hdChatInput" placeholder="${CONFIG.placeholder}" autocomplete="off">
                <button id="hdChatSend" aria-label="Pošlji">➤</button>
            </div>
            <div class="hd-chat-footer">Powered by DeepSeek AI</div>
        </div>
    `;
    document.body.appendChild(container);

    // Elements
    const toggle = document.getElementById('hdChatToggle');
    const window_ = document.getElementById('hdChatWindow');
    const messages = document.getElementById('hdChatMessages');
    const input = document.getElementById('hdChatInput');
    const sendBtn = document.getElementById('hdChatSend');
    const typing = document.getElementById('hdTyping');

    // Toggle chat
    toggle.addEventListener('click', () => {
        isOpen = !isOpen;
        toggle.classList.toggle('active', isOpen);
        window_.classList.toggle('open', isOpen);
        if (isOpen) input.focus();
    });

    // Send message
    async function sendMessage() {
        const text = input.value.trim();
        if (!text || isTyping) return;

        // Add user message
        addMessage(text, 'user');
        input.value = '';
        sendBtn.disabled = true;
        isTyping = true;
        typing.classList.add('show');
        messages.scrollTop = messages.scrollHeight;

        try {
            const res = await fetch(CONFIG.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, history })
            });

            const data = await res.json();
            
            if (data.error) {
                addMessage(CONFIG.errorSporočilo, 'bot');
            } else {
                addMessage(data.reply, 'bot');
                history.push({ role: 'user', content: text });
                history.push({ role: 'assistant', content: data.reply });
                // Keep history manageable
                if (history.length > 20) history = history.slice(-20);
            }
        } catch (err) {
            addMessage(CONFIG.errorSporočilo, 'bot');
        }

        isTyping = false;
        typing.classList.remove('show');
        sendBtn.disabled = false;
        input.focus();
    }

    function addMessage(text, role) {
        const div = document.createElement('div');
        div.className = `hd-msg ${role}`;
        div.textContent = text;
        messages.insertBefore(div, typing);
        messages.scrollTop = messages.scrollHeight;
    }

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
})();
