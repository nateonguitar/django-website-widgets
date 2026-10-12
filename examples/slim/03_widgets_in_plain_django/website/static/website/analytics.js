// A stand-in for an analytics snippet such as Google Analytics: script every page needs, so it's
// a static file the document template loads once, unlike a widget's own inline <script>.
window.exampleAnalytics = {
    events: [],

    track(name, details = {}) {
        const event = { name, path: window.location.pathname, ...details };
        this.events.push(event);
        console.info('[analytics]', event);
    },
};

window.exampleAnalytics.track('page_view', { title: document.title });
