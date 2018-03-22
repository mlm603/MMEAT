$(document).ready(function() {

    /*setTimeout(function() {
            console.log('hi')
            $('#test').load('https://projects.fivethirtyeight.com/2018-march-madness-predictions/', function(response) {
                console.log(response.length)
            })
        },
        20000
    );*/

///js/bundle.js?v=6f673ce8085eac7729f02dfc7dafdbdb
    $.get('https://projects.fivethirtyeight.com/2018-march-madness-predictions', function(response) {
        t= response.indexOf("Purdue")
        console.log(t)
        console.log(response.substring(t-100, t+100))
        t = response.indexOf("excitement")
        console.log(response.substring(t-100, t+100))
        //$('#test').html(response.replace("/2018-march-madness-predictions","https://projects.fivethirtyeight.com/2018-march-madness-predictions"))
    });
})