/*   
   Copyright 2011 Martin Hawksey
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

// Usage
//  1. Enter sheet name where data is to be written below
        var SHEET_NAME = "Transactions";
        
//  2. Run > setup
//
//  3. Publish > Deploy as web app 
//    - enter Project Version name and click 'Save New Version' 
//    - set security level and enable service (most likely execute as 'me' and access 'anyone, even anonymously) 
//
//  4. Copy the 'Current web app URL' and post this in your form/script action 
//
//  5. Insert column names on your destination sheet matching the parameter names of the data you are passing in (exactly matching case)

var SCRIPT_PROP = PropertiesService.getScriptProperties(); // new property service

// If you don't want to expose either GET or POST methods you can comment out the appropriate function
function doGet(e){
  return handleResponse(e);
}

function doPost(e){
  return handleResponse(e);
}

function handleResponse(e) {
  var ret = false;
  // https://developers.google.com/apps-script/reference/lock/
  var lock = LockService.getScriptLock();
  try { 
    lock.tryLock(30000) // wait 30 seconds before conceding defeat.
    try {
      // next set where we write the data - you could write to multiple/alternate destinations
      var doc = SpreadsheetApp.openById(SCRIPT_PROP.getProperty("key"));
      var sheet = doc.getSheetByName(SHEET_NAME);
      
      // we'll assume header is in row 1 but you can override with header_row in GET/POST data
      var headRow = e.parameter.header_row || 1;
      var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
      var row = []; 
      // loop through the header columns
      for (i in headers){
        if (headers[i] == "Timestamp"){ // special case if you include a 'Timestamp' column
          row.push(new Date());
        } else { // else use header name to get data
          if (e.parameter[headers[i]] != undefined) {
            row.push(e.parameter[headers[i]]);
          }
          else {
            ret = ContentService
            .createTextOutput(JSON.stringify({"result":"error", "error1": e}))
            .setMimeType(ContentService.MimeType.JSON);
          }
        }
      }
      var nextRow = sheet.getLastRow()+1; // get next row
      // more efficient to set values as [][] array than individually
      sheet.getRange(nextRow, 1, 1, row.length).setValues([row]);
      SpreadsheetApp.flush();
      // return json success results
      ret = ContentService
      .createTextOutput(JSON.stringify({"result":"success", "row": nextRow}))
      .setMimeType(ContentService.MimeType.JSON);
    } catch(e){
      // if error return this
      ret = ContentService
      .createTextOutput(JSON.stringify({"result":"error", "error2": e}))
      .setMimeType(ContentService.MimeType.JSON);
    }
    lock.releaseLock();
  } catch(e) {
    ret = ContentService
          .createTextOutput(JSON.stringify({"result":"error", "lockerror": e}))
          .setMimeType(ContentService.MimeType.JSON);
  }
  return ret
}

function setup() {
    var doc = SpreadsheetApp.getActiveSpreadsheet();
    SCRIPT_PROP.setProperty("key", doc.getId());
}
