import requests

import socket

from bs4 import BeautifulSoup

from lxml.html import fromstring

class scrap():
	def __init__(self):
		pass

	def get_proxies(self):
	    url = 'https://free-proxy-list.net/'
	    
	    response = requests.get(url)
	    
	    parser = fromstring(response.text)
	    
	    proxies = set()
	    
	    for i in parser.xpath('//tbody/tr')[:20]:
	        if i.xpath('.//td[7][contains(text(),"yes")]') and i.xpath('.//td[3][contains(text(),"US")]'):
	            #Grabbing IP and corresponding PORT
	            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
	            # proxies.add(proxy)
	    if not proxies:
	    	# hostname = socket.gethostname()
	    	# local_ip = socket.gethostbyname(hostname)
	    	# proxies.add(local_ip)        
	    	proxies.add('localhost')        
	    return proxies	
			
	def connect_amazon(self, store_front_url, proxies):
		# http://www.networkinghowtos.com/howto/common-user-agent-list/
		HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36',
			'Accept-Language': 'en-US, en;q=0.5',
			'cookie' : "i18n-prefs=USD;"}

		zipcode_post_url = "https://www.amazon.com/gp/delivery/ajax/address-change.html"; 

		# zip_code_form_data = {'form_params' : {'locationType':'LOCATION_INPUT', 'zipCode':'90201', 'storeContext':'office-products', 'deviceType':'web', 'pageType':'Detail', 'actionSource':'glow'}};

		zip_code_form_data = {'locationType':'LOCATION_INPUT', 'zipCode':'90201', 'storeContext':'office-products', 'deviceType':'web', 'pageType':'Detail', 'actionSource':'glow'};
			
		for proxy in proxies:
			session_request = requests.Session() 
			try:
				proxy_config = {}

				if proxy != 'localhost':
					proxy_config = {"http": proxy, "https": proxy}

				zipcode_post_response = session_request.post(zipcode_post_url, data = zip_code_form_data, headers={'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'}, proxies=proxy_config)
				self.saveHtmlResponse(zipcode_post_response.content, 'workfile_zip_'+proxy)
				# fetch the url
				get_response = session_request.get(store_front_url, headers=HEADERS, proxies=proxy_config)

				if get_response.content:
					self.saveHtmlResponse(get_response.content, 'workfile_'+proxy)

					# # create the object that will contain all the info in the url
					# soup = BeautifulSoup(get_response.content, features="lxml")
					
					# country = soup.find(id="glow-ingress-line2")

					# print(country)
					# for el in soup.select('.s-no-outline'):
					# 	print(el['href'])
				else :
					print("Skipping. Connnection error for proxy:"+proxy+'.JSON Response:'+get_response.Json)
			except:
				print("Skipping. Connnection error for proxy:"+proxy)	

	def saveHtmlResponse(self, content, file_name="workfile"):
		filepath = 'error_logs/'+file_name+'.html'
		Html_file = open(filepath,"wb")
		Html_file.write(content)
		Html_file.close()

self_obj = scrap()

proxies = self_obj.get_proxies()

store_front_url = "https://www.amazon.com/s?me=A25DPGHLKODDOE&marketplaceID=ATVPDKIKX0DER"

self_obj.connect_amazon(store_front_url, proxies)


