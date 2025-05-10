// Add copy buttons to all code blocks on page load (for static code, e.g. docs)
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('pre > code').forEach((codeBlock) => {
        const pre = codeBlock.parentElement;
        if (pre.querySelector('.copy-btn')) return;
        pre.style.position = 'relative';
        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.type = 'button';
        btn.innerText = 'Copy';
        btn.setAttribute('aria-label', 'Copy code');
        btn.onclick = function() {
            navigator.clipboard.writeText(codeBlock.innerText);
            btn.innerText = 'Copied!';
            setTimeout(() => { btn.innerText = 'Copy'; }, 1200);
        };
        pre.appendChild(btn);
    });
});
