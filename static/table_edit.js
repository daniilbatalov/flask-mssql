const Types = {
    'int': 'text',
    'nvarchar': 'text',
    'date': 'date',
    'time': 'time',
    'bit': 'checkbox'
};
let rowsChanged = 0;
$(document).ready(function () {
    $('td').on('click', function () {
        if (this.classList.contains('delete-row-button')) {
            return;
        }
        const tr = this.closest('tr');
        const id = $(tr).find('td:first').text();
        const colName = $(this).closest('table').find('th').eq($(this).index()).text();
        const idColName = $(this).closest('table').find('th')[0].innerText;
        const tableName = $(this).closest('table').parent().attr('id');
        let rowData = $(this).text().trim();
        const type = this.classList[0];

        const inputType = Types[type];

        switch (inputType) {
            case 'date':
                let convertedDate = moment(rowData, 'YYYY-MM-DD').format('YYYY-MM-DD'); // jshint ignore:line
                rowData = convertedDate;
                break;
            case 'time':
                let timeParts = rowData.split(':');
                let convertedTime = new Date(0, 0, 0, timeParts[0], timeParts[1], 0);
                rowData = convertedTime.toTimeString().split(' ')[0];
                break;
            case 'checkbox':
                rowData = rowData.toLowerCase() === 'true';
                break;
            default:
        }


        const isChecked = (inputType === 'checkbox' && rowData === true) ? ' checked' : '';

        const inputElement = '<input type="' + inputType + '" id="value" name="value" value="' + rowData + '"' +
            isChecked + ' required>';
        const modalContent = '<input type="hidden" name="idCol" value="' + idColName + '">' +
            '<input type="hidden" name="id" value="' + id + '">' +
            '<input type="hidden" name="table" value="' + tableName + '">' +
            '<input type="hidden" name="colName" value="' + colName + '">' +
            '<div class="form-group">' +
            '<p>Редактирование колонки ' + colName + ' с id ' + id + '</p>' +
            '</div>' +
            '<div class="form-group">' +
            '<label for="value">' + colName + ':</label>' +
            inputElement + '</div>' +
            '<div class="form-group">' +
            '<button type="submit" id="modalSubmit">Сохранить</button>' +
            '</div>';
        $('#editModal .modal-content').empty();
        $('.modal-content').html(modalContent);
        $('#editModal').modal('show');


    });
    $('button[id$="-add-row"]').on('click', function () {
        const tableId = $(this).attr('id').replace('-add-row', '');
        let newRow = '<tr>';
        $('#' + tableId + ' th').each(function () {
            const columnIndex = $(this).index();
            const cell = $('#' + tableId + ' thead tr:first th:eq(' + columnIndex + ')');
            const type = cell[0].classList[0];
            if (type === 'int' || type === 'nvarchar') {
                if (this.classList.contains('primary')) {
                    var relevantTr = $('#' + tableId + ' tr').last();


                    var primaryTd = relevantTr.find('td').filter(function () {
                        var colIndex = $(this).index(); // Получаем индекс столбца для этого td
                        return $('th:eq(' + colIndex + ')').hasClass('primary');
                    })[0];

                    var value = Number(primaryTd.textContent.trim()) + 1;
                    console.log(value);
                    newRow += '<td class=' + type + '>' + value + '</td>';
                } else {
                    newRow += '<td class=' + type + '><input type="text" value=""></td>';
                }

            } else if (type === 'date') {
                newRow += '<td class=' + type + '><input type="date" value=""></td>';
            } else if (type === 'time') {
                newRow += '<td class=' + type + '><input type="time" value=""></td>';
            } else if (type === 'bit') {
                newRow += '<td class=' + type + '><input type="checkbox" id="value" value="false"></td>';
            } else {
                newRow += '<td></td>';
            }
        });

        newRow += '</tr>';
        $('#' + tableId + ' tbody').append(newRow);
        rowsChanged += 1;

        $('#' + tableId + '-delete').removeClass('d-none');
        $('#' + tableId + ' tbody tr:last').addClass('new-row');
        if (rowsChanged === 0 && $('#' + tableId + ' tbody tr.new-row').length === 0) {
            $('#' + tableId + '-save').addClass('d-none');
        } else {
            $('#' + tableId + '-save').removeClass('d-none');
        }

    });
    $('button[id$="-delete"]').on('click', function () {
        const tableId = $(this).attr('id').replace('-delete', '');
        let lastRow = $('#' + tableId + ' tbody tr:not(.toDelete):last');
        lastRow.addClass('toDelete').hide();
        rowsChanged -= 1;
        if (rowsChanged === 0) {
            $('#' + tableId + '-save').addClass('d-none');
        } else {
            $('#' + tableId + '-save').removeClass('d-none');
        }
        if ($('#' + tableId + ' tbody').length === 0) {
            $('#' + tableId + '-delete').addClass('d-none');
        } else {
            $('#' + tableId + '-delete').removeClass('d-none');
        }
    });
    $('button[id$="-delete-row"]').on('click', function () {
        const tableId = $(this).attr('id').replace(/-[А-Яа-яЁёA-Za-z0-9]*-delete-row/g, '');
        let thisRow = $(this).closest("tr");
        thisRow.addClass('toDelete').hide();
        rowsChanged -= 1;
        if (rowsChanged === 0) {
            $('#' + tableId + '-save').addClass('d-none');
        } else {
            var tmp = $('#' + tableId + '-save');
            $('#' + tableId + '-save').removeClass('d-none');
        }
        if ($('#' + tableId + ' tbody').length === 0) {
            $('#' + tableId + '-delete').addClass('d-none');
        } else {
            $('#' + tableId + '-delete').removeClass('d-none');
        }
    });
    $('button[id$="-save"]').on('click', function () {
        const tableId = $(this).attr('id').replace('-save', '');
        var toDeleteIds = [];
        var newRowsData = [];
        var primaryColumn = $('#' + tableId).find('th.primary');
        var primaryColumnIndex = primaryColumn.index();
        var primaryColumnName = primaryColumn.text();

        $('#' + tableId + ' tr.toDelete.new-row').remove();

        $('#' + tableId + ' tr.toDelete').each(function () {
            var id = $(this).find('td').eq(primaryColumnIndex).text();
            toDeleteIds.push(id);
        });

        // Получение значений новых строк
        $('#' + tableId + ' tr.new-row').each(function () {
            var newRowData = {};
            $(this).find('td').each(function (index) {
                const columnName = $(this).closest('table').find('th').eq(index).text();
                const cellValue = $(this).find('input').length > 0 ? $(this).find('input').val() : $(this).text();
                if (columnName !== '') {
                    newRowData[columnName] = cellValue;
                }

            });
            newRowsData.push(newRowData);
        });

        // Создание объекта с данными для отправки на сервер
        const dataToSend = {
            toDeleteIds: toDeleteIds,
            primaryColumnName: primaryColumnName,
            tableName: tableId,
            newRowsData: newRowsData
        };

        // Отправка данных на сервер через AJAX
        jQuery.ajax({
            type: 'POST',
            url: '/insert_delete',
            data: JSON.stringify(dataToSend),
            contentType: 'application/json',
            success: function (response) {
                const res = response.message;
                const data = response.data;
                const error = response.error;
                const ids = response.ids;
                let resultHtml = '';

                if (res === 'Данные успешно обработаны') {
                    resultHtml = '<div class="alert alert-success" role="alert">' +
                        '<strong>Успех!</strong> Данные успешно обработаны.' +
                        '</div>';
                    $('td input').each(function () {
                        var value = $(this).val();
                        $(this).parent().text(value);
                    });

                } else {

                    resultHtml = '<div class="alert alert-danger" role="alert">' +
                        '<strong>Ошибка!</strong> ' + error + '<p>Удаленные id: </p>' + ids +
                        '</div>';
                }
                $('#editModal .modal-content').empty();
                $('#editModal .modal-content').html(resultHtml);
                $('#editModal').modal('show');

                $('#' + tableId + '-save').addClass('d-none');
            },
            error: function (error) {
                console.error(error);
            }
        });
    });
    $(document).on('change', '#value', function (e) {
        if (this.type === 'checkbox') {
            this.value = e.target.checked.toString();
        }

    });
    $(document).on('click', '#modalSubmit', function (e) {
        e.preventDefault();

        const dataB = {
            'id': $('input[name="id"]').val(),
            'idCol': $('input[name="idCol"]').val(),
            'colName': $('input[name="colName"]').val(),
            'table': $('input[name="table"]').val(),
            'value': $('input[name="value"]').val()
        };


        jQuery.ajax({
            type: 'POST',
            url: '/process_data', // Замените на ваш маршрут Flask
            data: JSON.stringify(dataB), // Преобразуйте данные в JSON
            contentType: 'application/json;charset=UTF-8',
            success: function (response) {

                const res = response.message;
                const data = response.data;
                const error = response.error;
                let resultHtml = '';

                if (res === 'Данные успешно обработаны') {
                    if (dataB.value === 'true' || dataB.value === 'false') {
                        dataB.value = dataB.value.charAt(0).toUpperCase() + dataB.value.slice(1);
                    }
                    resultHtml = '<div class="alert alert-success" role="alert">' +
                        '<strong>Успех!</strong> Данные успешно обработаны.' +
                        '</div>';
                    const tableName = $('#' + dataB.table).find('table');
                    const $row = $(tableName).find('tbody tr').find('td:first-child').filter(function () {
                        return $(this).text() === dataB.id;
                    }).closest('tr');

                    if ($row.length > 0) {
                        const $targetCell = $row.find('td').filter(function () {
                            return this.classList.contains(dataB.colName);
                        });
                        if ($targetCell.length > 0) {
                            $targetCell.text(dataB.value);
                        }

                    }

                } else {

                    resultHtml = '<div class="alert alert-danger" role="alert">' +
                        '<strong>Ошибка!</strong> ' + error +
                        '</div>';
                }
                $('#editModal .modal-content').empty();
                $('#editModal .modal-content').html(resultHtml);

            }
        });
    });

});
