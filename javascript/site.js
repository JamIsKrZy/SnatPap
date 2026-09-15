document.addEventListener('mousemove', (event) => {
    document.documentElement.style.setProperty('--mouse-x', `${event.clientX}px`);
    document.documentElement.style.setProperty('--mouse-y', `${event.clientY}px`);
});

(function () {
    const wrapper = document.querySelector('.glow-wrapper');
    if (!wrapper) return;

    const palettes = [
        ['rgba(112, 0, 255, 0.22)', 'rgba(112, 0, 255, 0.08)', 'rgba(0, 212, 255, 0.03)'],
        ['rgba(0, 212, 255, 0.20)', 'rgba(0, 212, 255, 0.07)', 'rgba(112, 0, 255, 0.03)']
    ];

    function spawnRipple() {
        const glow = document.createElement('div');
        glow.className = 'ripple-glow';

        const x = Math.random() * window.innerWidth;
        const y = Math.random() * window.innerHeight;
        const base = Math.min(window.innerWidth, window.innerHeight);
        const size = base * (0.45 + Math.random() * 0.45);

        const [core, mid, edge] = palettes[Math.floor(Math.random() * palettes.length)];

        glow.style.left = `${x}px`;
        glow.style.top = `${y}px`;
        glow.style.width = `${size}px`;
        glow.style.height = `${size}px`;
        glow.style.background = `radial-gradient(circle, ${core} 0%, ${mid} 45%, ${edge} 65%, transparent 75%)`;

        const duration = 2.2 + Math.random() * 1.6;
        glow.style.animationDuration = `${duration}s`;

        wrapper.appendChild(glow);
        window.setTimeout(() => glow.remove(), duration * 1000 + 100);
    }

    function loop() {
        spawnRipple();
        const nextDelay = 700 + Math.random() * 1400;
        window.setTimeout(loop, nextDelay);
    }

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReducedMotion) {
        loop();
    }
})();

const psgcApi = 'https://psgc.gitlab.io/api';
const provinceSelect = document.getElementById('province');
const citySelect = document.getElementById('city_municipality');
const barangaySelect = document.getElementById('barangay');

if (provinceSelect && citySelect && barangaySelect) {
    function populateSelect(select, items, placeholder, selectedValue) {
        select.replaceChildren(new Option(placeholder, ''));
        items.forEach((item) => {
            const option = new Option(item.name, item.name);
            option.dataset.code = item.code;
            option.selected = item.name === selectedValue;
            select.add(option);
        });
        select.disabled = false;
    }

    async function loadLocationOptions(url, select, placeholder, selectedValue) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Location data request failed');
            populateSelect(select, await response.json(), placeholder, selectedValue);
        } catch (error) {
            select.replaceChildren(new Option('Unable to load options. Please refresh.', ''));
        }
    }

    provinceSelect.addEventListener('change', () => {
        const provinceCode = provinceSelect.options[provinceSelect.selectedIndex]?.dataset.code;
        citySelect.disabled = true;
        barangaySelect.disabled = true;
        if (provinceCode) {
            loadLocationOptions(`${psgcApi}/provinces/${provinceCode}/cities-municipalities.json`, citySelect, 'Select a city or municipality', citySelect.dataset.selected);
        }
    });

    citySelect.addEventListener('change', () => {
        const cityCode = citySelect.options[citySelect.selectedIndex]?.dataset.code;
        barangaySelect.disabled = true;
        if (cityCode) {
            loadLocationOptions(`${psgcApi}/cities-municipalities/${cityCode}/barangays.json`, barangaySelect, 'Select a barangay', barangaySelect.dataset.selected);
        }
    });

    loadLocationOptions(`${psgcApi}/provinces.json`, provinceSelect, 'Select a province', provinceSelect.dataset.selected).then(() => {
        if (provinceSelect.value) provinceSelect.dispatchEvent(new Event('change'));
    });
}

document.querySelectorAll('.password-reveal').forEach((button) => {
    const password = document.getElementById(button.dataset.passwordTarget);
    if (!password) return;

    const showPassword = () => {
        password.type = 'text';
        button.setAttribute('aria-pressed', 'true');
        button.setAttribute('aria-label', 'Release to hide password');
        button.querySelector('i').className = 'bi bi-eye-slash';
    };

    const hidePassword = () => {
        password.type = 'password';
        button.setAttribute('aria-pressed', 'false');
        button.setAttribute('aria-label', 'Hold to show password');
        button.querySelector('i').className = 'bi bi-eye';
    };

    button.addEventListener('pointerdown', showPassword);
    button.addEventListener('pointerup', hidePassword);
    button.addEventListener('pointerleave', hidePassword);
    button.addEventListener('pointercancel', hidePassword);
});
