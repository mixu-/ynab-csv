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
import yaml
import ynab

DRY_RUN = False

from ynab.rest import ApiException

def validate_file(input_file, conf):
    """Validates that the CSV matches the config file field definitions
        @param csvfile - Name of the file.
        @param conf_dict - A config object.
    """

    reader = csv.DictReader(open(input_file, "r"), delimiter='\t', quoting=csv.QUOTE_NONE)
    fieldnames = reader.fieldnames
    if not conf['date'] in fieldnames:
        print(f"ERROR: Can't find {conf['date']} from input file")
        return False
    if not conf['payee'] in fieldnames:
        print(f"ERROR: Can't find {conf['payee']} from input file")
        return False
    if not conf['note'] in fieldnames:
        print(f"ERROR: Can't find {conf['note']} from input file")
        return False
    if not conf['category'] in fieldnames:
        print(f"ERROR: Can't find {conf['category']} from input file")
        return False
    if not conf['amount'] in fieldnames:
        print(f"ERROR: Can't find {conf['amount']} from input file")
        return False

    return True

def get_configuration(token):
    # Configure API key authorization: bearer
    configuration = ynab.Configuration()
    configuration.api_key['Authorization'] = token
    # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    return configuration

def get_upload_conf(csv_file, secrets_file):
    with open(secrets_file, 'r') as ymlfile:
        secrets = yaml.load(ymlfile, Loader=yaml.FullLoader)

    pprint(secrets)
    account = None
    for item in secrets["account_map"]:
        for pattern in item["patterns"]:
            if pattern in csv_file:
                account = item
                pprint(item)
                break
    return {
        "token": secrets["token"],
        "account_id": account["id"],
        "account_name": account["name"],
        "budget_id": secrets["budget_id"]
    }

def bulk_upload_transaction(transactions: list, conf: dict):
    """Uploads the transactions list to YNAB."""

    configuration = get_configuration(conf["token"])
    # create an instance of the API class
    ts_list = []
    for ts in transactions:
        # Increment the last number in case you need to re-upload files.
        iid = hashlib.md5(pformat(ts).encode("utf-8")).hexdigest() + "-2"
        transact = ynab.SaveTransaction(account_id=conf["account_id"],
                                        date=ts["Date"],
                                        amount=int(ts["Amount"]*1000),
                                        memo=ts["Memo"][0:199],
                                        payee_name=ts["Payee"],
                                        import_id=iid)
        ts_list.append(transact)
    bulk_transactions = ynab.BulkTransactions(ts_list)
    api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration))
    if DRY_RUN:
        pprint(ts_list)
    else:
        try:
            api_response = api_instance.bulk_create_transactions(conf["budget_id"], bulk_transactions)
            pprint(api_response)
        except ApiException as e:
            print("Exception when calling TransactionsApi->bulk_create_transaction: %s\n" % e)
            return False
    return True


# def upload_transaction(data: dict, conf: dict):
#     """Uploads the contents of a dictionary to YNAB.

#     YNAB only allows 200 requests per hour.
#     """
#     configuration = get_configuration(conf["token"])
#     # create an instance of the API class
#     api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration))
#     iid = hashlib.md5(pformat(data).encode("utf-8")).hexdigest()
#     transaction = ynab.SaveTransactionWrapper(\
#         ynab.SaveTransaction(account_id=conf["account_id"],
#                              date=data["Date"],
#                              amount=int(data["Amount"]*1000),
#                              memo=data["Memo"],
#                              payee_name=data["Payee"],
#                              import_id=iid,
#                              flag_color="blue"
#                             )
#     )

#     try:
#         # Create new transaction
#         pprint(data)
#         api_response = api_instance.create_transaction(conf["budget_id"], transaction)
#         pprint(api_response)
#     except ApiException as e:
#         print("Exception when calling TransactionsApi->create_transaction: %s\n" % e)

def clean_up_csv(file_name, conf):
    """Returns the path to a cleaned up CSV file"""

    new_file = file_name + ".tmp"
    with open(file_name, "r") as sourcef:
        with open(new_file, "w") as targetf:
            start_line = int(conf.get('global', 'start_line'))
            print(f"Start line of source CSV: {start_line}")
            for i, filerow in enumerate(sourcef):
                if i >= start_line:
                    #Skip empty rows
                    if filerow.strip() != "":
                        targetf.write(filerow)
    return new_file

def convert(source, config, target_file=None, upload_conf=None):
    """Converts the source CSV file to YNAB format.
    Based on the rules defined in config file."""

    strippable_notes = config.items('strippable_notes')
    conf_dict = config['data_fields']

    if not validate_file(source, config["data_fields"]):
        print(f"ERROR: Invalid fields in {source}")
        return False, 0
    with open(source, 'r') as infile:
        print("Delimiter: " + conf_dict['delimiter'])
        reader = csv.DictReader(infile, delimiter='\t', quoting=csv.QUOTE_NONE)

        fieldnames = ['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow']
        csvfile = None
        if target_file:
            print(f"Writing to {target_file}")
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
                upload_transactions.append(upload_obj)
    counter = len(upload_transactions)
    print(f"Found {counter} transactions")
    if counter == 0:
        return False, 0
    if upload_conf:
        ok = bulk_upload_transaction(upload_transactions, upload_conf)
    return ok, counter

def handle_cmdline():
    """Main function"""
    parser = argparse.ArgumentParser(description='Convert CSV files to YNAB format')
    parser.add_argument('infile', help='CSV file')
    parser.add_argument('--outfile', help='File to save to (optional)')
    parser.add_argument('--bank_config', help='Bank CSV format config file. \
        Defaults to nordea.cfg', default='nordea.cfg')
    parser.add_argument('--upload', default=False, action='store_true')
    parser.add_argument('--upload_config', default='my_secrets.yml',
                        help='Upload configuration file with token and account mapping.')

    args = parser.parse_args()

    if not args.outfile and not args.upload:
        print("ERROR: Must use either --outfile or --upload")
        sys.exit(1)
    list_of_files = glob.glob(args.infile)
    if not list_of_files:
        print("No files matched infile search criteria!")
        sys.exit(1)
    conf = configparser.ConfigParser()
    conf.read_file(open(args.bank_config, "r"))

    for file_name in list_of_files:
        clean_file = clean_up_csv(file_name, conf)
        if args.upload:
            upload_conf = get_upload_conf(file_name, args.upload_config)
        success, counter = convert(clean_file, conf,
                                   target_file=args.outfile,
                                   upload_conf=upload_conf)
        if success:
            print(f"Successfully processed {counter} transactions.")
        else:
            print("Something went wrong with " + file_name)
        print(f"Deleting {clean_file}")
        os.remove(clean_file)

handle_cmdline()
