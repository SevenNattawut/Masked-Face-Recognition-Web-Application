$(document).ready(function() {
    $(".editUser").click(function() {
        var userId = $(this).data("id");
        window.location.href = "/editUser/" + userId;
    });
});

$(document).ready(function () {
    $('.delUser').click(function () {
        var id = $(this).data('id');
        var name = $(this).data('name');
        var dep = $(this).data('dep');
        var pos = $(this).data('pos');
        $('#selId').text(id);
        $('#selName').text(name);
        $('#selDep').text(dep);
        $('#selPos').text(pos);
    });
});

var commit_id = document.getElementById("session-data").getAttribute("data-session-id");

$('.delBtn').click(function () {
    var userId = $('#selId').text();
    $.ajax({
        url: "/confirmDel/" + userId,
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({commit_id: commit_id})
    }).done(function(data) {
        // refresh the page
        window.location.reload();
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error("Error: " + textStatus, errorThrown);
    });
});  

$('#faceImgModal').on('show.bs.modal', function (e) {
    let userId = $(e.relatedTarget).data('id');
    let modalContents = "";

    // Generate the contents of the modal
    let unmaskedModalContent = "";
    let imageCount = 0;
    let imgType = "train/";

    // unmask img
    for (let i = 1; i <= 100; i++) {

        if (i > 70) {
            imgType = "test/";
        }

        var imagePath = "faceImgs/unmasked/" + imgType + userId + "/" + i + ".jpg";
        var imageUrl = "/static/" + imagePath;
        if ((i-1) % 5 === 0) {
            if (i-1 > 0) {
                unmaskedModalContent += "</div>";
            }
            unmaskedModalContent += "<div class='unmasked' style='display: flex; flex-wrap: wrap; justify-content: space-between;'>";
        }
        unmaskedModalContent += `<img src="${imageUrl}" style="width:175px; height:175px; margin:10px;">`;
        imageCount++;
    }
    unmaskedModalContent += "</div>";

    // masked img
    let maskedModalContent = "";
    imageCount = 0;
    imgType = "train/";
    for (let i = 1; i <= 100; i++) {
        if (i > 70) {
            imgType = "test/";
        }
        var imagePath = "faceImgs/masked/" + imgType + userId + "/" + i + ".jpg";
        var imageUrl = "/static/" + imagePath;
        if ((i-1) % 5 === 0) {
            if (i-1 > 0) {
                maskedModalContent += "</div>";
            }
            maskedModalContent += "<div class='masked' style='display: none; flex-wrap: wrap; justify-content: space-between;'>";
        }
        maskedModalContent += `<img src="${imageUrl}" style="width:175px; height:175px; margin:10px;">`;
        imageCount++;
    }
    maskedModalContent += "</div>";
    

    modalContents = unmaskedModalContent + maskedModalContent;

    // Set the contents of the modal
    // document.querySelector(".modal-body").innerHTML = modalContents;
    document.getElementById("faceImgDisplayContent").innerHTML = modalContents

    maskDisplay = false
});

let maskDisplay = false;
function toggleMaskDisplay() {
    maskDisplay = !maskDisplay; // toggle maskDisplay value
    
    const unmasked = document.querySelectorAll('.unmasked');
    const masked = document.querySelectorAll('.masked');

    if (maskDisplay){
        document.querySelector('#maskDisplayBtn').innerHTML = 'Image display: Masked';
    }
    else{
        document.querySelector('#maskDisplayBtn').innerHTML = 'Image display: Unmasked';
    }
    
    unmasked.forEach((el) => {
        el.style.display = maskDisplay ? 'none' : 'flex';
    });
    
    masked.forEach((el) => {
        el.style.display = maskDisplay ? 'flex' : 'none';
    });
}