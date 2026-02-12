/**
 * ARKA Browser Bridge — Background Service Worker
 * 
 * Connects to ARKA's WebSocket server (ws://localhost:7777)
 * and routes commands to content scripts or Chrome APIs.
 */

const ARKA_WS_URL = "ws://localhost:7777";
const AUTH_PATTERNS = [
    /login/i, /signin/i, /sign-in/i, /auth/i, /sso/i, /oauth/i,
    /accounts\.google/i, /account\.live/i, /github\.com\/login/i,
    /appleid\.apple/i
];
const AUTH_TITLE_PATTERNS = [
    /sign in/i, /log in/i, /authentication/i, /verify/i
];

let ws = null;
let connected = false;
let reconnectTimer = null;

// ─── WebSocket Connection ────────────────────────────────────────────

function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    try {
        ws = new WebSocket(ARKA_WS_URL);

        ws.onopen = () => {
            connected = true;
            clearReconnectTimer();
            updateBadge("ON", "#34d399");
            console.log("[ARKA] Connected to agent");

            // Send handshake
            ws.send(JSON.stringify({
                type: "handshake",
                agent: "arka-chrome-extension",
                version: "1.0.0"
            }));
        };

        ws.onmessage = async (event) => {
            try {
                const msg = JSON.parse(event.data);
                const result = await handleCommand(msg);
                ws.send(JSON.stringify({ id: msg.id, ...result }));
            } catch (err) {
                ws.send(JSON.stringify({
                    id: null,
                    status: "error",
                    error: err.message
                }));
            }
        };

        ws.onclose = () => {
            connected = false;
            updateBadge("OFF", "#ef4444");
            console.log("[ARKA] Disconnected. Reconnecting in 3s...");
            scheduleReconnect();
        };

        ws.onerror = (err) => {
            console.error("[ARKA] WebSocket error:", err);
            connected = false;
            updateBadge("OFF", "#ef4444");
        };
    } catch (e) {
        console.error("[ARKA] Connection failed:", e);
        scheduleReconnect();
    }
}

function scheduleReconnect() {
    clearReconnectTimer();
    reconnectTimer = setTimeout(connect, 3000);
}

function clearReconnectTimer() {
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
}

function updateBadge(text, color) {
    chrome.action.setBadgeText({ text });
    chrome.action.setBadgeBackgroundColor({ color });
}

// ─── Command Router ──────────────────────────────────────────────────

async function handleCommand(msg) {
    const { action, params = {} } = msg;

    switch (action) {
        case "navigate":
            return await cmdNavigate(params);
        case "click":
            return await cmdInContent("click", params);
        case "type":
            return await cmdInContent("type", params);
        case "scroll":
            return await cmdInContent("scroll", params);
        case "get_dom":
            return await cmdInContent("get_dom", params);
        case "get_text":
            return await cmdInContent("get_text", params);
        case "get_elements":
            return await cmdInContent("get_elements", params);
        case "highlight":
            return await cmdInContent("highlight", params);
        case "screenshot":
            return await cmdScreenshot();
        case "list_tabs":
            return await cmdListTabs();
        case "new_tab":
            return await cmdNewTab(params);
        case "switch_tab":
            return await cmdSwitchTab(params);
        case "close_tab":
            return await cmdCloseTab(params);
        case "get_page_info":
            return await cmdGetPageInfo();
        case "continue_after_auth":
            return { status: "ok", message: "Resumed" };
        default:
            return { status: "error", error: `Unknown action: ${action}` };
    }
}

// ─── Navigation ──────────────────────────────────────────────────────

async function cmdNavigate(params) {
    const { url } = params;
    if (!url) return { status: "error", error: "URL required" };

    const fullUrl = url.startsWith("http") ? url : `https://${url}`;

    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        await chrome.tabs.update(tab.id, { url: fullUrl });

        // Wait for page to load
        await waitForTabLoad(tab.id, 15000);

        const updatedTab = await chrome.tabs.get(tab.id);

        // Check for auth page
        const authCheck = checkAuthPage(updatedTab.url, updatedTab.title);
        if (authCheck) {
            return {
                status: "auth_required",
                message: `Login page detected: ${updatedTab.url}. Please log in manually, then tell ARKA to continue.`,
                url: updatedTab.url
            };
        }

        return {
            status: "ok",
            title: updatedTab.title,
            url: updatedTab.url
        };
    } catch (err) {
        return { status: "error", error: err.message };
    }
}

// ─── Content Script Commands ─────────────────────────────────────────

async function cmdInContent(action, params) {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab) return { status: "error", error: "No active tab" };

        // Ensure content script is injected
        try {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ["content.js"]
            });
        } catch (e) {
            // Content script may already be loaded, that's fine
        }

        const response = await chrome.tabs.sendMessage(tab.id, { action, params });

        // Check response for auth signals
        if (response && response.hasPasswordField) {
            return {
                status: "auth_required",
                message: "Password field detected. Please log in manually.",
                ...response
            };
        }

        return response || { status: "ok" };
    } catch (err) {
        return { status: "error", error: err.message };
    }
}

// ─── Screenshot ──────────────────────────────────────────────────────

async function cmdScreenshot() {
    try {
        const dataUrl = await chrome.tabs.captureVisibleTab(null, {
            format: "png",
            quality: 90
        });
        return {
            status: "ok",
            screenshot: dataUrl,
            format: "png/base64"
        };
    } catch (err) {
        return { status: "error", error: err.message };
    }
}

// ─── Tab Management ──────────────────────────────────────────────────

async function cmdListTabs() {
    const tabs = await chrome.tabs.query({});
    return {
        status: "ok",
        tabs: tabs.map(t => ({
            id: t.id,
            title: t.title,
            url: t.url,
            active: t.active,
            index: t.index
        }))
    };
}

async function cmdNewTab(params) {
    const { url } = params;
    const tab = await chrome.tabs.create({
        url: url ? (url.startsWith("http") ? url : `https://${url}`) : "about:blank"
    });

    if (url) await waitForTabLoad(tab.id, 15000);

    return { status: "ok", tabId: tab.id, title: tab.title || "" };
}

async function cmdSwitchTab(params) {
    const { tab_id } = params;
    if (!tab_id) return { status: "error", error: "tab_id required" };

    await chrome.tabs.update(tab_id, { active: true });
    const tab = await chrome.tabs.get(tab_id);
    return { status: "ok", title: tab.title, url: tab.url };
}

async function cmdCloseTab(params) {
    const { tab_id } = params;
    if (!tab_id) return { status: "error", error: "tab_id required" };

    await chrome.tabs.remove(tab_id);
    return { status: "ok" };
}

async function cmdGetPageInfo() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return { status: "error", error: "No active tab" };

    return {
        status: "ok",
        title: tab.title,
        url: tab.url,
        id: tab.id,
        favIconUrl: tab.favIconUrl
    };
}

// ─── Helpers ─────────────────────────────────────────────────────────

function checkAuthPage(url, title) {
    if (!url) return false;
    for (const p of AUTH_PATTERNS) {
        if (p.test(url)) return true;
    }
    if (title) {
        for (const p of AUTH_TITLE_PATTERNS) {
            if (p.test(title)) return true;
        }
    }
    return false;
}

function waitForTabLoad(tabId, timeout = 15000) {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            chrome.tabs.onUpdated.removeListener(listener);
            resolve(); // Resolve even on timeout — page may be partially loaded
        }, timeout);

        function listener(updatedTabId, changeInfo) {
            if (updatedTabId === tabId && changeInfo.status === "complete") {
                clearTimeout(timer);
                chrome.tabs.onUpdated.removeListener(listener);
                setTimeout(resolve, 500); // Extra 500ms for JS to settle
            }
        }

        chrome.tabs.onUpdated.addListener(listener);
    });
}

// ─── Auto-Connect ────────────────────────────────────────────────────
connect();

// Reconnect when service worker wakes up
chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
