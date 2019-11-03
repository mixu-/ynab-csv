# ynab-csv
Tooling for fetching & converting bank CSV files to the format YNAB uses.

Has been tested on Finnish Nordea CSV files. If you're able to use ynab-csv for importing CSVs to YNAB from some other bank, upload me your config file. I'll add it to the project. There are some legacy files included for Osuuspankki which may or may not work at this point.

## Dependencies

`pip3 install ynab`

## File descriptions

* *csv_to_ynab.py* - A Python script for working with YNAB4 or the new YNAB web app. Can do CSV conversion and upload to YNAB API.
* *nordea.cfg* - Nordea config file
* *osuuspankki.cfg* - (abandoned) A config file for the python script. Specific to Osuuspankki.
* *op_csv_fetcher.user.js* - (abandoned) A Greasemonkey script that can be used to fetch CSVs faster. Using this requires you to make small modifications to Javascript. If you have no coding skills, forget about it.
