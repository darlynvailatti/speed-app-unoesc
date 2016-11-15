function temposPorVolta(ondeSeraRenderizado,dados) {

    series = []
    seriesParaOGrafico = { name: "tempoTotal", colorByPoint: true, data: []};

    $.each( dados, function( key, val ) {
        var dado = { name: "", y: ""};
        dado.name = "V:" + val.volta;
        dado.y = val.tempo;
        seriesParaOGrafico["data"].push(dado)
    });

    series.push(seriesParaOGrafico);


    // Build the chart
    var chart = {

        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
            type: 'pie'
        },

        credits: {
            enabled: false
        },

        title: {
            text: 'Tempo total por volta'
        },
        tooltip: {
            pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b> <br> <b>Tempo total: {point.y:.2f}</b>',
            valueSuffix: ' s',
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: false
                },
                showInLegend: true
            }
        },

        series: [{}]

    };

    chart.series = series;

    $("#" + ondeSeraRenderizado).highcharts(chart);

}