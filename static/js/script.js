/**
 * Museum Artifact Explorer - Client Scripts
 * Handles mobile navigation toggle, flash message auto-dismiss, and interactive UI enhancements.
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Mobile navigation toggle
    const hamburger = document.getElementById("hamburger");
    const navLinks = document.getElementById("nav-links");

    if (hamburger && navLinks) {
        hamburger.addEventListener("click", () => {
            navLinks.classList.toggle("open");
            const isOpen = navLinks.classList.contains("open");
            hamburger.setAttribute("aria-expanded", isOpen);
        });
    }

    // 2. Auto-dismiss flash notifications after 5 seconds
    const flashMessages = document.querySelectorAll(".flash");
    flashMessages.forEach((msg) => {
        setTimeout(() => {
            msg.style.transition = "opacity 0.4s ease, transform 0.4s ease";
            msg.style.opacity = "0";
            msg.style.transform = "translateX(20px)";
            setTimeout(() => msg.remove(), 400);
        }, 5000);
    });

    // 3. Fallback handlers for images without inline onerror
    const images = document.querySelectorAll("img");
    images.forEach((img) => {
        img.addEventListener("error", function () {
            if (this.classList.contains("card-img") || this.classList.contains("featured-img") || this.classList.contains("detail-img")) {
                const placeholder = document.createElement("div");
                placeholder.className = "card-img-placeholder";
                placeholder.textContent = "🏺";
                this.replaceWith(placeholder);
            }
        });
    });
});
