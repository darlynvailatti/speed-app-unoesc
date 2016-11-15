function velocidadeDasVoltasPorAresta(ondeSeraRenderizado,dados)  {

    var chart ={

        chart: {
            type: 'bar'
        },
        title: {
            text: 'Velocidade por arestas'
        },
        subtitle: {
            text: ''
        },
        xAxis: {
            categories: []
        },
        yAxis: {
            min: 0,
            title: {
                text: 'Metros por segundo',
                align: 'high'
            },
            labels: {
                overflow: 'justify'
            }
        },
        tooltip: {
            pointFormat:'<b>Aresta: {series.name}</b> <br>' +
                        '<b>Velocidade: {point.y:.2f} m/s</b>',
            valueSuffix: ' m/s',
        },
        plotOptions: {
            bar: {
                dataLabels: {
                    enabled: true,
                    format: "{y:.2f}"
                }
            }
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'top',
            x: -40,
            y: 80,
            floating: true,
            borderWidth: 1,
            backgroundColor: ((Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'),
            shadow: true,
            enabled: false
        },
        credits: {
            enabled: false
        },
        series: []
    };

    //Categorias
    var xAxis = { categories: []};
    $.each( dados, function( key, val ) {
        $.each(val, function( keyV, valV){
            console.log(valV.numero);
            xAxis.categories.push(valV.numero);
        });
    });

    //Series
    var series = [];

    $.each( dados, function( key, val ){

         //Voltas
         $.each(val, function( keyV, valV){
            xAxis.categories.push(valV.numero);

            //Arestas
            $.each(valV.arestas, function( keyA, valA){
                console.log(valA);

                serie = {
                    name: {},
                    data: []
                };
                serie.name = valA.descricao;

                //Ja existe serie com este nome?
                index = series.findIndex(s => s.name == serie.name);

                //Ja existe
                if(index >= 0){
                    series[index].data.push(valA.velocidade);
                }else{
                //Nao existe
                    serie.data.push(valA.velocidade);
                    series.push(serie);
                }

            });
         });
    });


   //Categorias
   chart.xAxis = xAxis;
   chart.series = series;

    $("#" + ondeSeraRenderizado).highcharts(chart);
}