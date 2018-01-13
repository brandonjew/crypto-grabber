import ast
import os
import sys
import urllib.request
import httplib2

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from time import sleep

INTERVAL = 10

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = "client_secret.json" #Update to your json path
CA_FILE = "cacert.pem" # Update to cacert.pem path in certifi package
SPREADSHEET_ID = 'abcdefghijklmnopqrstuvwxyz1234567890' #Spreadsheet ID from URL
APPLICATION_NAME = 'crypto_tracker'

try:
  import argparse
  flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
  flags = None

class Cryptocoins(object):
  """Stores info for all coins"""
  def __init__(self, coins, use_cases, scams):
    self.rows = [
                 "Cryptocurrency", "USD", "MC (L=B)", "CS", "TS", "%TS (L=B)",
                 "MS (Max Supply)", "UC (Usecase)", "Scam"
                ]
    self.data = []
    for coin in coins:
      info = grab_crypto(coin)
      header = "{} ({})".format(info["symbol"], info["name"])
      usd = info["price_usd"]
      mc = info["market_cap_usd"]
      cs = info["available_supply"]
      ts = info["total_supply"]
      percent_ts = str(float(cs)/float(ts))
      ms = info["max_supply"]
      uc = ""
      scam = ""
      if coin in use_cases:
        uc = "Yes"
      if coin in scams:
        scam = "Yes"
      self.data.append({
                   "Cryptocurrency": header, "USD": usd, "MC (L=B)": mc,
                   "CS": cs, "TS": ts, "%TS (L=B)": percent_ts,
                   "MS (Max Supply)": ms, "UC (Usecase)": uc, "Scam": scam
                  })

  def sort_by(self, row_title):
    """Sorts list of coins by decreasing numerical entries for row_title"""
    self.data.sort(key=lambda x: float(x[row_title]))
    self.data = self.data[::-1]

  def add_ranking(self, row_title):
    """Determines rank given row and adds entry for it"""
    rank_title = "{} Ranking".format(row_title)
    self.rows.append(rank_title)
    self.sort_by(row_title)
    rank = 1
    last_val = None
    for index, coin in enumerate(self.data):
      curr_val = float(coin[row_title])
      if last_val != None:
        if curr_val != last_val:
          rank += 1
      last_val = curr_val
      self.data[index][rank_title] = rank
  
  def add_average_rankings(self):
    """Averages rankings for each coin and adds row"""
    row_title = "Average Ranking"
    add_row = False
    for index, coin in enumerate(self.data):
      ranks = 0
      sum_ranks = 0
      for row in coin.keys():
        if row.find("Ranking") != -1:
          ranks += 1
          sum_ranks += coin[row]
      if ranks != 0:
        add_row = True
        avg_rank = sum_ranks/ranks
        self.data[index][row_title] = avg_rank
    if add_row:
      self.rows.append(row_title)

  def add_score(self, row_val_points):
    """Adds points to score if entry in row equals val
    Args:
      row_val_points: List of 3 member tuples
        (e.g. For (1, "test", 3), if entry in row 1 equals "test", add 3points)
    """
    row_title = "Score"
    for index,coin in enumerate(self.data):
      score = coin["Average Ranking"]
      for row, val, point in row_val_points:
        if coin[row] == val:
          score += points
      self.data[index][row_title] = score
    self.rows.append(row_title)

  def arbitrary_method(self):
    """Arbitrary method for sorting currencies"""
    self.add_ranking("MC (L=B)")
    self.add_ranking("%TS (L=B)")
    self.add_ranking("USD")
    self.add_average_rankings()
    self.add_score([("UC (Usecase)", "yes", 1),
                    ("MS (Max Supply)", "null", -1)
                   ])
    self.sort_by("Average Ranking")
        
  def prepare_values(self):
    """Returns range and body for google api update"""
    col_coord = chr(len(self.data) + 65) #ASCII value of A is 65
    row_coord = len(self.rows)
    range_name = "A1:{}{}".format(col_coord,row_coord)
    values = []
    for row, row_title in enumerate(self.rows):
      values.append([row_title])
      for item in self.data:
        values[row].append(item[row_title])
    body = {"values": values}
    return range_name, body

def get_credentials():
  """Gets valid user credentials from storage.

  If nothing has been stored, or if the stored credentials are invalid,
  the OAuth2 flow is completed to obtain the new credentials.

  Returns:
      Credentials, the obtained credential.
  """
  home_dir = os.path.expanduser('~')
  credential_dir = os.path.join(home_dir, '.credentials')
  if not os.path.exists(credential_dir):
    os.makedirs(credential_dir)
  credential_path = os.path.join(credential_dir,
                                 'sheets.googleapis.com-python-quickstart.json')
  store = Storage(credential_path)
  credentials = store.get()
  if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    flow.user_agent = APPLICATION_NAME
    if flags:
      credentials = tools.run_flow(flow, store, flags)
    else: # Needed only for compatibility with Python 2.6
      credentials = tools.run(flow, store)
    print('Storing credentials to ' + credential_path)
  return credentials

def grab_crypto(crypto):
  """Parses json file for supplied cryptocurrency
  
  Args:
    crypto: String with currency id 
  Returns:
    info: Dictionary of JSON for currency
  """
  url = "https://api.coinmarketcap.com/v1/ticker/{}/".format(crypto)


  ca_file = CA_FILE.encode('utf-8')
  info = {}
  try:
    with urllib.request.urlopen(url, cafile=ca_file) as html:
      # Beautiful string manipulation and eval
      info = ast.literal_eval(html.read().decode('utf-8').replace(" null,", "\"null\",").strip("[]").replace('\n', '').replace('\r', '').replace(' ', ''))
  except urllib.error.HTTPError:
    raise Exception("cryptocurrency ({}) not found".format(crypto))
  return info

def main():
  coins = ["vechain", "poet", "request-network",
           "stellar", "time-new-bank", "coindash",
           "enjin-coin", "bitcoin", "ethereum"]

  use_cases = []
  scams = []

  use_cases = set(use_cases)
  scams = set(scams)
  credentials = get_credentials()
  http = credentials.authorize(httplib2.Http())
  discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                  'version=v4')
  service = discovery.build('sheets', 'v4', http=http,
                            discoveryServiceUrl=discoveryUrl)
  value_input_option="USER_ENTERED"
  while(True):
    values = Cryptocoins(coins, use_cases, scams)
    values.arbitrary_method()
    range_name, body = values.prepare_values()
    result = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=range_name, valueInputOption=value_input_option, body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))
    sleep(INTERVAL)

if __name__ == "__main__":
  main()
