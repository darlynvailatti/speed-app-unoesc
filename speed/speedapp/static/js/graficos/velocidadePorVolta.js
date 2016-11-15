function velocidadePorVolta(ondeSeraRenderizado,dados) {


    // Build the chart
    var chart = {

         chart: {
            type: 'line',
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
         },

         title: {
            text: 'Velocidade por volta'
         },

         subtitle: {
            text: 'Média e Geral'
         },

         xAxis: { categories: []},

         yAxis: {
             title: {
                 text: 'm/s'
             },
             visible: false
         },


         plotOptions: {
             line: {
                 dataLabels: {
                     enabled: true,
                     format: "{y:.2f}"
                 },
                 enableMouseTracking: false
             }
         },

         credits: {
             enabled: false
         },

         tooltip: {
             pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b> <br>' +
                          '<b>Velocidade média: {point.y:.2f}</b>' +
                          '<b>Velocidade geral: </b>',
             valueSuffix: ' m/s',
         },

         series: []
    };


    //Categorias
    var xAxis = { categories: []};
    $.each( dados, function( key, val ) {
        xAxis.categories.push(key);
    });


    //Series
    series = []
    seriesParaOGrafico = { name: "Velocidade", colorByPoint: true, data: []};

    var serieVelcoidadeMedia = { name: "", data: []};
    serieVelcoidadeMedia.name = "Velocidade media";
    $.each( dados, function( key, val ) {
        serieVelcoidadeMedia.data.push(val.velocidadeMedia);
    });

    var serieVelcoidadeGeral = { name: "", data: []};
    serieVelcoidadeGeral.name = "Velocidade geral";
    $.each( dados, function( key, val ) {
        serieVelcoidadeGeral.data.push(val.velocidadeGeral);
    });


    //Series
    chart.series.push(serieVelcoidadeGeral);
    chart.series.push(serieVelcoidadeMedia);

    //Categorias
    chart.xAxis = xAxis;



    $("#" + ondeSeraRenderizado).highcharts(chart);

}