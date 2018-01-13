Grabs info on cryptocurrencies from coinmarketcap and keeps real-time information updated on google sheets.

To get started:
* Follow steps 1 and 2 (https://developers.google.com/sheets/api/quickstart/python)
* Rest of the packages should be in anaconda for python 3.6
* Update globals in header of python file (clientsecret json file, CA certificate file, spreadsheet ID
* Add coins to track in 'coins' list in first line of main()
* 'use_cases' and 'scams' lists should be subsets of 'coins' list
* Set update interval (currently updates every 10 seconds)
