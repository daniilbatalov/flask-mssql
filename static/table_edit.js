$(document).ready(function() {
    $('td').on('click', function() {
        var tr = this.parentNode;
        var rowData = $(this).text();
        $('.modal-content').html('<div class="form-group"><p>Редактирование:</p></div>' +  '<div class="form-group"><input type="text" id="value" name="value" value="' + rowData +'" required></div><div class="form-group"><button type="submit">Сохранить</button></div>');
        $('#editModal').modal('show');
    });
});