/* ═══════════════════════════════════════════════════════
   YoRobot Landing Page — JavaScript
   Animaciones, scroll, navbar, accordion, counter
   ═══════════════════════════════════════════════════════ */

// ─── Navbar scroll effect ───────────────────────────────
const navbar = document.getElementById("navbar");

window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});

// ─── Mobile nav toggle ─────────────────────────────────
const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");

navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
});

// Close mobile nav on link click
navLinks.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", () => {
        navLinks.classList.remove("open");
    });
});

// ─── Number counter animation ───────────────────────────
function animateCounters() {
    const counters = document.querySelectorAll(".stat-number[data-count]");

    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute("data-count"));
        const duration = 2000;
        const start = performance.now();

        function update(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            counter.textContent = Math.floor(target * eased);

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                counter.textContent = target;
            }
        }

        requestAnimationFrame(update);
    });
}

// ─── Intersection Observer for scroll animations ────────
const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px"
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add("visible");

            // Trigger counter animation when hero stats become visible
            if (entry.target.classList.contains("hero-stats")) {
                animateCounters();
            }
        }
    });
}, observerOptions);

// Observe elements for fade-in
document.addEventListener("DOMContentLoaded", () => {
    // Add fade-in class to elements
    const animateElements = document.querySelectorAll(
        ".feature-card, .detail-feature, .mgmt-card, .tech-card, .cmd-group, .hero-stats"
    );

    animateElements.forEach((el, i) => {
        el.classList.add("fade-in");
        el.style.transitionDelay = `${Math.min(i * 0.08, 0.5)}s`;
        observer.observe(el);
    });

    // Observe hero stats for counter
    const heroStats = document.querySelector(".hero-stats");
    if (heroStats) {
        heroStats.classList.add("fade-in");
        observer.observe(heroStats);
    }
});

// ─── Command accordion toggle ───────────────────────────
function toggleGroup(button) {
    const group = button.closest(".cmd-group");
    const isOpen = group.getAttribute("data-open") === "true";

    // Close all groups
    document.querySelectorAll(".cmd-group").forEach(g => {
        g.setAttribute("data-open", "false");
    });

    // Toggle clicked group
    if (!isOpen) {
        group.setAttribute("data-open", "true");
    }
}

// ─── Active nav link highlighting ───────────────────────
const sections = document.querySelectorAll("section[id]");

window.addEventListener("scroll", () => {
    let current = "";
    const scrollY = window.scrollY + 200;

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;

        if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
            current = section.getAttribute("id");
        }
    });

    document.querySelectorAll(".nav-link").forEach(link => {
        link.classList.remove("active");
        if (link.getAttribute("href") === `#${current}`) {
            link.classList.add("active");
            link.style.color = "#f0f0f5";
        } else {
            link.style.color = "";
        }
    });
});

// ─── Smooth parallax for hero orbs ──────────────────────
let ticking = false;

window.addEventListener("scroll", () => {
    if (!ticking) {
        requestAnimationFrame(() => {
            const scrolled = window.scrollY;
            const orbs = document.querySelectorAll(".hero-orb");

            orbs.forEach((orb, i) => {
                const speed = 0.1 + i * 0.05;
                orb.style.transform = `translateY(${scrolled * speed}px)`;
            });

            ticking = false;
        });
        ticking = true;
    }
});

// ─── Vinyl record play/pause toggle ─────────────────────
const playBtn = document.querySelector(".p-btn-play");
const vinyl = document.querySelector(".vinyl-record");

if (playBtn && vinyl) {
    let isPlaying = true;

    playBtn.addEventListener("click", () => {
        isPlaying = !isPlaying;
        playBtn.textContent = isPlaying ? "▶" : "⏸";
        vinyl.style.animationPlayState = isPlaying ? "running" : "paused";
    });
}
