$('.content-section').click(function() {
    $(this).toggleClass('bi-caret-right bi-caret-down');
});

$('.text-no-ud').hover(function() {
    $(this).toggleClass('bg-secondary text-muted text-light');
});

function copyToClipboard(elementId) {
    var copyText = document.getElementById(elementId);
    copyText.select();
    copyText.setSelectionRange(0, 99999); /* For mobile devices */
    document.execCommand("copy");
    $('#copyText').html("&lt; Copied &gt;")
}