$(document).ready(function() {

	var speed_plot = $.plot("#speed_plot", [ [0,0] ], {
		series: {
			shadowSize: 0,	// Drawing is faster without shadows
			lines: {
				fill: false,
				fillColor: "#077f35"
			}
		},
		axisLabels: {
			show: true
		},
		yaxis: {
			show: true,
			tickDecimals: 0
		},
		yaxes: [{
			axisLabel: 'Speed (rpm)',
			axisLabelPadding: 20
		}],
		xaxis: {
			show: true
		},
		xaxes: [{
			axisLabel: 'Time (s)',
			axisLabelPadding: 4
		}]
	});

	var torque_plot = $.plot("#torque_plot", [ [0,0] ], {
		series: {
			shadowSize: 0,	// Drawing is faster without shadows
			lines: {
				fill: false,
				fillColor: "#cccc00"
			}
		},
		axisLabels: {
			show: true
		},
		yaxis: {
			show: true,
			tickDecimals: 0
		},
		yaxes: [{
			axisLabel: 'Torque (Nm)',
			axisLabelPadding: 20
		}],
		xaxis: {
			show: true
		},
		xaxes: [{
			axisLabel: 'Time (s)',
			axisLabelPadding: 4
		}]
	});

    var speed = 0, 
        torque = 0, 
        time = 0, 
        spd_plot = [], 
        torq_plot = [],
        sample_freq = 50,
        plot_time_shown = 10
        num_data_points = plot_time_shown*sample_freq
        dyno_ws = new WebSocket("ws://localhost:8001/");


    dyno_ws.onmessage = function (event) {
        data = event.data;
        if (data[0] == "f") {
        	sample_freq = parseInt(data.slice(1));
        	num_data_points = sample_freq*plot_time_shown;
        }
        else if (data[0] == "s") { 
			speed = data.slice(1);
        }
        else if (data[0] == "T") {
        	torque = data.slice(1);
        }
        else if (data[0] == "t") {
        	time = data.slice(1);
        	// Format data arrays for plotting
        	if (spd_plot.length < num_data_points && torq_plot.length < num_data_points) {
        		spd_plot.push( [time,speed] );
           		torq_plot.push( [time,torque] );
        	}
        	else {
        		spd_plot = spd_plot.slice(1);
        		torq_plot = torq_plot.slice(1);
        		spd_plot.push( [time,speed] );
        		torq_plot.push( [time,torque] );
        	}
        }
    };

	function draw_plots() {

		speed_plot.setData([{data: spd_plot, label: "Speed", color: "#077f35"}]);
		speed_plot.setupGrid();
		speed_plot.draw();

		torque_plot.setData([{data: torq_plot, label: "Torque", color: "#cccc00"}]);
		torque_plot.setupGrid();
		torque_plot.draw();

		setTimeout(draw_plots, 50);
	}

	draw_plots();

});