# ynab-csv
Tooling for fetching & converting bank CSV files to the format YNAB uses.

Has been tested on Finnish Osuuspankki CSV files. If you're able to use ynab-csv for importing CSVs to YNAB from some other bank, upload me your config file. I'll add it to the project.

<h3>File descriptions:</h3>

<ul>
<li>*csv_to_ynab.py* - A Python script for converting a CSV file to YNAB CSV format.</li>
<li>*osuuspankki.cfg* - A config file for the python script. Specific to Osuuspankki.</li>
<li>*op_csv_fetcher.user.js* - A Greasemonkey script that can be used to fetch CSVs faster. Using this requires you to make small modifications to Javascript. If you have no coding skills, forget about it.</li>
</ul>
