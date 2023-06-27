$(document).ready(function () {
    // Show all cards by default
    $(".task-body .col-lg-4").show();

    // Handle navigation clicks
    $(".pagination .page-link").click(function () {
        var target = $(this).data("target"); // Get the target value

        // Show or hide cards based on the target value
        if (target === "all") {
            $(".task-body .col-lg-4").show();
        } else {
            $(".task-body .col-lg-4").hide();
            $("[data-card='" + target + "']").parent().show();
        }

        // Update active navigation link
        $(".pagination .page-item").removeClass("active");
        $(this).parent().addClass("active");

        return false; // Prevent default link behavior
    });
});

const cards = document.querySelectorAll('.filecard');

cards.forEach(function (card) {
    const iconOption = card.querySelector('.icon-option');
    const iElement = card.querySelector('.icon-option i');
    const ulElement = card.querySelector('.icon-option .ul');

    card.addEventListener('mouseenter', function () {
        iElement.style.display = 'inline';
    });

    card.addEventListener('mouseleave', function () {
        if (!iconOption.classList.contains('show')) {
            iElement.style.display = 'none';
        }
    });

    iElement.addEventListener('click', function (e) {
        e.stopPropagation();
        iconOption.classList.toggle('show');
    });

    ulElement.addEventListener('mouseleave', function () {
        ulElement.classList.remove('show');
    });
});


