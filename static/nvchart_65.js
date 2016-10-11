$(document).ready(function() {
      $(":radio, .user_update, #countryid").on('change', function() {
           $.getJSON('/background_process', {
                     wage: $('input[name="wage"]').val(),
                     size: $('input[name="esize"]').val(),
                     title: $('input[name="jtitle"]').val(),
                     country: $('select[name="country"]').val(),
                     state: $('select[name="state"]').val(),
                     visa: $('select[name="visa"]').val(),
                     degree: $('input[name="education"]:checked').val(),
                     fed_flag: $('input[name="foreign_ed"]:checked').val(),
                     l_flag: $('input[name="lawyer"]:checked').val(),
                     on_flag: $('input[name="online"]:checked').val(),
                     }, function(data) {
                     $("#result").text(data.result);
                     $("#dollarrange").text(data.wage);
                     $("#sizerange").text(data.size);
                     $("#recmsg").text(data.rec);
                     $("#featmsg").text(data.frec);
                     
                     var prob = String(JSON.parse(data["result"]));
                     prob = prob / 100.0;

                    var pdata = [{
                                "key": "Failure",
                                "color": "#d67777",
                                "values": [
                                           {
                                           "label" : "Approval" ,
                                           "value" : 1.0 - prob
                                           } ,
                                           {
                                           "label" : "No Audit" ,
                                           "value" : 1.0 - prob
                                           }]
                                },
                                {
                                "key": "Success",
                                "color": "#4f99b4",
                                "values": [
                                           {
                                           "label" : "Approval" ,
                                           "value" : prob
                                           } , 
                                           { 
                                           "label" : "No Audit" ,
                                           "value" : prob
                                           }]
                                }
                                ];

                    nv.addGraph(function() {
                                var chart = nv.models.multiBarHorizontalChart()
                                .x(function(d) { return d.label })
                                .y(function(d) { return d.value })
                                .margin({top: 30, right: 20, bottom: 20, left: 100})
                                .tooltips(true)
                                .height(200)
                                
                                // Tells NVD3 to display values with two decimal places.
                                chart.yAxis
                                .tickFormat(d3.format(',.2f'));
                                
                                // Select the "svg" tag and render the chart.
                                d3.select('svg#pplot')
                                .datum(pdata)
                                .call(chart)
                                .style({'height': 200});
                                
                                nv.utils.windowResize(chart.update);
                                
                                return chart;
                                });
                                               
                    var fdata = [{
                                "key": "Feature Importance",
                                "color": "#4f99b4",
                                 "values": [{"label" : "Expected Pay" , "value" : JSON.parse(data["feat_wage"])},
                                            {"label" : "Visa Status" , "value" : JSON.parse(data["feat_visa"])},
                                            {"label" : "Country of Origin" , "value" : JSON.parse(data["feat_isos"])},
                                            {"label" : "Lawyer Used" , "value" : JSON.parse(data["feat_no_lawyer"])},
                                            {"label" : "Education" , "value" : JSON.parse(data["feat_degree"])},
                                            {"label" : "Job Description" , "value" : JSON.parse(data["feat_title"])},
                                            {"label" : "Application Year" , "value" : JSON.parse(data["feat_year"])},
                                            {"label" : "Studied in the US" , "value" : JSON.parse(data["feat_foreign_ed"])},
                                            {"label" : "Company Size" , "value" : JSON.parse(data["feat_esize"])},
                                            {"label" : "Job Location" , "value" : JSON.parse(data["feat_state"])},
                                            {"label" : "Online/Mail" , "value" : JSON.parse(data["feat_online"])}]
                                }];
                                               
                    nv.addGraph(function() {
                                var fchart = nv.models.multiBarHorizontalChart()
                                .x(function(d) { return d.label })
                                .y(function(d) { return d.value })
                                .margin({top: 30, right: 20, bottom: 20, left: 100})
                                .tooltips(true)
                                
                                // Tells NVD3 to display values with two decimal places.
                                fchart.yAxis
                                .tickFormat(d3.format(',.2f'));
                                
                                // Select the "svg" tag and render the chart.
                                d3.select('svg#fplot')
                                .datum(fdata)
                                .call(fchart)
                                
                                nv.utils.windowResize(fchart.update);
                                
                                return fchart;
                                });

                    });
                    return false;
        });
});