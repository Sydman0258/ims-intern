document.addEventListener("DOMContentLoaded", function () {
    console.log("Mall Management System loaded");

    const cards = document.querySelectorAll(".mall-card");

    cards.forEach((card, index) => {
        card.style.opacity = "0";

        setTimeout(() => {
            card.style.transition = "opacity 1s ease";
            card.style.opacity = "1";
        }, index * 100);
    });
});