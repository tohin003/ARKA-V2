/**
 * ARKA Browser Bridge — Content Script
 * 
 * Injected into every page. Handles DOM manipulation commands
 * from the background service worker.
 */

(() => {
    // Prevent double-injection
    if (window.__ARKA_CONTENT_LOADED) return;
    window.__ARKA_CONTENT_LOADED = true;

    // ─── Message Handler ─────────────────────────────────────────────

    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
        const { action, params = {} } = msg;

        try {
            switch (action) {
                case "click":
                    sendResponse(handleClick(params));
                    break;
                case "type":
                    sendResponse(handleType(params));
                    break;
                case "scroll":
                    sendResponse(handleScroll(params));
                    break;
                case "get_dom":
                    sendResponse(handleGetDom(params));
                    break;
                case "get_text":
                    sendResponse(handleGetText(params));
                    break;
                case "get_elements":
                    sendResponse(handleGetElements(params));
                    break;
                case "highlight":
                    sendResponse(handleHighlight(params));
                    break;
                default:
                    sendResponse({ status: "error", error: `Unknown content action: ${action}` });
            }
        } catch (err) {
            sendResponse({ status: "error", error: err.message });
        }

        return true; // Keep channel open for async
    });

    // ─── Click ───────────────────────────────────────────────────────

    function handleClick(params) {
        const { selector, text, index = 0 } = params;
        let el;

        if (text) {
            // Find by visible text content
            const candidates = findByText(text);
            if (candidates.length === 0) {
                return { status: "error", error: `No element found with text: "${text}"` };
            }
            el = candidates[Math.min(index, candidates.length - 1)];
        } else if (selector) {
            const elements = document.querySelectorAll(selector);
            if (elements.length === 0) {
                return { status: "error", error: `No element matches selector: ${selector}` };
            }
            el = elements[Math.min(index, elements.length - 1)];
        } else {
            return { status: "error", error: "Provide 'selector' or 'text'" };
        }

        // Scroll into view and click
        el.scrollIntoView({ behavior: "smooth", block: "center" });

        setTimeout(() => {
            el.click();
            flashElement(el); // Visual feedback
        }, 300);

        return {
            status: "ok",
            clicked: describeElement(el),
            hasPasswordField: !!document.querySelector('input[type="password"]:not([hidden])')
        };
    }

    // ─── Type ────────────────────────────────────────────────────────

    function handleType(params) {
        const { selector, text, clear = true } = params;
        if (!text) return { status: "error", error: "text is required" };

        let el;
        if (selector) {
            el = document.querySelector(selector);
        } else {
            // Type into focused element
            el = document.activeElement;
        }

        if (!el || !isTypable(el)) {
            return { status: "error", error: `No typable element found for: ${selector || 'active element'}` };
        }

        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.focus();

        if (clear) {
            el.value = "";
            el.dispatchEvent(new Event("input", { bubbles: true }));
        }

        // Simulate realistic typing
        el.value = text;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));

        flashElement(el);

        return {
            status: "ok",
            typed: text,
            into: describeElement(el),
            hasPasswordField: !!document.querySelector('input[type="password"]:not([hidden])')
        };
    }

    // ─── Scroll ──────────────────────────────────────────────────────

    function handleScroll(params) {
        const { direction = "down", amount = 500, selector } = params;
        const target = selector ? document.querySelector(selector) : window;

        const scrollOpts = { behavior: "smooth" };

        switch (direction) {
            case "down":
                target === window
                    ? window.scrollBy({ top: amount, ...scrollOpts })
                    : target.scrollBy({ top: amount, ...scrollOpts });
                break;
            case "up":
                target === window
                    ? window.scrollBy({ top: -amount, ...scrollOpts })
                    : target.scrollBy({ top: -amount, ...scrollOpts });
                break;
            case "left":
                target === window
                    ? window.scrollBy({ left: -amount, ...scrollOpts })
                    : target.scrollBy({ left: -amount, ...scrollOpts });
                break;
            case "right":
                target === window
                    ? window.scrollBy({ left: amount, ...scrollOpts })
                    : target.scrollBy({ left: amount, ...scrollOpts });
                break;
            case "top":
                target === window
                    ? window.scrollTo({ top: 0, ...scrollOpts })
                    : target.scrollTo({ top: 0, ...scrollOpts });
                break;
            case "bottom":
                target === window
                    ? window.scrollTo({ top: document.body.scrollHeight, ...scrollOpts })
                    : target.scrollTo({ top: target.scrollHeight, ...scrollOpts });
                break;
        }

        return {
            status: "ok",
            scrolled: direction,
            amount,
            pageHeight: document.body.scrollHeight,
            scrollY: window.scrollY
        };
    }

    // ─── Get DOM ─────────────────────────────────────────────────────

    function handleGetDom(params) {
        const { selector, max_depth = 3 } = params;
        const root = selector ? document.querySelector(selector) : document.body;

        if (!root) {
            return { status: "error", error: `Element not found: ${selector}` };
        }

        const dom = serializeDOM(root, 0, max_depth);
        return {
            status: "ok",
            dom,
            url: location.href,
            title: document.title
        };
    }

    function serializeDOM(el, depth, maxDepth) {
        if (depth > maxDepth || !el) return null;
        if (el.nodeType === Node.TEXT_NODE) {
            const text = el.textContent.trim();
            return text ? { type: "text", content: text.slice(0, 200) } : null;
        }
        if (el.nodeType !== Node.ELEMENT_NODE) return null;

        const tag = el.tagName.toLowerCase();
        // Skip invisible and script elements
        if (["script", "style", "noscript", "svg", "path"].includes(tag)) return null;

        const node = {
            tag,
            id: el.id || undefined,
            class: el.className ? String(el.className).slice(0, 100) : undefined,
            text: el.innerText ? el.innerText.slice(0, 100) : undefined,
        };

        // Important attributes
        if (el.href) node.href = el.href;
        if (el.src) node.src = el.src;
        if (el.type) node.type = el.type;
        if (el.name) node.name = el.name;
        if (el.placeholder) node.placeholder = el.placeholder;
        if (el.value && tag === "input") node.value = el.value.slice(0, 50);
        if (el.getAttribute("role")) node.role = el.getAttribute("role");
        if (el.getAttribute("aria-label")) node.ariaLabel = el.getAttribute("aria-label");

        // Children
        if (depth < maxDepth && el.children.length > 0) {
            const kids = [];
            for (const child of el.childNodes) {
                const serialized = serializeDOM(child, depth + 1, maxDepth);
                if (serialized) kids.push(serialized);
            }
            if (kids.length > 0) node.children = kids.slice(0, 50); // Cap at 50
        }

        return node;
    }

    // ─── Get Text ────────────────────────────────────────────────────

    function handleGetText(params) {
        const { selector, max_length = 5000 } = params;
        const root = selector ? document.querySelector(selector) : document.body;

        if (!root) {
            return { status: "error", error: `Element not found: ${selector}` };
        }

        const text = root.innerText.slice(0, max_length);
        return {
            status: "ok",
            text,
            length: text.length,
            title: document.title,
            url: location.href
        };
    }

    // ─── Get Elements ────────────────────────────────────────────────

    function handleGetElements(params) {
        const { selector, max_results = 20 } = params;
        if (!selector) return { status: "error", error: "selector required" };

        const elements = document.querySelectorAll(selector);
        const results = [];

        for (let i = 0; i < Math.min(elements.length, max_results); i++) {
            const el = elements[i];
            results.push({
                index: i,
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || "").slice(0, 100),
                ...describeElement(el)
            });
        }

        return {
            status: "ok",
            count: elements.length,
            elements: results
        };
    }

    // ─── Highlight ───────────────────────────────────────────────────

    function handleHighlight(params) {
        const { selector } = params;
        if (!selector) return { status: "error", error: "selector required" };

        const elements = document.querySelectorAll(selector);
        if (elements.length === 0) {
            return { status: "error", error: `No elements match: ${selector}` };
        }

        elements.forEach(el => flashElement(el, "#a78bfa", 2000));

        return { status: "ok", highlighted: elements.length };
    }

    // ─── Utilities ───────────────────────────────────────────────────

    function findByText(searchText) {
        const lower = searchText.toLowerCase();
        const all = document.querySelectorAll("a, button, input, select, [role='button'], [onclick], label, span, div, p, h1, h2, h3, h4, h5, h6, li, td, th");
        const matches = [];

        for (const el of all) {
            const text = (el.innerText || el.value || el.placeholder || el.getAttribute("aria-label") || "").toLowerCase();
            if (text.includes(lower)) {
                matches.push(el);
            }
        }

        // Prioritize interactive elements
        matches.sort((a, b) => {
            const aScore = isInteractive(a) ? 0 : 1;
            const bScore = isInteractive(b) ? 0 : 1;
            return aScore - bScore;
        });

        return matches;
    }

    function isInteractive(el) {
        const tag = el.tagName.toLowerCase();
        return ["a", "button", "input", "select", "textarea"].includes(tag) ||
            el.getAttribute("role") === "button" ||
            el.hasAttribute("onclick");
    }

    function isTypable(el) {
        if (!el) return false;
        const tag = el.tagName.toLowerCase();
        return tag === "input" || tag === "textarea" || el.isContentEditable;
    }

    function describeElement(el) {
        return {
            tag: el.tagName.toLowerCase(),
            id: el.id || undefined,
            class: el.className ? String(el.className).slice(0, 80) : undefined,
            text: (el.innerText || "").slice(0, 60),
            href: el.href || undefined,
            type: el.type || undefined,
            name: el.name || undefined,
        };
    }

    function flashElement(el, color = "#34d399", duration = 800) {
        const orig = el.style.outline;
        const origBg = el.style.backgroundColor;
        el.style.outline = `3px solid ${color}`;
        el.style.backgroundColor = `${color}22`;
        setTimeout(() => {
            el.style.outline = orig;
            el.style.backgroundColor = origBg;
        }, duration);
    }

})();
