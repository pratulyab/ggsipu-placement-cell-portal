var Download = (function() {

	function download_resume(e) {
		e.preventDefault();
		var $a = $(this),
			url = $a.attr('href');
		swal({
			title: "Note",
			text: "Please note that you are requesting to download the resumes of all the students currently enrolled in this session. You won't be able to make more download requests until next 10 minutes. Are you sure to proceed?",
			type: "warning",
			showCancelButton: true,
			confirmButtonColor: "#DD6B55",
			confirmButtonText: "Proceed",
			closeOnConfirm: false,
			showLoaderOnConfirm: true,
			allowEscapeKey: false,
			allowOutsideClick: false,
			},
			function(){
				$.ajax({
					url: url,
					type: 'GET',
					data: {},
					processData: true,
					success: function(data, status, xhr){
						swal({
							title: "Success!",
							text: "Your request is being processed. A notification containing the download link will be generated. Please go to the home page, and look for new notifications. This otherwise instantaneous process, sometimes might take a while. We request you to refresh the home page in intervals to look for new notifications.",
							type: "success",
							allowEscapeKey: true,
							allowOutsideClick: true,
							confirmButtonText: "Go To Home Page"
						},
							function(){window.location='/'});
					},
					error: function(xhr, status, error){
						if (xhr.status >= 400 && xhr.status < 500) {
							var error_msg = xhr.responseJSON['error'] ? xhr.responseJSON['error'] : "Error Occurred.";
							swal("Error!", error_msg, "error");
						} else if (xhr.status > 500) {
							swal("Oops..", "Sorry, an unexpected error occurred. Please try again after sometime.", "error");
						}
					}
				});
			});
	}

	function serve_resume(e) {
		e.preventDefault();
		var $a = $(this),
			url = $a.attr('href');
		$.ajax({
			url: url,
			type: 'GET',
			data: {},
			processData: true,
			success: function(data, status, xhr){
				swal({
					title: "Success!",
					text: "Your download has begun. Please don't close the browser until your download completes. Also, to get updated resumes, you need to request again by choosing to \"Download Resumes\" from session's settings page.",
					type: "success",
					allowEscapeKey: true,
					allowOutsideClick: true,
				});
				window.location = url;
			},
			error: function(xhr, status, error){
				if (xhr.status >= 400 && xhr.status < 500) {
					var error_msg = xhr.responseJSON && xhr.responseJSON['error'] ? xhr.responseJSON['error'] : "Error Occurred.";
					error_msg += "\nIf you want to download updated resumes, then request the download link again by choosing to \"Download Resumes\" from session's settings page.";
					swal("Error!", error_msg, "error");
				} else if (xhr.status > 500) {
					swal("Oops..", "Sorry, an unexpected error occurred. Please try again after sometime.", "error");
				}
			}
		});

	}

	return {
		request: function() {
			$('.resume').on('click', download_resume);
		},
		serve: function() {
			$('.resume-dl').on('click', serve_resume);
		}
	}
})();
