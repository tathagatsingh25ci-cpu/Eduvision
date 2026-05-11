(() => {
    const canvas = document.getElementById("particleCanvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const particles = [];
    const density = 72;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        particles.length = 0;
        const count = Math.min(density, Math.floor((canvas.width * canvas.height) / 18000));
        for (let index = 0; index < count; index += 1) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.35,
                vy: (Math.random() - 0.5) * 0.35,
                radius: Math.random() * 1.8 + 0.7,
            });
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "rgba(34, 211, 238, 0.62)";
        ctx.strokeStyle = "rgba(34, 211, 238, 0.12)";

        particles.forEach((particle, index) => {
            particle.x += particle.vx;
            particle.y += particle.vy;

            if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;

            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            ctx.fill();

            for (let next = index + 1; next < particles.length; next += 1) {
                const other = particles[next];
                const dx = particle.x - other.x;
                const dy = particle.y - other.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < 120) {
                    ctx.globalAlpha = 1 - distance / 120;
                    ctx.beginPath();
                    ctx.moveTo(particle.x, particle.y);
                    ctx.lineTo(other.x, other.y);
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                }
            }
        });

        requestAnimationFrame(animate);
    }

    window.showToast = (message) => {
        const stack = document.getElementById("toastStack");
        if (!stack) return;
        const toast = document.createElement("div");
        toast.className = "toast";
        toast.textContent = message;
        stack.appendChild(toast);
        setTimeout(() => toast.remove(), 3400);
    };

    function createPopBurst(event) {
        if (prefersReducedMotion || !event.clientX || !event.clientY) return;
        const labels = ["AI", "%", "ML", "+", "OK"];
        const count = 3;
        for (let index = 0; index < count; index += 1) {
            const pop = document.createElement("span");
            const angle = Math.random() * Math.PI * 2;
            const distance = 34 + Math.random() * 28;
            pop.className = "pop-icon";
            pop.textContent = labels[Math.floor(Math.random() * labels.length)];
            pop.style.left = `${event.clientX}px`;
            pop.style.top = `${event.clientY}px`;
            pop.style.setProperty("--dx", `${Math.cos(angle) * distance}px`);
            pop.style.setProperty("--dy", `${Math.sin(angle) * distance - 14}px`);
            document.body.appendChild(pop);
            setTimeout(() => pop.remove(), 820);
        }
    }

    document.addEventListener("pointerdown", (event) => {
        if (event.target.closest(".btn, .social-btn, .role-tab, .feature-card, .metric-card, .chart-card, .sidebar-link")) {
            createPopBurst(event);
        }
    });

    document.querySelectorAll("[data-contact-form]").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const status = form.querySelector(".message");
            const payload = Object.fromEntries(new FormData(form).entries());
            try {
                const response = await fetch("/api/contact", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (!response.ok) throw new Error(data.message || "Contact request failed");
                status.textContent = data.message;
                status.className = "message success";
                form.reset();
                window.showToast("Contact request recorded");
            } catch (error) {
                status.textContent = error.message;
                status.className = "message error";
            }
        });
    });

    const counters = document.querySelectorAll("[data-counter]");
    if (counters.length) {
        const revealCounter = (node) => {
            const target = Number(node.dataset.counter || 0);
            const start = performance.now();
            const duration = 900;
            const decimals = String(node.dataset.counter || "").includes(".") ? 1 : 0;

            function tick(now) {
                const progress = Math.min(1, (now - start) / duration);
                const value = target * (1 - Math.pow(1 - progress, 3));
                node.textContent = decimals ? value.toFixed(decimals) : Math.round(value);
                if (progress < 1) requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting && !entry.target.dataset.counted) {
                    entry.target.dataset.counted = "true";
                    revealCounter(entry.target);
                }
            });
        }, { threshold: 0.45 });
        counters.forEach((counter) => observer.observe(counter));
    }

    document.querySelectorAll(".social-btn").forEach((button) => {
        button.addEventListener("click", () => window.showToast("Social login UI placeholder"));
    });

    window.addEventListener("resize", resize);
    resize();
    if (!prefersReducedMotion) animate();
})();
