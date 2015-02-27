"""Convert OP style CSV files to YNAB format"""

import csv
import argparse
import glob
import re
import ConfigParser
import os

def validate_files(reader, conf_dict):
    """Validates that the CSV matches the config file field definitions
        @param csvfile - Name of the file.
        @param conf_dict - A config object.
    """

    if not conf_dict['date'] in reader.fieldnames:
        print "ERROR: Can't find " + conf_dict['date'] + " from input file"
        return False
    if not conf_dict['payee'] in reader.fieldnames:
        print "ERROR: Can't find " + conf_dict['payee'] + " from input file"
        return False
    if not conf_dict['note'] in reader.fieldnames:
        print "ERROR: Can't find " + conf_dict['note'] + " from input file"
        return False
    if not conf_dict['category'] in reader.fieldnames:
        print "ERROR: Can't find " + conf_dict['category'] + " from input file"
        return False
    if not conf_dict['amount'] in reader.fieldnames:
        print "ERROR: Can't find " + conf_dict['amount'] + " from input file"
        return False

    return True

def convert(source, target, config):
    """Converts the source CSV file to YNAB format.
    Based on the rules defined in config file."""
    strippable_notes = config.items('strippable_notes')
    conf_dict = {
        'amount' : config.get('data_fields', 'amount'),
        'payee' : config.get('data_fields', 'payee'),
        'date' : config.get('data_fields', 'date'),
        'note' : config.get('data_fields', 'note'),
        'category' : config.get('data_fields', 'category')
    }

    with open(source, 'r') as infile:

        reader = csv.DictReader(infile, delimiter=";")
        if not validate_files:
            return False

        with open(target, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, delimiter=',',
                                    fieldnames=['Date', 'Payee', 'Category',
                                                'Memo', 'Outflow', 'Inflow'])
            writer.writeheader()
            for row in reader:
                amount = float(row[conf_dict['amount']].replace(",", "."))
                row_obj = {
                    'Date': row[conf_dict['date']].replace(".", "/"),
                    'Payee': row[conf_dict['payee']],
                    'Category': row[conf_dict['category']],
                    'Memo': "",
                    'Outflow': "",
                    'Inflow': ""
                }

                if float(amount) < 0:
                    row_obj['Outflow'] = (amount * -1)
                else:
                    row_obj['Inflow'] = amount
                row_obj['Memo'] = row[conf_dict['note']]
                if row_obj['Memo']:
                    for strip in strippable_notes:
                        row_obj['Memo'] = re.sub(str(strip[1]), "",
                                                 row_obj['Memo'])
                writer.writerow(row_obj)
    return True

def handle_cmdline():
    """Main function"""
    parser = argparse.ArgumentParser(description='Convert CSV files to YNAB format')
    parser.add_argument('infile', help='CSV file')
    parser.add_argument('bank_config', nargs='?', help='Bank CSV format config file. \
        Defaults to osuuspankki.cfg', default='osuuspankki.cfg')

    args = parser.parse_args()

    list_of_files = glob.glob(args.infile)
    conf = ConfigParser.ConfigParser()
    conf.readfp(open(args.bank_config))

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

handle_cmdline()
