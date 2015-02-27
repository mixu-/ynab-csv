"""Convert OP style CSV files to YNAB format"""

import csv
import argparse
import glob
import re
import ConfigParser
import os

def convert(source, target, config):

    amountfield = config.get('data_fields', 'amount')
    payeefield = config.get('data_fields', 'payee')
    datefield = config.get('data_fields', 'date')
    notefield = config.get('data_fields', 'note')
    categoryfield = config.get('data_fields', 'category')

    strippable_notes = config.items('strippable_notes')

    with open(source, 'r') as infile:

        reader = csv.DictReader(infile, delimiter=";")
        if not datefield in reader.fieldnames:
            print "ERROR: Can't find " + datefield + " from input file"
            return False
        if not payeefield in reader.fieldnames:
            print "ERROR: Can't find " + payeefield + " from input file"
            return False
        if not notefield in reader.fieldnames:
            print "ERROR: Can't find " + notefield + " from input file"
            return False
        if not categoryfield in reader.fieldnames:
            print "ERROR: Can't find " + categoryfield + " from input file"
            return False
        if not amountfield in reader.fieldnames:
            print "ERROR: Can't find " + amountfield + " from input file"
            return False

        with open(target, 'wb') as csvfile:
            fieldnames = ['Date', 'Payee', 'Category',
                'Memo', 'Outflow', 'Inflow']
            writer = csv.DictWriter(csvfile, delimiter=',',
                fieldnames=fieldnames)
            writer.writeheader()
            for row in reader:
                date = row[datefield].replace(".", "/")
                note = row[notefield]
                amount = float(row[amountfield].replace(",", "."))
                inflow = ''
                outflow = ''
                if float(amount) < 0:
                    outflow = (amount * -1)
                else:
                    inflow = amount
                if note:
                    for strip in strippable_notes:
                        note = re.sub(str(strip[1]), "", note)

                rowObj = {
                    'Date': date,
                    'Payee': row[payeefield],
                    'Category': row[categoryfield],
                    'Memo': note,
                    'Outflow': outflow,
                    'Inflow': inflow}
                writer.writerow(rowObj)
    return True


parser = argparse.ArgumentParser(description='Convert files to YNAB format')
parser.add_argument('infile', metavar='N', nargs='+', help='OP format CSV file')

args = parser.parse_args()

list_of_files = glob.glob(args.infile[0])
conf = ConfigParser.ConfigParser()
conf.readfp(open('osuuspankki.cfg'))

for file_name in list_of_files:
    new_file = file_name.replace(".csv", ".tmp.csv")
    sourcef = open(file_name)
    targetf = open(new_file, "w")
    for i, filerow in enumerate(sourcef):
        writable_str = filerow
        decoded_str = filerow.decode("windows-1252")
        if i == 0:
            tmp = decoded_str.encode("ascii", "ignore")
            writable_str = tmp.decode("ascii").encode("utf8")
        else:
            writable_str = decoded_str.encode("utf8")
        targetf.write(writable_str)
    sourcef.close()
    targetf.close()

    if convert(new_file, file_name.replace(".csv", "_ynab.csv"), conf):
        print "Successfully created " + file_name.replace(".csv", "_ynab.csv")
    else:
        print "Something went wrong with " + file_name
    os.remove(new_file)
