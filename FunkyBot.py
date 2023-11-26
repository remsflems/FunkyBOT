#!/usr/bin/env python3

#### 0 - HEADER #####
from sys import exit
from datetime import datetime
import signal
import time
import threading
import csv
import os

try:
	import matplotlib
	import matplotlib.pyplot as plt #pip3 install ccxt
except:
	print("[ERROR 90] matplotlib not found: pip3 install matplotlib")
	exit(1)
	
try:
	matplotlib.use('tkagg') #apt-get install python3-tk
except:
	print("[ERROR 93] tkinter not found: apt-get install python3-tk")
	print("		or pip3 install tk")
	print("[ERROR 94] PIL & imageTK not found: apt-get install python3-pil.imagetk")
	print("		or pip3 install Pillow")
	exit(1)
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

#### FIN DU HEADER #####

#### FUNNY DISPLAY INTO ####
result = pyfiglet.figlet_format("FunkyBOT")
print(result)
###########################

#### 0 - PRE-ACTIONS ####
#On créé le fichier CSV
# Check if the file exists
CSV_FILE = "asset_data.csv"
if os.path.exists(CSV_FILE):
	# Remove the file if it exists
	os.remove(CSV_FILE)
    
# Create the CSV file
header = ['datetime','rsi','btc_price_in_usdt','wallet_qty']
with open(CSV_FILE, 'w', newline='') as file:
	writer = csv.writer(file) #set a writer handler
	writer.writerow(header) # write the header
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
EX_BINANCE.feeTiers = True  # Enable fee tiers

#ci-dessous, les parametres généraux de trading du BOT
SRC_SYMBOL = "USDT" # la devise source
DST_SYMBOL = "BTC" # la devise à trader
SYMBOL = DST_SYMBOL + SRC_SYMBOL # symbole
SYMBOL_SLASH = DST_SYMBOL + "/" + SRC_SYMBOL #symbole formaté avec un slash
TRADING_QTY = 0.003  # Quantité unitaire à trader (par trade)
TRADING_MAX = 10 # Nombe maximum de trades autorisés.
RSI_PERIOD = 30 # l'historique (en minutes) pour le calcul du RSI
SLEEP_TIME_SEC = 60 # nombre de secondes entre chaque itération
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
		print(" [" + C_BLUE + "ACHAT" + C_NORMAL + "] [" + str(orderinfo['amount']) + " " + DST_SYMBOL + "] [PRICE: " + str(order_cost) + " " + str(SRC_SYMBOL) + "] [FEES: "+str(order_fees_cost) + " " + str(order_fees_currency) + "] [ID: " + str(order['id']) + "]")
	elif ordertype == "limit":
		order = exchange.create_limit_buy_order(symbol, quantity, get_pair_average_price(exchange, SYMBOL) + 0.05)
		orderinfo = exchange.fetch_order(id=order['id'], symbol=symbol)
		order_amount = orderinfo['amount']
		order_cost = orderinfo['cost']
		order_fees_cost = orderinfo['fees'][0]['cost']
		order_fees_currency = orderinfo['fees'][0]['currency']
		print("  [ACHAT] [" + str(orderinfo['amount']) + " " + DST_SYMBOL + "] [PRICE: " + str(order_cost) + " " + str(SRC_SYMBOL) + "] [FEES: " + str(order_fees_cost) + " " + str(order_fees_currency) + "] [ID: " + str(order['id']) + "]")
	else:
		print("[ERROR 102] - unsupported type")
		return "NaN"
	#print("  [ACHAT] [" + str(quantity) + " " + symbol + "] [ID: " + str(order['id']) + "]")
	return order['id']

# Fonction pour placer un ordre de vente
def place_sell_order(exchange, symbol, quantity, ordertype = "market", nonewline=False):
	order = "NaN"
	if ordertype == "market":
		order = exchange.create_market_sell_order(symbol, quantity)
		orderinfo = exchange.fetch_order(id=order['id'],symbol=symbol)
		order_amount = orderinfo['amount']
		order_cost = orderinfo['cost']
		order_fees_cost = orderinfo['fees'][0]['cost']
		order_fees_currency = orderinfo['fees'][0]['currency']
		if nonewline:
			print(" [" + C_BLUE + "VENTE" + C_NORMAL + "] [" + str(orderinfo['amount']) + " " + DST_SYMBOL + "] [PRICE: " + str(order_cost) + " " + str(SRC_SYMBOL) + "] [FEES: "+str(order_fees_cost) + " " + str(order_fees_currency) + "] [ID: " + str(order['id']) + "]",end="")
		else:
			print(" [" + C_BLUE + "VENTE" + C_NORMAL + "] [" + str(orderinfo['amount']) + " " + DST_SYMBOL + "] [PRICE: " + str(order_cost) + " " + str(SRC_SYMBOL) + "] [FEES: "+str(order_fees_cost) + " " + str(order_fees_currency) + "] [ID: " + str(order['id']) + "]")
	elif ordertype == "limit":
		order = exchange.create_limit_sell_order(symbol, quantity, get_pair_average_price(exchange, SYMBOL)-0.05)
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
def get_market_data(exchange, symbol, trigger="close",frame="1m",limit=RSI_PERIOD):
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

#La fonction calculate_rsi opère le calcul du RSI basé sur les données du marché récoltées.
#Elle calcule donc le RSI à parti de la fonction get_market_data
def calculate_rsi(exchange, symbol,trigger="close",frame="1m",limit=RSI_PERIOD):
	data = get_market_data(exchange, symbol, trigger, frame, limit) #GET OHLCV data
	#print(data)
	deltas = [data[i][1] - data[i-1][1] for i in range(1, len(data))]
	gain = [deltas[i] if deltas[i] > 0 else 0 for i in range(len(deltas))]
	loss = [abs(deltas[i]) if deltas[i] < 0 else 0 for i in range(len(deltas))]
	avg_gain = sum(gain) / len(data)
	avg_loss = sum(loss) / len(data)
	rsi = None  #variable initialization

	if avg_loss == 0: #FAILSAFE EN SITUATION CRITIQUE
		avg_loss = 0.00001
	
	for i in range(len(data)-1):
		avg_gain = (avg_gain * (len(data) - 1) + gain[i]) / len(data)
		avg_loss = (avg_loss * (len(data) - 1) + loss[i]) / len(data)
		
		if avg_loss == 0: #FAILSAFE EN SITUATION CRITIQUE
			avg_loss = 0.00001

		rs = avg_gain / avg_loss
		rsi = 100 - (100 / (1 + rs))

	rsi = float("{:.2f}".format(rsi))
	return rsi

# La fonction TEMINATE_handler sera executée lorsque l'on arrête le BOT (après un CTRL+C)
# Son objectif sera de vendre tous les ordres en cours.
def TERMINATE_handler(signum, frame):
	print("[CTRL+C] EXIT signal ... Selling remaining orders then EXIT...pease wait")
	for sell_cpt in range(ORDERS_NBR):
		orderid = place_sell_order(EX_BINANCE, SYMBOL, TRADING_QTY, "market",nonewline=True)
		sell_orderinfo = EX_BINANCE.fetch_order(id=orderid,symbol=SYMBOL)
		sell_order_amount = sell_orderinfo['amount']
		sell_order_cost = sell_orderinfo['cost']
		sell_order_fees_cost = sell_orderinfo['fees'][0]['cost']
		sell_order_fees_currency = sell_orderinfo['fees'][0]['currency']
		print(" [BUYED AT: " + str(ORDERS_LIST[sell_cpt][1]) + "] ",end="")
		if sell_order_cost > ORDERS_LIST[sell_cpt][1]:
			print("--> " + C_GREEN + "GOOD TRADE" + C_NORMAL)
		elif  sell_order_cost < ORDERS_LIST[sell_cpt][1]:
			print("--> " + C_RED + "BAD TRADE" + C_NORMAL)
		else:
			print(" ")
	print("[GOODBYE] Copyright: FunkyBot")
	exit(1)
	
# Define your two tasks as functions
def SLEEPING():
	time.sleep(SLEEP_TIME_SEC)

#### FIN DU FONCTIONS #####


#### 3 - CONFIG ####
try:
	print("[+] CONFIG")
	print("  [-] La devise refuge est le " + C_GREEN + SRC_SYMBOL + C_NORMAL)
	print("  [-] La devise à commercer est le " + C_GREEN + DST_SYMBOL + C_NORMAL)
	print("  [-] L'objectif est donc de gagner des " + C_GREEN + SRC_SYMBOL + C_NORMAL + " en commercant le symbole " + C_GREEN + SYMBOL + C_NORMAL + " ( " + C_GREEN + SYMBOL_SLASH + C_NORMAL + " )")
	print("  [-] La fréquence d'analyse est de " + C_GREEN + str(SLEEP_TIME_SEC) + " secondes" + C_NORMAL)
	MY_INITIAL_SRC_QTY = float("{:.2f}".format(wallet_status(EX_BINANCE, SRC_SYMBOL, "free")))
	VALUE_AFTER_SELL = MY_INITIAL_SRC_QTY
	print("  [-] La quantité initiale est de " + C_GREEN + str(MY_INITIAL_SRC_QTY) + " " + SRC_SYMBOL +C_NORMAL)
	AVG_PRICE = get_pair_average_price(EX_BINANCE, SYMBOL_SLASH)
	TRADING_PRICE = float("{:.2f}".format(TRADING_QTY * AVG_PRICE))
	print("  [-] Les ordres sont de " + C_GREEN + str(TRADING_QTY) + " " + DST_SYMBOL + C_NORMAL + " ( environ " + C_GREEN + str(TRADING_PRICE) + " " + SRC_SYMBOL + C_NORMAL + " )")
	MAX_EXPOSURE = float("{:.2f}".format(TRADING_MAX * TRADING_PRICE))
	print("  [-] " + C_GREEN + str(TRADING_MAX) + C_NORMAL + " ordres sont cumulables pour une exposition maximum de " + C_GREEN + str(MAX_EXPOSURE) + " " + SRC_SYMBOL + C_NORMAL)
	print("  [-] La periode de calcul du RSI est de " + C_GREEN + str(RSI_PERIOD) + C_NORMAL + " minutes")
	ALLOWED_EXPOSURE = MY_INITIAL_SRC_QTY * 70/100
	if MAX_EXPOSURE > ALLOWED_EXPOSURE:
		print("[ERROR 104] "+ C_RED + "CONFIG KO" + C_NORMAL + " L'exposition maximum ne doit pas dépasser 70% de ma quantité initiale.")
		exit(1)
	else:
		print("  [-] " + C_GREEN + "CONFIG: OK" + C_NORMAL)
except Exception as ex:
	print("[ERROR 106] "+ C_RED + "CONFIG KO" + C_NORMAL + " Something went wrong! Exchange unreachable (network)?")
	print(ex)
	exit(1)
#### FIN DU CONFIG #####

#### 3 - INIT ####
print("[+] INIT")
signal.signal(signal.SIGINT, TERMINATE_handler) #fonction pour terminer le BOT lorsque CTRL+C

ORDERS_NBR=0
ORDERS_LIST=[]
RSI_PREV=50
RSI_PREV_PREV=50


#GRAPHIC GUI - SETUP
plt.ion()
fig,ax = plt.subplots(figsize=(12, 8))
ax.set_xlabel("dates", fontsize = 14) # set x-axis label 
ax.set_ylabel("RSI", color="red", fontsize=10) # set y-axis label
ax.yaxis.label.set_color('red')
ax.tick_params(axis='y', colors='red') 
ax2=ax.twinx() # twin object for two different y-axis on the sample plot
ax2.set_ylabel(SYMBOL_SLASH+" price",color="blue",fontsize=10)
ax2.tick_params(axis='y', colors='blue') 
ax3=ax2.twinx() # twin object for two different y-axis on the sample plot
ax3.set_ylabel("Wallet",color="green",fontsize=10)
ax3.tick_params(axis='y', colors='green')
	
while True:
	#STEP 0: definir le thead pour patienter. Pou chaque tour. (30 sec minimum pour eviter les bugs)
	thread1 = threading.Thread(target=SLEEPING)
	thread1.start()
	
	#STEP1 - on affiche la date/heure au format -  dd/mm/YY H:M:S
	now = datetime.now()
	DT_STR = now.strftime("%d/%m/%Y %H:%M:%S")
	try:
		#STEP2 - on calcule le RSI
		RSI_VAL = calculate_rsi(EX_BINANCE,SYMBOL,limit=RSI_PERIOD)
		SYMBOL_AVG_PRICE = float("{:.2f}".format(get_pair_average_price(EX_BINANCE, SYMBOL_SLASH)))

		#STEP3 - SIGNAL par rapport au RSI
		SIGNAL="WAIT"
		"""
		if ORDERS_NBR < TRADING_MAX and RSI_VAL < 30: #si on a pas ateint le MAX d'ordres en cours
			if RSI_PREV < 30 and RSI_VAL > RSI_PREV:
				if RSI_PREV_PREV < 30 and RSI_PREV < RSI_PREV_PREV:
					SIGNAL="BUY"
		elif ORDERS_NBR > 0 and RSI_VAL > 70:
			SIGNAL="SELL"
		"""

		#Si on a pas ateint le MAX d'ordres en cours. Si RS_VAL et RSI_PREV < 30 et RSI_VAL est inferieur à RSI_PREV
		if ORDERS_NBR < TRADING_MAX and RSI_VAL < 30 and RSI_PREV < 30 and RSI_VAL <= RSI_PREV :
			SIGNAL="BUY"
		#Si il y a des ordre en cours. et que RSI_VAL est > 60 , et RSI_PREV et RSI_PREV_PREV > 70
		elif ORDERS_NBR > 0 and RSI_VAL > 60 and RSI_PREV > 70 and RSI_PREV_PREV > 70 :
			SIGNAL="SELL"
		
		#STEP 2 BIS - Update valeurs precedentes pour mémoriser les RSI des boucles précédente et boucle -2.
		RSI_PREV_PREV = RSI_PREV
		RSI_PREV = RSI_VAL

		#STEP4 - PERFORM ACTION
		if SIGNAL == "BUY":
			print("[" + DT_STR + "]",end="") #affichage de la date & time
			print(" [RSI: " + str(RSI_VAL).rjust(5," ")+"]",end="")
			orderid = place_buy_order(EX_BINANCE, SYMBOL, TRADING_QTY, "market")
			orderinfo = EX_BINANCE.fetch_order(id=orderid,symbol=SYMBOL)
			order_cost = orderinfo['cost']
			order_fees_cost = orderinfo['fees'][0]['cost']
			order_fees_currency = orderinfo['fees'][0]['currency']
			ORDERS_LIST.append([orderid,order_cost,order_fees_cost,order_fees_currency])
			ORDERS_NBR += 1
		elif SIGNAL == "SELL":
			for sell_cpt in range(ORDERS_NBR):
				print("[" + DT_STR + "]",end="") #affichage de la date & time
				print(" [RSI: " + str(RSI_VAL).rjust(5," ")+"]",end="")
				orderid = place_sell_order(EX_BINANCE, SYMBOL, TRADING_QTY, "market",nonewline=True)
				sell_orderinfo = EX_BINANCE.fetch_order(id=orderid,symbol=SYMBOL)
				sell_order_amount = sell_orderinfo['amount']
				sell_order_cost = sell_orderinfo['cost']
				sell_order_fees_cost = sell_orderinfo['fees'][0]['cost']
				sell_order_fees_currency = sell_orderinfo['fees'][0]['currency']
				print(" [BUYED AT: " + str(ORDERS_LIST[sell_cpt][1]) + "] ",end="")
				if sell_order_cost > ORDERS_LIST[sell_cpt][1]:
					print("--> " + C_GREEN + "GOOD TRADE" + C_NORMAL)
				elif  sell_order_cost < ORDERS_LIST[sell_cpt][1]:
					print("--> " + C_RED + "BAD TRADE" + C_NORMAL)
				else:
					print(" ")
			ORDERS_NBR = 0
			VALUE_AFTER_SELL = float("{:.2f}".format(wallet_status(EX_BINANCE, SRC_SYMBOL, "free")))

		#STEP 5 Affichage général du status du wallet
		#STEP1 - on affiche la date/heure au format -  dd/mm/YY H:M:S
		now = datetime.now()
		DT_STR = now.strftime("%d/%m/%Y %H:%M:%S")


		print("[" + DT_STR + "]",end="") #affichage de la date & time

		#STEP5 - quantité actuelle de SRC_SYMBOL
		MY_SRC_QTY = float("{:.2f}".format(wallet_status(EX_BINANCE, SRC_SYMBOL, "free")))

		#STEP 6 - AFFICHAGE DES INFOS
		print(" [RSI: " + str(RSI_VAL).rjust(5," ")+"]",end="")
		print(" [ORDRES: "+str(ORDERS_NBR)+"/"+str(TRADING_MAX)+"]",end="")
		print(" ["+SRC_SYMBOL+": "+str(MY_SRC_QTY)+"]",end="")
		val_diff = float("{:.2f}".format(MY_SRC_QTY - MY_INITIAL_SRC_QTY))
		if val_diff > 0:
			print(" [DIFF: " + C_GREEN + str(val_diff) + C_NORMAL + "]")
		elif val_diff < 0:
			print(" [DIFF: " + C_RED + str(val_diff) + C_NORMAL + "]")
		else:
			print("")
		
		#STEP 7 - analyses avancées.
		# On stocke les données en csv.
		line_to_append = [DT_STR, RSI_VAL, SYMBOL_AVG_PRICE, VALUE_AFTER_SELL]
		with open(CSV_FILE, 'a', newline='') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(line_to_append)

		dates = []
		rsi_values = []
		symbol_values = []
		wallet_values = []
		with open(CSV_FILE, 'r') as file: #open CSV file
			reader = csv.reader(file)
			next(reader)  # Skip header row if it exists
			for row in reader: #boucle pour MAJ (daes, rsi_values & symbol_values) avec les données venant du CSV (rreprésentées par la variable row)
				dates.append(datetime.strptime(row[0], '%d/%m/%Y %H:%M:%S'))
				rsi_values.append(float(row[1]))
				symbol_values.append(float(row[2]))
				wallet_values.append(float(row[3]))
		#affichage / update du gaphique avec les données mises à jour	
		ax.plot(dates, rsi_values, color="red", marker="o") # make a plot
		ax2.plot(dates, symbol_values ,color="blue",marker="o") # make a plot with different y-axis using second axis object
		ax3.plot(dates, wallet_values ,color="green",marker="o") # make a plot with different y-axis using third axis object
		plt.draw()
		plt.pause(1)

	except Exception as e:
		print("[" + DT_STR + "]",end="") #affichage de la date & time
		print(" [ERROR 201] [STATUS: " + C_RED + "BOT general failure" + C_NORMAL + "] [REASONS: Network issue ? exchange not responding ?")
		print(e)
		
	#time.sleep(SLEEP_TIME_SEC)
	# Wait for both threads to finish execution
	thread1.join()

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
