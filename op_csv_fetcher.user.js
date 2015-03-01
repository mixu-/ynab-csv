// ==UserScript==
// @name        OP_CSV_fetcher
// @namespace   csv_fetcher
// @description Fetches account records in CSV from specified accounts.
// @include     http://www.greasespot.net/p/welcome.html?utm_source=xpi&utm_medium=xpi&utm_campaign=welcome&utm_content=2.3
// @require     http://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js
// @version     1
// @grant       none
// ==/UserScript==
console.log("Loading CSV fetcher greasemonkey script");

var today = new Date();
var dd = today.getDate();
var mm = today.getMonth()+1; //January is 0!
var yyyy = today.getFullYear();

if( dd < 10 ) {
    dd='0'+dd;
}

if( mm < 10 ) {
    mm='0'+mm;
}

today = dd+'-'+mm+'-'+yyyy;

var base_url = "https://www.op.fi/";

//Moneltako päivältä tiedot haetaan?
var day_count = 90;

//Lisää tilinumerosi tähän listaan "vanhassa muodossa pelkkinä kokonaislukuina" - ei siis IBAN.
//Esim. 5271521231231
var account_nrs = { kayttotili: "",
                    saastotili: ""
                  };


$("body").prepend("<div id='fetcher' style='float: " +
                  "right; width: 300px; font-size: 0.7em; text-align: left;'>" +
                  "<h2>OP CSV Fetcher</h2>" +
                  "<p>Tämä elementti on OP_CSV_fetcher Greasemonkey-skriptin " +
                  "tuottama. Hae tilitapahtumia klikkaamalla kunkin tilin " +
                  "alla listatut linkit järjestyksessä läpi.</p></div>");

$.each(account_nrs, function(accountname, account) {
    console.log(account);
    var output_file = account + "_" + today + "-" + day_count + "_days.csv";
    var step1 = base_url + "op?id=12402&tilinro=" + account;
    var step2 = base_url + "op?id=12402&tilinro=" + account + "&paiva_lkm=" + day_count + "&srcpl=3&act_tarkista=true";
    var step3 = base_url + "/tulostus/tiliote2/" + output_file + "?id=12402&csv=1&act_valinta=true&muoto=3&srcpl=3";
    $("#fetcher").append("<h3>Tili: " + accountname + " " + account + "</h3>");
    $("#fetcher").append("<p><a href='" + step1 + "'>1. Tilit -> Verkkotiliote</a></p>");
    $("#fetcher").append("<p><a href='" + step2 + "'>2. Hae viimeisimmät tapahtumat " + day_count + " päivän ajalta.</a></p>");
    $("#fetcher").append("<p><a href='" + step3 + "'>3. Lataa pelkät tilitapahtumat tiedostona (csv)</a></p>");
});
