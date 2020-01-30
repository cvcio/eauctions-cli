"""
Import Libraries
"""
from click import progressbar, echo, secho, group, style, option, File, Path, confirm, argument
from click import Context as ctx
from time import sleep, strftime
from bs4 import BeautifulSoup
from price_parser import Price

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

import pandas as pd

import datetime
import re
import csv
import os
import ast

from methods.methods import fetch, fetch_file
from utils.utils import clean_keyword, format_afm, afm_type, format_hastener


"""
Set Constants
"""

REQ_THRESHOLD = 1.5  # sleep for 1.5 seconds between each request
PAUSE_THRESHOLD = 60 * 15  # pause program for 15 minutes
BASE_DETAILS_URL = 'https://www.eauction.gr/Auction/Details/'
BASE_DOWNLOAD_URL = 'https://www.eauction.gr/Auction/GetAuctionFile'


"""
Initialize CLI Group Commands
"""


@group()
def cli():
    """
    eauctions CLI
    \n
    A better description can be added here!
    """
    pass


@cli.command()
@option('-s', '--start', default=970, help='Start from page ID.', show_default=True)
@option('-e', '--end', default=80000, help='End at page ID.', show_default=True)
@option('-l', '--list_of_ids', default=[], show_default=True, help='Comma separeted list of ids.')
@option('-b', '--backup', default='backup', show_default=True, help='Backup files in folder (root folder).')
def scrape(start, end, list_of_ids, backup):
    """
    Scrape command will fetch a range of URLs from the eauctions.gr website, given a range of IDs,
    saving appropriate information (html documents) into the backup folder.
    \n
    Disclaimer: Although eauctions scraping policy prohibits such actions, we sincerely dont't give a fuck.
    """
    if len(list_of_ids) > 0:
        list_of_ids = [int(n) for n in list_of_ids.split(',')]
        list_of_ids = list(set(list_of_ids))
    else:
        list_of_ids = []

    length = (end - (start + 1)) if len(list_of_ids) == 0 else len(list_of_ids)

    if length < 0 and len(list_of_ids) == 0:
        secho('Start ID ({0}) is greater than end ID ({1})'.format(
            start, end + 1), fg='red')
        ctx.abort(0)

    """
    Create Directories
    """
    if backup != '':
        if not os.path.exists(backup + '/csv'):
            os.makedirs(backup + '/csv')
        if not os.path.exists(backup + '/files'):
            os.makedirs(backup + '/files')
        if not os.path.exists(backup + '/html'):
            os.makedirs(backup + '/html')

    secho('Scraping Process Started', fg='green')

    """
    progress bar options
    """

    label = 'Scraping {:,} Document{}'.format(
        length, '' if length == 1 else 's')
    bar_template = '%(label)s %(bar)s | %(info)s'
    fill_char = style(u'█', fg='white')

    errored = []
    auto_pause = False

    with progressbar(
        range(start, end + 1) if len(list_of_ids) == 0 else list_of_ids, label=label,
        width=50, show_pos=True, show_percent=True, info_sep=' ',
        bar_template=bar_template, empty_char='-', fill_char=fill_char
    ) as ids:
        # open output file stream
        """
        iterate over range of document ids
        """
        for id in ids:
            """
            invoke the scraping command for given doc id
            """

            if os.path.isfile(backup + '/html/' + str(id) + '.html'):
                continue

            if auto_pause:
                auto_pause = False
                sleep(REQ_THRESHOLD)

            url = BASE_DETAILS_URL + str(id)

            # fetch url
            root_html = fetch(url)
            if isinstance(root_html, int):
                """
                Handle errors / cache failed pages
                """
                errored.append({'id': id, 'status': root_html})
                if root_html == 403:
                    if confirm('\nIt seams that impreva\'s anti-scraping policy blocked us, would you like to pause for 15 sminutes?'):
                        echo('Pausing for 15 minutes')
                        sleep(PAUSE_THRESHOLD)
                    else:
                        auto_pause = True
                sleep(REQ_THRESHOLD)
                continue

            """
            save root_html document (backup)
            we don't care about rewrites at this point (or ever)
            """
            if backup != '':
                with open(backup + '/html/' + str(id) + '.html', 'w') as html_file:
                    html_file.write(root_html)

            """
            pause scraper for REQ_THRESHOLD seconds in order to avoid any 
            scraping blockers like impreva for which we are sure of it!
            """
            sleep(REQ_THRESHOLD)
    """
    Check if we have any blocked pages and re-run the scraper 
    for the given list of ids
    """

    # close output file stream
    # save file
    # f.close()
    """
    Exit the programm
    """
    secho('Done!', fg='green')
    ctx.exit(0)


@cli.command()
@option('-s', '--start', default=970, help='Start from page ID.', show_default=True)
@option('-e', '--end', default=80000, help='End at page ID.', show_default=True)
@option('-l', '--list_of_ids', default=[], show_default=True, help='Comma separeted list of ids.')
@option('-b', '--backup', default='backup', show_default=True, help='Backup files in folder (root folder).')
@option('--verbose', is_flag=False, help='Verbose, print each line.')
def extract(start, end, list_of_ids, backup, verbose):
    """
    Extract command will read all html documents previously fetched from the eauctions.gr website, given a range of IDs,
    and will extract appropriate infrormation with beautifulsoup into an output csv file.
    """

    if len(list_of_ids) > 0:
        list_of_ids = [int(n) for n in list_of_ids.split(',')]
        list_of_ids = list(set(list_of_ids))
    else:
        list_of_ids = []

    length = (end - (start + 1)) if len(list_of_ids) == 0 else len(list_of_ids)

    if length < 0 and len(list_of_ids) == 0:
        secho('Start ID ({0}) is greater than end ID ({1})'.format(
            start, end + 1), fg='red')
        ctx.abort(0)

    """
    Create Directories
    """
    if backup != '':
        if not os.path.exists(backup + '/csv'):
            os.makedirs(backup + '/csv')
        if not os.path.exists(backup + '/files'):
            os.makedirs(backup + '/files')
        if not os.path.exists(backup + '/html'):
            os.makedirs(backup + '/html')

    secho('Extraction Process Started', fg='green')

    f = open(backup + '/csv/' + 'data' + '-' + str(start) + '-' +
             str(end) + '-' + strftime("%Y%m%d-%H%M%S") + '.csv', 'w')
    w = csv.DictWriter(f, [
        'status',
        'date_auction', 'date_online', 'date_published',
        'unique_id', 'price', 'currency', 'property_type', 'property_features',
        'debtors', 'debtor_names', 'debtor_ids', 'debtor_afms', 'debtor_afm_classes',
        'hasteners', 'hastener_names', 'hastener_ids', 'hastener_afms', 'hastener_afm_classes',
        'employee_name', 'employee_address', 'employee_phone', 'employee_email',
        'files', 'file_list', 'auction_id',  # 'notes',
        'url'
    ])
    w.writeheader()

    label = 'Scraping {:,} Document{}'.format(
        length, '' if length == 1 else 's')
    bar_template = '%(label)s %(bar)s | %(info)s'
    fill_char = style(u'█', fg='white')

    with progressbar(
        range(start, end + 1) if len(list_of_ids) == 0 else list_of_ids, label=label,
        width=50, show_pos=True, show_percent=True, info_sep=' ',
        bar_template=bar_template, empty_char='-', fill_char=fill_char
    ) as ids:
        """
        iterate over range of document ids
        """
        for id in ids:
            # if file doesn't exist continue with the next one

            if not os.path.isfile(backup + '/html/' + str(id) + '.html'):
                continue

            # read the file

            html_file = open(backup + '/html/' + str(id) + '.html', 'r')
            html = html_file.read()

            # parse html with bs4

            soup = BeautifulSoup(html, 'lxml')
            soup = soup.find('section', {'id': 'AuctionsDetailsContainer'})

            # extract html dom elements && construct dict

            auction = {
                'status': 'UNK',

                'date_auction': 'UNK',
                'date_online': 'UNK',
                'date_published': 'UNK',

                'unique_id': 'UNK',
                'price': 0.0,
                'currency': 'UNK',
                'property_type': 'UNK',
                'property_features': 'UNK',

                'debtors': [],
                'debtor_names': [],
                'debtor_ids': [],
                'debtor_afms': [],
                'debtor_afm_classes': [],

                'hasteners': [],
                'hastener_names': [],
                'hastener_ids': [],
                'hastener_afms': [],
                'hastener_afm_classes': [],

                'employee_name': 'UNK',
                'employee_address': 'UNK',
                'employee_phone': 'UNK',
                'employee_email': 'UNK',

                'files': [],
                'file_list': [],
                'auction_id': 'UNK',

                'url': ''
                # 'notes': 'UNK'
            }

            # status
            if soup.find('div', text=re.compile('Κατάσταση:')):
                auction['status'] = soup.find(
                    'div', text=re.compile('Κατάσταση:')).findNext('div').text

            # date_auction
            if soup.find('label', text=re.compile('Ημ/νία Διεξαγωγής')):
                auction['date_auction'] = datetime.datetime.strptime(
                    soup.find('label', text=re.compile(
                        'Ημ/νία Διεξαγωγής')).findNext('label').text,
                    '%d/%m/%Y %H:%M'
                ).strftime('%Y-%m-%d %H:%M:%S')

            # date_online
            if soup.find('label', text=re.compile('Ημερομηνία Ανάρτησης')):
                auction['date_online'] = datetime.datetime.strptime(
                    soup.find('label', text=re.compile(
                        'Ημερομηνία Ανάρτησης')).findNext('label').text,
                    '%d/%m/%Y %H:%M:%S'
                ).strftime('%Y-%m-%d %H:%M:%S')

            # date_published
            if soup.find('label', text=re.compile('Ημ/νία Δημοσίευσης')):
                auction['date_published'] = datetime.datetime.strptime(
                    soup.find('label', text=re.compile(
                        'Ημ/νία Δημοσίευσης')).findNext('label').text,
                    '%d/%m/%Y'
                ).strftime('%Y-%m-%d %H:%M:%S')

            # unique_id
            if soup.find('label', text=re.compile('Μοναδικός Κωδικός')):
                auction['unique_id'] = soup.find('label', text=re.compile(
                    'Μοναδικός Κωδικός')).findNext('label').text

            # price
            if soup.find('label', text=re.compile('Τιμή 1ης Προσφοράς')):
                price = Price.fromstring(soup.find('label', text=re.compile(
                    'Τιμή 1ης Προσφοράς')).findNext('label').text)
                auction['price'] = float(price.amount_float)
                auction['currency'] = price.currency

            # property_type
            if soup.find('label', text=re.compile('Είδος προς Πλειστηριασμό')):
                auction['property_type'] = soup.find('label', text=re.compile(
                    'Είδος προς Πλειστηριασμό')).findNext('label').text
                auction['property_type'] = clean_keyword(
                    auction['property_type'])

            # property_features
            if soup.find('label', text=re.compile('Χαρακτηριστικά')):
                auction['property_features'] = soup.find('label', text=re.compile(
                    'Χαρακτηριστικά')).findNext('label').text

            # debtors
            """
            In multiple cases we have multiple debtors per auction, 
            thus we extract both single or multiple in lists.
            """

            # if we find a single debtor
            if soup.find('label', text=re.compile('Ονοματεπώνυμο Οφειλέτη')):
                debtor = {'id': '', 'name': 'UNK',
                          'afm': 'UNK', 'afm_type': 'UNK'}

                debtor['name'] = clean_keyword(soup.find('label', text=re.compile(
                    'Ονοματεπώνυμο Οφειλέτη')).findNext('label').text)
                debtor['id'] = int(
                    soup.find('input', {'id': 'Debtors_0__DebtorID'}).get('value'))

                if soup.find('label', text=re.compile('ΑΦΜ Οφειλέτη')):
                    debtor['afm'] = format_afm(soup.find(
                        'label', text=re.compile('ΑΦΜ Οφειλέτη')).findNext('label').text)
                    debtor['afm_type'] = afm_type(debtor['afm'])

                auction['debtors'] = [debtor]
                auction['debtor_names'] = [debtor['name']]
                auction['debtor_ids'] = [debtor['id']]
                auction['debtor_afms'] = [debtor['afm']]
                auction['debtor_afm_classes'] = [debtor['afm_type']]

            # if we find multiple debtors
            if soup.find('label', text=re.compile('Ονοματεπώνυμα Οφειλετών')):
                parent = soup.find('label', text=re.compile(
                    'Ονοματεπώνυμα Οφειλετών')).parent

                names = [el.text for el in parent.find_all(
                    'label', {'class': 'ADetailsinput3Cell'})]
                afms = [el.text for el in parent.findNext(
                    'div', {'class': 'AuctionDetailsDivR'}).find_all('label', {'class': 'ADetailsinput'})]

                for i, name in enumerate(names):
                    debtor = {
                        'id': int(soup.find('input', {'id': 'Debtors_' + str(i) + '__DebtorID'}).get('value')),
                        'name': clean_keyword(name),
                        'afm': format_afm(clean_keyword(afms[i])),
                        'afm_type': afm_type(afms[i])
                    }
                    auction['debtors'].append(debtor)
                    auction['debtor_names'].append(debtor['name'])
                    auction['debtor_ids'].append(debtor['id'])
                    auction['debtor_afms'].append(debtor['afm'])
                    auction['debtor_afm_classes'].append(debtor['afm_type'])

            # hasteners
            if soup.find('label', text=re.compile('Επισπεύδων')):
                parent = soup.find('label', text=re.compile(
                    'Επισπεύδων')).parent
                names = [el.text for el in parent.find_all(
                    'label', {'class': 'ADetailsinput3Cell'})]

                afms = [el.text for el in parent.findNext(
                    'div', {'class': 'AuctionDetailsDivR'}).find_all('label', {'class': 'ADetailsinput'})]

                for i, name in enumerate(names):
                    hastener = {
                        'id': int(soup.find('input', {'id': 'Hasteners_' + str(i) + '__HastenerID'}).get('value')),
                        'name': clean_keyword(name),
                        'afm': format_afm(clean_keyword(afms[i])),
                        'afm_type': afm_type(afms[i])
                    }
                    auction['hasteners'].append(hastener)
                    auction['hastener_names'].append(hastener['name'])
                    auction['hastener_ids'].append(hastener['id'])
                    auction['hastener_afms'].append(hastener['afm'])
                    auction['hastener_afm_classes'].append(
                        hastener['afm_type'])

            # auction['hasteners'] = soup.find(
            #     'label', text=re.compile('Επισπεύδων')).findNext('label').text
            # auction['hasteners'] = format_hastener(auction['hasteners'])

            # hastener_ids
            # if soup.find('input', {'id': 'Hasteners_0__HastenerID'}):
            #     auction['hastener_ids'] = int(
            #         soup.find('input', {'id': 'Hasteners_0__HastenerID'}).get('value'))

            # hastener_afm
            # if soup.find('label', text=re.compile('ΑΦΜ Επισπεύδοντα')):
            #     auction['hastener_afm'] = format_afm(clean_keyword(soup.find('label', text=re.compile(
            #         'ΑΦΜ Επισπεύδοντα')).findNext('label').text))
            #     auction['hastener_afm_class'] = afm_type(
            #         auction['hastener_afm'])

            # employee_name
            if soup.find('label', text=re.compile('Υπάλληλος Πλειστηριασμού')):
                auction['employee_name'] = soup.find('label', text=re.compile(
                    'Υπάλληλος Πλειστηριασμού')).findNext('div').text
                auction['employee_name'] = clean_keyword(
                    auction['employee_name'])

            # employee_address
            if soup.find('label', text=re.compile('Διεύθυνση')):
                auction['employee_address'] = soup.find(
                    'label', text=re.compile('Διεύθυνση')).findNext('div').text
                auction['employee_address'] = clean_keyword(
                    auction['employee_address'])

            # employee_phone
            if soup.find('label', text=re.compile('Τηλέφωνο')):
                auction['employee_phone'] = soup.find(
                    'label', text=re.compile('Τηλέφωνο')).findNext('div').text
                auction['employee_phone'] = clean_keyword(
                    auction['employee_phone'])

            # employee_email
            if soup.find('label', text=re.compile('Email')):
                auction['employee_email'] = soup.find(
                    'label', text=re.compile('Email')).findNext('div').text
                auction['employee_email'] = clean_keyword(
                    auction['employee_email'])

            # auction_id
            if soup.find('input', {'id': 'auctionId'}):
                auction['auction_id'] = int(
                    soup.find('input', {'id': 'auctionId'}).get('value'))

            # files
            auction['files'] = []

            for el in soup.find_all('a', {'class': 'DownloadAuctionFile'}):
                doc = {
                    'eauctionsFileId': int(el['fileid']),
                    'fileName': el.get_text(),
                    'auction_id': auction['auction_id'],
                    'newFileName': str(el['fileid']) + '.' + el.get_text().split('.')[-1]
                    # 'newFileName': str(auction['auction_id']) + '-' + str(el['fileid']) + '.' + el.get_text().split('.')[-1]
                }
                if not any(d['eauctionsFileId'] == doc['eauctionsFileId'] for d in auction['files']):
                    auction['files'].append(doc)
                    auction['file_list'].append(doc['fileName'])

            # notes
            # if soup.find('label', {'class': 'ADetailsinputNotes'}):
            #     auction['notes'] = soup.find(
            #         'label', {'class': 'ADetailsinputNotes'}).text

            auction['url'] = 'https://www.eauction.gr/Auction/Details/' + \
                str(auction['auction_id'])

            if verbose:
                echo(auction)

            # save line to csv
            w.writerow(auction)

            # save id as last_id in user conf
            pass

    # close output file stream
    f.close()

    """
    Exit tthe programm
    """
    secho('Done!', fg='green')
    ctx.exit(0)


@cli.command()
@argument('input', type=Path(exists=True))
@option('-b', '--backup', default='backup', show_default=True, help='Backup files in folder (root folder).')
@option('--verbose', is_flag=True, default=False, help='Verbose, print each line.')
def download(input, backup, verbose):
    """
    Download command will read an input csv file and fetch the corresponding documents from the eauctions.gr website ($BASE_DOWNLOAD_URL).
    We will need to read the previously generated csv which contains the appropriate information, such as, eauctionsFileId|fileId|newFileName.
    
    UPDATE: Unfortunately, eauctions blocked POST requests outside SAME_ORIGIN, thus we use selenium to download the files in a temp folder.
    """

    """
    Create Directories
    """
    if backup != '':
        if not os.path.exists(backup + '/tmp'):
            os.makedirs(backup + '/tmp')
        if not os.path.exists(backup + '/files'):
            os.makedirs(backup + '/files')

    secho('Preparing Files', fg='green')

    f = pd.read_csv(input)

    errored = []
    auto_pause = False

    options = webdriver.ChromeOptions()
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2, 'javascript': 1
        },
        'download.default_directory': os.path.abspath(backup + '/tmp')
    }
    options.add_argument('--disable-extensions')
    options.add_experimental_option('prefs', prefs)
    options.add_argument('start-maximized')
    options.add_argument('disable-infobars')
    browser = webdriver.Chrome(options=options)
    missing_files = pd.DataFrame(columns=['url', 'auction_id', 'files'])
    for idx, row in f.iterrows():
        for doc in ast.literal_eval(f.iloc[idx].files):
            if os.path.isfile(backup + '/files/' + doc['newFileName']):
                continue
            missing_files = missing_files.append(pd.Series(
                [row.url, row.auction_id, doc], index=missing_files.columns), ignore_index=True)

    missing_files = missing_files.groupby(['auction_id'])
    f = missing_files
        
    secho('Downloading Files', fg='green')
    
    label = 'Downloading ~{} Document{}'.format(
        len(f), '' if len(f) == 1 else 's')
    bar_template = '%(label)s %(bar)s | %(info)s '
    fill_char = style(u'█', fg='white')
    
    with progressbar(
        [i for i, d in f], label=label,
        width=50, show_pos=True, show_percent=True, info_sep=' ',
        bar_template=bar_template, empty_char='-', fill_char=fill_char
    ) as ids:
        skip = False
        for id in ids:
            if verbose:
                secho(' ' + f.get_group(id).url.values[0])
            
            sleep(REQ_THRESHOLD)
            
            try:
                browser.get(f.get_group(id).url.values[0])
            except Exception as e:
                continue
            
            for doc in f.get_group(id).files.values:
                if os.path.isfile(backup + '/files/' + doc['newFileName']):
                    continue
                sleep(REQ_THRESHOLD)
                try:
                    link = browser.find_element_by_link_text(doc['fileName'])
                    if os.path.isfile(backup + '/tmp/' + doc['fileName']):
                        continue
                    link.click()
                except NoSuchElementException as err:
                    secho(' ' + err.msg, fg='red')
                    continue
                    
    """
    Exit the programm
    """
    secho('Done!', fg='green')
    ctx.exit(0)


@cli.command()
def enrich():
    secho('Enrich Process Started', fg='green')

    """
    Exit the programm
    """
    secho('Done!', fg='green')
    ctx.exit(0)


@cli.command()
def save():
    secho('Saving Documents', fg='green')

    """
    Exit the programm
    """
    secho('Done!', fg='green')
    ctx.exit(0)


if __name__ == '__main__':
    cli()
