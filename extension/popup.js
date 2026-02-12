/**
 * ARKA Browser Bridge — Popup Script
 */

document.addEventListener("DOMContentLoaded", async () => {
    const dot = document.getElementById("statusDot");
    const text = document.getElementById("statusText");
    const tabEl = document.getElementById("activeTab");
    const lastCmd = document.getElementById("lastCmd");

    // Check connection by trying to reach the background script's state
    try {
        // Check badge text for connection status
        const badge = await chrome.action.getBadgeText({});

        if (badge === "ON") {
            dot.className = "dot connected";
            text.className = "status-text connected";
            text.textContent = "Connected";
        } else {
            dot.className = "dot disconnected";
            text.className = "status-text disconnected";
            text.textContent = "Disconnected";
        }
    } catch (e) {
        dot.className = "dot disconnected";
        text.className = "status-text disconnected";
        text.textContent = "Error";
    }

    // Show active tab info
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.title) {
            tabEl.textContent = tab.title.slice(0, 25) + (tab.title.length > 25 ? "…" : "");
        }
    } catch (e) {
        tabEl.textContent = "—";
    }

    // Show last command from storage
    try {
        const data = await chrome.storage.local.get("lastCommand");
        if (data.lastCommand) {
            lastCmd.textContent = data.lastCommand;
        }
    } catch (e) {
        // ignore
    }
});
