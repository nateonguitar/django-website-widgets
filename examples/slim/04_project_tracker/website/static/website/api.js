// How every page's script calls the JSON endpoints, so each one stays a few lines. Script every
// page needs, so it's a static file the document template loads once; each widget's own
// behaviour stays an inline <script> in its template.
//
// A static file can't read template values, so the document template puts them in <meta> tags.
window.exampleApi = {
    csrfToken: document.querySelector('meta[name="csrf-token"]').content,
    flashCookieName: document.querySelector('meta[name="flash-cookie-name"]').content,

    async send(method, url, body) {
        let response;
        try {
            response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: body === undefined ? undefined : JSON.stringify(body),
            });
        } catch {
            return { ok: false, status: 0, data: null, error: 'Something went wrong. Check your connection and try again.', errors: {} };
        }
        const data = response.status === 204 ? null : await response.json().catch(() => null);
        if (response.ok) {
            return { ok: true, status: response.status, data, error: null, errors: {} };
        }
        const errors = data?.errors ?? {};
        return {
            ok: false,
            status: response.status,
            data,
            error: data?.error ?? (Object.keys(errors).length ? null : 'Something went wrong.'),
            errors,
        };
    },

    // Puts each field's messages beside its input, and anything else in the form's message.
    showErrors(result, fieldElements, formElement) {
        const unplaced = result.error ? [result.error] : [];
        for (const [field, messages] of Object.entries(result.errors)) {
            if (fieldElements[field]) {
                fieldElements[field].textContent = messages.join(' ');
            } else {
                unplaced.push(...messages);
            }
        }
        formElement.textContent = unplaced.join(' ');
    },

    navigateWithMessage(url, message) {
        document.cookie = `${this.flashCookieName}=${encodeURIComponent(message)}; path=/; SameSite=Lax`;
        window.location.assign(url);
    },

    // The message the last page left describes what happened before this page loaded, so it goes
    // once the page does something of its own.
    clearFlash() {
        document.getElementById('example-flash')?.remove();
    },
};
