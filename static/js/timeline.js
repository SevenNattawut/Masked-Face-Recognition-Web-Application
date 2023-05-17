$('#infoModal').on('show.bs.modal', function (e) {
    let infoStr = $(e.relatedTarget).data('info');
    let infoArray = infoStr.replace(/'/g, '"');
    let infoJson = JSON.parse(infoArray);

    let imagePath = "detectedFaces/" + infoJson[0] + ".jpg";
    let imageUrl = "/static/" + imagePath;

    let modalContents = `
            <div class="d-flex">
                <div>
                    <img src="${imageUrl}" style="width:175px; height:175px; margin-right: 10px;">
                </div>
                <div>
                    Timestamp: ${infoJson[1]} <br>
                    ID: ${infoJson[2].id} <br>
                    Name: ${infoJson[2].name} <br>
                    Department: ${infoJson[2].department} <br>
                    Position: ${infoJson[2].position} <br>
                </div>
            </div>
            `
    document.getElementById("infoModalBody").innerHTML = modalContents
});