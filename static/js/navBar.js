$('#trainBtn').click(function () {
    let sessionId = $("#session-data").data("session-id");
    $.ajax({
        url: "/trainModel",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ commit_id: sessionId })
    }).fail(function (jqXHR, textStatus, errorThrown) {
        console.error("Error: " + textStatus, errorThrown);
    });
});

$('#commitLog').on('show.bs.modal', function (e) {
    $.ajax({
        type: "GET",
        url: "/getLog",
        dataType: "json",
        success: function (response) {
            // Check if the response is empty or null
            if (response == null || response.length == 0) {
                // Display a message if no data is received
                $('#commitLog .modal-body').html("No data available");
            }
            else {
                // Create a table to display the logs data
                var table = $('<table>').addClass('table table-striped');
                // Create the table header row
                var header = $('<thead>');
                var headerRow = $('<tr>');
                $('<th>').text('commit_ID').appendTo(headerRow);
                $('<th>').text('Date').appendTo(headerRow);
                $('<th>').text('Time').appendTo(headerRow);
                $('<th>').text('Committer').appendTo(headerRow);
                $('<th>').text('Commit Type').appendTo(headerRow);
                $('<th>').text('Committed Target').appendTo(headerRow);
                headerRow.appendTo(header);
                header.appendTo(table);

                var body = $('<tbody>');
                // Loop through the logs data and add each row to the table
                $.each(response, function (index, log) {
                    console.log(response);
                    var row = $('<tr>');
                    $('<td>').text(log[0]).appendTo(row);
                    var date = new Date(log[2]);
                    var offset = date.getTimezoneOffset(); // get the UTC offset in minutes
                    date.setTime(date.getTime() + (offset) * 60 * 1000); // set the time with an offset of GMT+7 (420 = 7 * 60)
                    var options = { day: '2-digit', month: '2-digit', year: 'numeric' };
                    $('<td>').text(date.toLocaleDateString('en-GB', options)).appendTo(row); // display formatted date
                    $('<td>').text(date.toLocaleTimeString()).appendTo(row); // Separate time
                    $('<td>').text(log[1]).appendTo(row);
                    let actionData = JSON.parse(log[3]);
                    $('<td>').text(actionData.type).appendTo(row);
                    if (actionData.target == null) {
                        $('<td>').text("-").appendTo(row);
                    }
                    else{
                        $('<td>').text(actionData.target).appendTo(row);
                    }
                    row.appendTo(body);
                });
                body.appendTo(table);
                // Display the table in the modal body
                $('#log_table').html(table);
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log(textStatus, errorThrown);
            // Display a message if an error occurs
            $('#log_table').html("Error occurred while fetching data");
        }
    });
});