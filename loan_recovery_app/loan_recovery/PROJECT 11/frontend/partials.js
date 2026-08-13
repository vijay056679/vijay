(function () {
    async function loadPartials() {
        const includeNodes = Array.from(document.querySelectorAll('[data-include]'));

        for (const node of includeNodes) {
            const url = node.getAttribute('data-include');
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`Failed to load partial: ${url}`);
            }

            const template = document.createElement('template');
            template.innerHTML = await response.text();
            node.replaceWith(template.content.cloneNode(true));
        }
    }

    window.partialsReady = loadPartials();
})();
