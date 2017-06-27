$.ajax({
            url: url,
            type: type,
            data: form_data,
            processData: false,
            contentType: false,
            beforeSend: function() {
                inProcess = true;
                $(form).find('button').addClass('disabled');
                showPreloader();
            },
            complete: function() {
                inProcess = false;
                removePreloader();
                $(form).find('button').removeClass('disabled');
            },
            success: function(data, status, xhr){
                if (data.refresh) {
                    swal({
                        title: 'Success',
                        text: data.message,
                        type: 'success',
                        allowEscapeKey: false,
                        }, function(e) {
                            window.location.href = '';
                        }
                    );
                } else
                    swal("Success!", data.message, "success");

            },
            error: function(xhr, status, error){
                if (xhr.responseJSON['error']){
                    $(form).parent().prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
                }
                var form_errors = xhr.responseJSON['errors'];
                addErrorsToForm(form_errors, form_id);
                if (xhr.responseJSON['refresh']) {
                    swal({
                        title: 'Error',
                        text: xhr.responseJSON['message'],
                        type: 'error',
                        allowOutsideClick: true,
                        }, function(e) {
                            window.location.href = '';
                        }
                    );
                } else
                    swal("Error!", xhr.responseJSON['message'] , "error");
            }
        });