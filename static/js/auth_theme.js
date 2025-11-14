document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    let currentTheme = localStorage.getItem('theme') || 'auto';

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    function setTheme(theme) {
        if (theme === 'auto') {
            body.dataset.theme = mediaQuery.matches ? 'dark' : 'light';
        } else {
            body.dataset.theme = theme;
        }
        currentTheme = theme;
        localStorage.setItem('theme', theme);
    }

    mediaQuery.addEventListener('change', () => {
        if (currentTheme === 'auto') {
            setTheme('auto');
        }
    });

    setTheme(currentTheme);
});