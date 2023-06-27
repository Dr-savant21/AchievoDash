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