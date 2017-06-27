var Stats = (function() {
	var statsForm = null,
		dataDiv = null,
		preloaderDiv = null;

	function addOptionsToSelectField(data, $select_el){
		$select_el.children().slice(1).remove();
		for(var datum of data) {
			var $option = $('<option/>');
			$option.attr('value', datum.value);
			$option.html(datum.html);
			$select_el.append($option);
		}
		$select_el.material_select('destroy');
		$select_el.prop('disabled', false);
		$select_el.material_select();
		Materialize.updateTextFields();
	}

	function getYears() {
		dataDiv.empty();
		var college_field = statsForm.find('#id_college'),
			year_field = statsForm.find('#id_year');
		$.ajax({
			url: statsForm.attr('action'),
			type: statsForm.attr('method'),
			data: {'years': true, 'college': $(college_field.children()[college_field.prop('selectedIndex')]).attr('value')},
			processData: true,
			contentType: false,
			beforeSend: function() {
				preloaderDiv.html($('<div class="progress"><div class="indeterminate"></div></div>'));
			},
			complete: function() {
				preloaderDiv.empty();
			},
			success: function(data, status, xhr) {
				addOptionsToSelectField(data.years, year_field);
				year_field.on('change', getStats);
				Materialize.toast($('<span class="flow-text yellow-text"/>').html('Choose a year').css('fontWeight', '400'), 2000);
			},
			error: function(xhr, status, error) {
				/*
				year_field.children().slice(1).remove();
				year_field.prop('disabled', true);
				year_field.material_select();
				*/
				swal('Error', xhr.responseJSON['errors'], 'error');
//			  	Materialize.toast($('<span class="flow-text red-text" />').html(xhr.responseJSON['errors']).css('fontWeight', 'bold'), 2000);
			}
		});
	}

	function getStats() {
		var college_field = statsForm.find('#id_college'),
			year_field = statsForm.find('#id_year');
		$.ajax({
			url: statsForm.attr('action'),
			type: statsForm.attr('method'),
			data: {
					'stats': true,
					'year': $(year_field.children()[year_field.prop('selectedIndex')]).attr('value'),
					'college': $(college_field.children()[college_field.prop('selectedIndex')]).attr('value')
			},
			processData: true,
			contentType: false,
			beforeSend: function() {
				preloaderDiv.html($('<div class="progress"><div class="indeterminate"></div></div>'));
			},
			complete: function() {
				preloaderDiv.empty();
			},
			success: function(data, status, xhr) {
				dataDiv.empty();
				dataDiv.append($(data.table));
				showGraph(data.graph);
			},
			error: function(xhr, status, error) {
				/*
				year_field.children().slice(1).remove();
				year_field.prop('disabled', true);
				year_field.material_select();
				*/
				swal('Error', xhr.responseJSON['errors'], 'error');
//			   	Materialize.toast($('<span class="flow-text red-text" />').html(xhr.responseJSON['errors']).css('fontWeight', 'bold'), 5000);
			}

		});
	}

	function showGraph(data) {
		dataDiv.prepend('<div class="col s12 m6"><canvas id="graph"></canvas></div>');
		var ctx = document.getElementById('graph').getContext('2d');
		var between254 = [],
			between46 = [],
			between69 = [],
			greater9 = [];
		for (var i=0; i<data.length; i++){
			point = data[i];
			if (point.salary < 4)
				between254.push({'x': point.salary, 'y': point.offers, 'r': 7, 'label': point.company});
			else if (point.salary < 6)
				between46.push({'x': point.salary, 'y': point.offers, 'r': 7, 'label': point.company});
			else if (point.salary < 9)
				between69.push({'x': point.salary, 'y': point.offers, 'r': 7, 'label': point.company});
			else
				greater9.push({'x': point.salary, 'y': point.offers, 'r': 7, 'label': point.company});
		}
		var scatterChart = new Chart(ctx, {
			type: 'bubble',
			data: {
			datasets: [
					{
						label: '2.5 - 4 LPA',
						backgroundColor: '#ff6384',
						borderColor: '#ff6384',
						data: between254
					},
					{
						label: '4 - 6 LPA',
						backgroundColor: '#36a2eb',
						borderColor: '#36a2eb',
						data: between46
					},
					{
						label: '6 - 9 LPA',
						backgroundColor: '#009688',
						borderColor: '#009688',
						data: between69
					},
					{
						label: '> 9 LPA',
						backgroundColor: '#ffce56',
						borderColor: '#ffce56',
						data: greater9
					},
				],
			},
			options: {
				scales: {
					xAxes: [{
						type: 'linear',
						position: 'bottom',
						scaleLabel: {
							display: true,
							labelString: 'Salary (Lakhs P.A.)',
						},
					}],
					yAxes: [{
						type: 'linear',
						scaleLabel: {
							display: true,
							labelString: 'No. of Offers',
						},
					}]
				},
				tooltips: {
					callbacks: {
						title: function(tooltipitem, chart) {
							return chart.datasets[tooltipitem[0].datasetIndex].data[tooltipitem[0].index].label;
						},
						label: function(tooltipitem, chart) {
							var salary = tooltipitem.xLabel + " LPA",
								offers = tooltipitem.yLabel ? tooltipitem.yLabel + " offers" : "Result Awaited";
							return salary + ", " + offers;
						},
					}
				}
			}
		});
	}

	return {
		init: function() {
			statsForm = $('#stats-form');
			statsForm.find('#id_college').on('change', getYears);
			dataDiv = $('#stats-data');
			preloaderDiv = $('#stats-preloader');
		}
	}
})();
