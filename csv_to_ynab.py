"""Convert OP style CSV files to YNAB format"""

from __future__ import print_function
import csv
import sys
import argparse
import glob
import re
import datetime
import configparser
from pprint import pprint, pformat
import hashlib
import os
import ynab
from ynab.rest import ApiException

def validate_files(reader, conf_dict):
    """Validates that the CSV matches the config file field definitions
        @param csvfile - Name of the file.
        @param conf_dict - A config object.
    """

    if not conf_dict['date'] in reader.fieldnames:
        print("ERROR: Can't find " + conf_dict['date'] + " from input file")
        return False
    if not conf_dict['payee'] in reader.fieldnames:
        print("ERROR: Can't find " + conf_dict['payee'] + " from input file")
        return False
    if not conf_dict['note'] in reader.fieldnames:
        print("ERROR: Can't find " + conf_dict['note'] + " from input file")
        return False
    if not conf_dict['category'] in reader.fieldnames:
        print("ERROR: Can't find " + conf_dict['category'] + " from input file")
        return False
    if not conf_dict['amount'] in reader.fieldnames:
        print("ERROR: Can't find " + conf_dict['amount'] + " from input file")
        return False

    return True

def get_configuration(token):
    # Configure API key authorization: bearer
    configuration = ynab.Configuration()
    configuration.api_key['Authorization'] = token
    # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    return configuration

def bulk_upload_transaction(transactions: list, conf: dict):
    """Uploads the transactions list to YNAB."""

    configuration = get_configuration(conf["token"])
    # create an instance of the API class
    ts_list = []
    for ts in transactions:
        iid = hashlib.md5(pformat(ts).encode("utf-8")).hexdigest()
        transact = ynab.SaveTransaction(account_id=conf["account_id"],
                                        date=ts["Date"],
                                        amount=int(ts["Amount"]*1000),
                                        memo=ts["Memo"],
                                        payee_name=ts["Payee"],
                                        import_id=iid)
        ts_list.append(transact)
    bulk_transactions = ynab.BulkTransactions(ts_list)
    api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration))
    try:
        api_response = api_instance.bulk_create_transactions(conf["budget_id"], bulk_transactions)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling TransactionsApi->bulk_create_transaction: %s\n" % e)
        return False
    return True


def upload_transaction(data: dict, conf: dict):
    """Uploads the contents of a dictionary to YNAB.

    YNAB only allows 200 requests per hour.
    """
    configuration = get_configuration(conf["token"])
    # create an instance of the API class
    api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration))
    iid = hashlib.md5(pformat(data).encode("utf-8")).hexdigest()
    transaction = ynab.SaveTransactionWrapper(\
        ynab.SaveTransaction(account_id=conf["account_id"],
                             date=data["Date"],
                             amount=int(data["Amount"]*1000),
                             memo=data["Memo"],
                             payee_name=data["Payee"],
                             import_id=iid,
                             flag_color="blue"
                            )
    )

    try:
        # Create new transaction
        pprint(data)
        api_response = api_instance.create_transaction(conf["budget_id"], transaction)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling TransactionsApi->create_transaction: %s\n" % e)

def convert(source, config, target_file=None, upload_conf=None):
    """Converts the source CSV file to YNAB format.
    Based on the rules defined in config file."""

    strippable_notes = config.items('strippable_notes')
    conf_dict = {
        'amount' : config.get('data_fields', 'amount'),
        'payee' : config.get('data_fields', 'payee'),
        'date' : config.get('data_fields', 'date'),
        'note' : config.get('data_fields', 'note'),
        'category' : config.get('data_fields', 'category'),
        'delimiter' : config.get('data_fields', 'delimiter'),
        'date_format' : config.get('data_fields', 'date_format')
    }

    with open(source, 'r') as infile:
        print("Delimiter: " + conf_dict["delimiter"])
        reader = csv.DictReader(infile, delimiter='\t', quoting=csv.QUOTE_NONE)
        if not validate_files:
            return False

        fieldnames = ['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow']
        csvfile = None
        if target_file:
            csvfile = open(target_file, 'w')
            writer = csv.DictWriter(csvfile, delimiter=',',
                                    fieldnames=fieldnames)
            writer.writeheader()
        upload_transactions = []

        for row in reader:
            amount = float(row[conf_dict['amount']].replace(",", "."))
            row_obj = {
                'Date': row[conf_dict['date']].replace(".", "/"),
                'Payee': row[conf_dict['payee']],
                'Category': row[conf_dict['category']],
                'Memo': ""
            }
            upload_obj = row_obj
            upload_obj["Amount"] = amount

            if float(amount) < 0:
                row_obj["Outflow"] = (amount * -1)
            else:
                row_obj["Inflow"] = amount
            row_obj["Memo"] = row[conf_dict["note"]]
            if row_obj["Memo"]:
                for strip in strippable_notes:
                    row_obj["Memo"] = re.sub(str(strip[1]), "",
                                                row_obj["Memo"])
                upload_obj["Memo"] = row_obj["Memo"]
            if target_file:
                writer.writerow(row_obj)
            if upload_conf:
                date = datetime.datetime.strptime(row[conf_dict["date"]], conf_dict["date_format"])
                upload_obj["Date"] = date.strftime("%Y-%m-%d")
                #upload_transaction(row_obj, upload_conf)
                upload_transactions.append(upload_obj)
    if upload_conf:
        return bulk_upload_transaction(upload_transactions, upload_conf)
    return True

def handle_cmdline():
    """Main function"""
    parser = argparse.ArgumentParser(description='Convert CSV files to YNAB format')
    parser.add_argument('infile', help='CSV file')
    parser.add_argument('--outfile', help='File to save to (optional)')
    parser.add_argument('--bank_config', help='Bank CSV format config file. \
        Defaults to nordea.cfg', default='nordea.cfg')
    parser.add_argument('--token', help="YNAB API token")
    parser.add_argument('--budget_id', help="YNAB budget id")
    parser.add_argument('--account_id', help="YNAB account id")

    args = parser.parse_args()

    list_of_files = glob.glob(args.infile)
    conf = configparser.ConfigParser()
    conf.read_file(open(args.bank_config))

    for file_name in list_of_files:
        new_file = file_name.replace(".csv", ".tmp.csv")
        sourcef = open(file_name)
        targetf = open(new_file, "w")
        start_line = 0

        start_line = int(conf.get('global', 'start_line'))
        print(f"Start line of source CSV: {start_line}")
        counter = 0
        for i, filerow in enumerate(sourcef):
            if i >= start_line:
                #Skip empty rows
                if filerow.strip() != "":
                    counter += 1
                    targetf.write(filerow)
        sourcef.close()
        targetf.close()
        do_upload = False
        if not args.outfile and not args.token:
            print("ERROR: Must define either --outfile or --token")
            sys.exit(1)
        if args.token:
            do_upload = True
            if not args.budget_id or not args.account_id:
                print("ERROR: Must define --budget_id and --account_id for uploading.")
                sys.exit(1)
            upload_conf = {
                "token": args.token,
                "account_id": args.account_id,
                "budget_id": args.budget_id
            }
        if convert(new_file, conf, target_file=args.outfile, upload_conf=upload_conf):
            print(f"Successfully converted {counter} transactions to "
                  + file_name.replace(".csv", "_ynab.csv"))
        else:
            print("Something went wrong with " + file_name)
        os.remove(new_file)

handle_cmdline()
