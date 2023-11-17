#!/usr/bin/env python3

#### 0 - HEADER #####
try:
	import ccxt #pip3 install ccxt
except:
	print("[ERROR 91] CCXT not found: pip3 install ccxt")
	exit(1)

try:
	import pyfiglet #pip3 install pyfiglet
except:
	print("[ERROR 92] pyfiglet not found: pip3 install pyfiglet")
	exit(1)

from datetime import datetime
import signal
import time
#### FIN DU HEADER #####

#### FUNNY DISPLAY INTO ####
result = pyfiglet.figlet_format("FunkyBOT")
print(result)
###########################

#### 1 - PARAMS ####
# Initalisation des diverses variables globales du script.
print("[+] PARAMS")
API_KEY = 'API KEY ID string'
API_SECRET = 'API KEY SECRET password'
EX_BINANCE = ccxt.binance({ # Initialiser l'exchange Binance - En mode testnet
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})
EX_BINANCE.set_sandbox_mode(True) #important pour le mode sandbox
#ci-dessous, les parametres généraux de trading du BOT
SRC_SYMBOL = "USDT" # la devise source
DST_SYMBOL = "BTC" # la devise à trader
SYMBOL = DST_SYMBOL + SRC_SYMBOL # symbole
SYMBOL_SLASH = DST_SYMBOL + "/" + SRC_SYMBOL #symbole formaté avec un slash
TRADING_QTY = 0.003  # Quantité unitaire à trader (par trade)
TRADING_MAX = 10 # Nombe maximum de trades autorisés.
SLEEP_TIME_SEC = 120 # nombre de secondes entre chaque itération
#ci-dessous, des variables pour coloriser le texte (couleur)
C_RED = '\033[1;31;40m'
C_GREEN = '\033[1;32;40m'
C_BLUE = '\033[1;34;40m'
C_NORMAL ='\033[0;0;0m'
#### FIN DU PARAMS #####

#### 2 - FONCTIONS ####
print("[+] FONCTIONS")
# Fonction pour placer un ordre d'achat
def testfunc (exchange):
	wallet_update = exchange.fetch_balance()
	print("TST :"+ str(wallet_update['BTC']))
	print("TST :"+ str(wallet_update['BTC']['total']))

def wallet_status(exchange, symbol, param = "full"):
	#param may be one of the following: full, total, free, used. Default is full
	#full return a string type
	#others return a float type
	wallet_update = exchange.fetch_balance()
	if param == "full":
		output = wallet_update[symbol]
	elif param in ('total', 'free','used'):
		output = wallet_update[symbol][param]
	else:
		print("[ERROR 101] - Bad param")
		return "NaN"
	return output

def get_pair_average_price(exchange, symbol_slash):
	#fonction pour obtenir le prix moyen d'une paire
	return exchange.fetch_ticker(symbol_slash)['average']

def place_buy_order(exchange, symbol, quantity, ordertype = "market"):
	order = "NaN"
	if ordertype == "market":
		order = exchange.create_market_buy_order(symbol, quantity)
		orderinfo = exchange.fetch_order(id=order['id'],symbol=symbol)
		order_amount = orderinfo['amount']
		order_cost = orderinfo['cost']
		order_fees_cost = orderinfo['fees'][0]['cost']
		order_fees_currency = orderinfo['fees'][0]['currency']
		print("  [ACHAT] [" + str(orderinfo['amount']) + " " + DST_SYMBOL + "] [PRICE: " + str(order_cost) + " " + str(SRC_SYMBOL) + "] [FEES: "+str(order_fees_cost) + " " + str(order_fees_currency) + "] [ID: " + str(order['id']) + "]")
	else:
		print("[ERROR 102] - unsupported type")
		return "NaN"
	#print("  [ACHAT] [" + str(quantity) + " " + symbol + "] [ID: " + str(order['id']) + "]")
	return order['id']

# Fonction pour placer un ordre de vente
def place_sell_order(exchange, symbol, quantity, ordertype = "market"):
	order = "NaN"
	if ordertype == "market":
		order = exchange.create_market_sell_order(symbol, quantity)
		orderinfo = exchange.fetch_order(id=order['id'],symbol=symbol)
		order_amount = orderinfo['amount']
		order_cost = orderinfo['cost']
		order_fees_cost = orderinfo['fees'][0]['cost']
		order_fees_currency = orderinfo['fees'][0]['currency']
		print("  [VENTE] [" + str(orderinfo['amount']) + " " + DST_SYMBOL + "] [PRICE: " + str(order_cost) + " " + str(SRC_SYMBOL) + "] [FEES: "+str(order_fees_cost) + " " + str(order_fees_currency) + "] [ID: " + str(order['id']) + "]")
	else:
		print("[ERROR 103] - unsupported type")
		return "NaN"
	#print("  [VENTE] [" + str(quantity) + " " + symbol + "] [ID: " + str(order['id']) + "]")
	return order['id']

# Fonction pour obtenir les données du marché
# L'historique des données obtenues est de timestamp * limit.
# Par défaut: 1mn * 15 = 15mn d'historique.
def get_market_data(exchange, symbol, trigger="close",frame="1m",limit=15):
	#OHLCV format
	#[0] UTC timestamp in milliseconds, integer
	#[1] (O)pen price, float
	#[2] (H)ighest price, float
	#[3] (L)owest price, float
        #[4] (C)losing price, float
        #[5] (V)olume (in terms of the base currency), float
	triggerNUM = 4
	if trigger == "open":
		triggerNUM = 1
	elif trigger == "high":
		triggerNUM = 2
	elif trigger == "low":
		triggerNUM = 3
	elif trigger == "close":
		triggerNUM = 4
	else:
		print("[ERROR 105] - unsupported trigger")
		return "NaN"
	ohlcv = exchange.fetch_ohlcv(symbol, timeframe=frame, limit=limit)
	final_array = []
	for x in ohlcv:
		data_tmstmp = int(str(x[0])[:-3])
		data_array = [data_tmstmp,x[triggerNUM]]
		#dt_object = datetime.fromtimestamp(data_tmstmp)
		#print("dt_object =", dt_object)
		#print(data_array)
		final_array.append(data_array)
	return final_array

def calculate_rsi(exchange, symbol,trigger="close",frame="1m",limit=15):
	data = get_market_data(exchange, symbol, trigger, frame, limit) #GET OHLCV data

	deltas = [data[i][1] - data[i-1][1] for i in range(1, len(data))]
	gain = [deltas[i] if deltas[i] > 0 else 0 for i in range(len(deltas))]
	loss = [abs(deltas[i]) if deltas[i] < 0 else 0 for i in range(len(deltas))]

	avg_gain = sum(gain) / len(data)
	avg_loss = sum(loss) / len(data)

	rsi = None  #variable initialization

	for i in range(len(data)-1):
		avg_gain = (avg_gain * (len(data) - 1) + gain[i]) / len(data)
		avg_loss = (avg_loss * (len(data) - 1) + loss[i]) / len(data)
		rs = avg_gain / avg_loss
		rsi = 100 - (100 / (1 + rs))

	rsi = float("{:.2f}".format(rsi))
	return rsi

def TERMINATE_handler(signum, frame):
	print("[CTRL+C] EXIT signal ... Selling remaining orders then EXIT...pease wait")
	for ordercpt in range(ORDERS_NBR):
		place_sell_order(EX_BINANCE, SYMBOL, TRADING_QTY, "market")
	print("[GOODBYE] Copyright: FunkyBot")
	exit(1)
#### FIN DU FONCTIONS #####


#### 3 - CONFIG ####
print("[+] CONFIG")
print("  [-] La devise refuge est le " + C_GREEN + SRC_SYMBOL + C_NORMAL)
print("  [-] La devise à commercer st le " + C_GREEN + DST_SYMBOL + C_NORMAL)
print("  [-] L'objectif est donc de gagner des " + C_GREEN + SRC_SYMBOL + C_NORMAL + " en commercant le symbole " + C_GREEN + SYMBOL + C_NORMAL + " ( " + C_GREEN + SYMBOL_SLASH + C_NORMAL + " )")
print("  [-] La fréquence d'analyse est de " + C_GREEN + str(SLEEP_TIME_SEC) + " secondes" + C_NORMAL)
MY_INITIAL_SRC_QTY = float("{:.2f}".format(wallet_status(EX_BINANCE, SRC_SYMBOL, "free")))
print("  [-] La quantité initiale est de " + C_GREEN + str(MY_INITIAL_SRC_QTY) + " " + SRC_SYMBOL +C_NORMAL)
AVG_PRICE = get_pair_average_price(EX_BINANCE, SYMBOL_SLASH)
TRADING_PRICE = float("{:.2f}".format(TRADING_QTY * AVG_PRICE))
print("  [-] Les ordres sont de " + C_GREEN + str(TRADING_QTY) + " " + DST_SYMBOL + C_NORMAL + " ( environ " + C_GREEN + str(TRADING_PRICE) + " " + SRC_SYMBOL + C_NORMAL + " )")
MAX_EXPOSURE = float("{:.2f}".format(TRADING_MAX * TRADING_PRICE))
print("  [-] " + C_GREEN + str(TRADING_MAX) + C_NORMAL + " ordres sont cumulables pour une exposition maximum de " + C_GREEN + str(MAX_EXPOSURE) + " " + SRC_SYMBOL + C_NORMAL)
ALLOWED_EXPOSURE = MY_INITIAL_SRC_QTY * 70/100
if MAX_EXPOSURE > ALLOWED_EXPOSURE:
	print("[ERROR 104] "+ C_RED + "CONFIG KO" + C_NORMAL + " L'exposition maximum ne doit pas dépasser 70% de ma quantité initiale.")
	exit(1)
else:
	print("  [-] " + C_GREEN + "CONFIG: OK" + C_NORMAL)
#### FIN DU CONFIG #####

#### 3 - INIT ####
print("[+] INIT")
signal.signal(signal.SIGINT, TERMINATE_handler) #fonction pour terminer le BOT lorsque CTRL+C

ORDERS_NBR=0
while True:
	#STEP1 - on affiche la date/heure au format -  dd/mm/YY H:M:S
	now = datetime.now()
	DT_STR = now.strftime("%d/%m/%Y %H:%M:%S")

	#STEP2 - on calcule le RSI
	RSI_VAL = calculate_rsi(EX_BINANCE,SYMBOL,limit=60)

	#STEP3 - SIGNAL par rapport au RSI
	SIGNAL="WAIT"
	if ORDERS_NBR < TRADING_MAX and RSI_VAL <= 30: #si on a pas ateint le MAX d'ordres en cours
		SIGNAL="BUY"
	elif ORDERS_NBR > 0 and RSI_VAL >= 70:
		SIGNAL="SELL"

	#STEP4 - PERFORM ACTION
	if SIGNAL == "BUY":
		orderid = place_buy_order(EX_BINANCE, SYMBOL, TRADING_QTY, "market")
		#orderinfo = EX_BINANCE.fetch_order(id=orderid,symbol=SYMBOL)
		#order_cost = orderinfo['cost']
		#order_fees_cost = orderinfo['fees'][0]['cost']
		#order_fees_currency = orderinfo['fees'][0]['currency']
		ORDERS_NBR += 1
	elif SIGNAL == "SELL":
		for sell_cpt in range(ORDERS_NBR):
			orderid = place_sell_order(EX_BINANCE, SYMBOL, TRADING_QTY, "market")
			#orderinfo = EX_BINANCE.fetch_order(id=orderid,symbol=SYMBOL)
			#order_amount = orderinfo['amount']
			#order_cost = orderinfo['cost']
			#order_fees_cost = orderinfo['fees'][0]['cost']
			#order_fees_currency = orderinfo['fees'][0]['currency']
		ORDERS_NBR = 0

	#STEP5 - quantité actuelle de SRC_SYMBOL
	MY_SRC_QTY = float("{:.2f}".format(wallet_status(EX_BINANCE, SRC_SYMBOL, "free")))

	#STEP 6 - AFFICHAGE DES INFOS
	print("[" + DT_STR + "]",end="")
	print(" [RSI: " + str(RSI_VAL)+"]",end="")
	print(" [ORDRES: "+str(ORDERS_NBR)+"/"+str(TRADING_MAX)+"]",end="")
	print(" ["+SRC_SYMBOL+": "+str(MY_SRC_QTY)+"]")

	time.sleep(SLEEP_TIME_SEC)

#testfunc(EX_BINANCE)
#print("USDT: "+str(wallet_status(EX_BINANCE,"USDT")))
#print("BTC: "+str(wallet_status(EX_BINANCE,"BTC")))

#place_sell_order(EX_BINANCE,symbol, quantity, "market")

#print("USDT: "+str(wallet_status(EX_BINANCE,"USDT")))
#print("BTC: "+str(wallet_status(EX_BINANCE,"BTC")))

# Récupérer le ticker pour la paire BTC/USDT
#ticker = EX_BINANCE.fetch_ticker('BTC/USDT')
#print(ticker)
#print("AV: " + str(ticker['average']))
