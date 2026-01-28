// 4. Initialization
function bootstrap() {
    const urlParams = new URLSearchParams(window.location.search);
    const lang = urlParams.get('lang') || 'uz';
    const p64 = urlParams.get('p');
    if (p64) { try { window.PROMO_CODES = JSON.parse(atob(p64.replace(/-/g, '+').replace(/_/g, '/'))); } catch (e) { } }

    finalMenu = (window.DYNAMIC_MENU_DATA && Object.keys(window.DYNAMIC_MENU_DATA).length > 0)
        ? window.DYNAMIC_MENU_DATA
        : DEFAULT_MENU;

    activeCat = Object.keys(finalMenu)[0] || "";
    setLanguage(lang);
    renderCats();
    renderProducts();
    updateCartUI();
}

bootstrap();

// Auto Scroll Update
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('.category-block');
    let current = '';
    sections.forEach(s => {
        if (window.pageYOffset >= s.offsetTop - 200) {
            const header = s.querySelector('.cat-name');
            if (header) current = header.innerText;
        }
    });
    if (current && activeCat !== current) { activeCat = current; renderCats(); }
});
