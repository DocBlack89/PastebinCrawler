#check pastebin archive
#verifier à une fréquence entre 1 et 5 minutes

import requests
from lxml.html import fromstring
from itertools import cycle
from bs4 import BeautifulSoup
import traceback
#from stem import Signal
#from stem.control import Controller
from fake_useragent import UserAgent
import re
import sqlite3
from sqlite3 import Error
import time
import datetime


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:50]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies



def get_archive():
	headers = { 'User-Agent': UserAgent().random }
	url_archive = 'https://pastebin.com/archive'
	try:
		response = requests.get(url_archive, headers=headers)
	except:
		print("Skipping. Connection error")
	return response



def get_urls(archives):
	urls = []
	soup = BeautifulSoup(archives.text, 'html.parser')
	for td in soup.table.find_all('td', {'class':''}):
		soup2 = td
		for link in soup2.find_all('a'): 
				urls.append(link.get('href'))
	return urls


def get_paste(conn):

	archive=get_archive()
	proxies = get_proxies()
	proxy_pool = cycle(proxies)
	urls=get_urls(archive)
	k=1
	for i in range(len(urls)):
		proxy = next(proxy_pool)
		print(proxy)
		request_number = str(i+1)
		print("Request #"+request_number)
		url = 'https://www.pastebin.com'+urls[i]
		print(url)
		headers = { 'User-Agent': UserAgent().random }
		ok = False
		if k==5:
			proxy=next(proxy_pool)
		ok = False
		exist = verif_paste_bdd(urls[i], conn)
		if exist == 0:
			k=k+1
			while ok == False:
				try:
					response = requests.get(url,headers=headers)#, proxies={"http": proxy, "https": proxy})
					with open ("./"+urls[i]+".txt", "w") as f:
						f.write(response.text)
					ok = True
				except:
					print("Next proxy")
					proxy = next(proxy_pool)
			detection_code(response.text, conn, urls[i])


def detection_code(text, conn, url):
	regex = ["/loreal/gmi"] #Ajouter toute les regex
	for reg in regex:
		find = re.search(reg, text)
		if (find):
			#############Ajout dans la BDD###############
			sql = ''' INSERT INTO urls(url, match, date_scan) VALUES (?,?,?)''' 
			value = (url, 1, datetime.datetime.now())
			cursor = conn.cursor()
			cursor.execute(sql, value)
			return 
	sql = ''' INSERT INTO urls(url, match, date_scan) VALUES (?,?,?)''' 
	value = (url, 0, datetime.datetime.now())
	cursor = conn.cursor()
	cursor.execute(sql, value)



def verif_paste_bdd(url, conn):
	cursor = conn.cursor()
	sql = "SELECT * FROM urls WHERE url = %s"
	result = cursor.fetchone()
	if result is None:
		return 0
	else:
		return 1


def create_connection(db):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db)
    except Error as e:
        print(e)
    finally:
        if conn:
           return conn 


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        print("create table")
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)



def main():
	sql_create_urls_table = """ CREATE TABLE IF NOT EXISTS urls (
										id integer PRIMARY KEY AUTOINCREMENT,
										url text NOT NULL,
										match text,
										date_scan text
									); """
	# create a database connection
	conn = create_connection(r"./url.db")

	# create tables
	if conn is not None:
		# create projects table
		create_table(conn, sql_create_urls_table)
		while 1:
			get_paste(conn)
			time.sleep(180)
	else:
		print("Error! cannot create the database connection.")
	


if __name__ == '__main__':
    main()