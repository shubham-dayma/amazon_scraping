from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import time
import datetime
import mysql.connector
import urllib.request
from selenium.webdriver.common.action_chains import ActionChains

class Scrap:
    def __init__(self):
        self.bot = webdriver.Chrome("D:/Python_script/drivers/chromedriver_win32/chromedriver.exe")
        self.store_front = "https://www.amazon.com/s?marketplaceID=ATVPDKIKX0DER&me=A17MC6HOH9AVE6"
        self.crawl_page_no = '151'
        self.mydb = mysql.connector.connect(
                      host="localhost",
                      database="codeigniter_ecom",
                      user="root",
                      password=""
                    )
        self.cursor = self.mydb.cursor(buffered=True)


    def load_url(self):
        bot = self.bot
        bot.get(self.store_front+'&page='+self.crawl_page_no)
        time.sleep(5)

    def change_zipcode(self, zipcode):
        bot = self.bot
        zipcode_popup_el = bot.find_element_by_id("glow-ingress-line2")
        zipcode_popup_el.click()
        time.sleep(5)
        zipcode_text_el = bot.find_element_by_id("GLUXZipUpdateInput")
        zipcode_text_el.clear()
        zipcode_text_el.send_keys(zipcode)
        zipcode_text_el.send_keys(Keys.RETURN)
        time.sleep(5)
        try:
            confirm = bot.find_element_by_xpath('//*[@id="a-popover-4"]/div/div[2]/span/span')
            confirm.click()
            time.sleep(2)
            bot.get(self.store_front+'&page='+self.crawl_page_no)
            time.sleep(5)
        except Exception as e:
            pass

    def crawl_pages(self):
        bot = self.bot

        #set flag if new page needs to be loaded
        load_next_page = 0
        try :
            next_el = bot.find_elements_by_class_name("a-last")
            classes = next_el[0].get_attribute("class")
            if classes.find('a-disabled') < 0:
                self.crawl_page_no = str(int(self.crawl_page_no) + 1)
                load_next_page = 1
        except Exception as e:
            pass

        # load asins
        asins = []
        product_els =bot.find_elements_by_css_selector('div[data-asin]')
        if product_els :
            for product_el in product_els:
                asin = product_el.get_attribute("data-asin")
                if asin:
                    asins.append(asin)

        #get all asin details
        self.load_product_details(asins)

        # load next page
        if load_next_page == 1:
            bot.get(self.store_front+'&page='+self.crawl_page_no)
            print(self.crawl_page_no)
            time.sleep(3)
            self.crawl_pages()
        
        # save page source code
        # page_source = bot.page_source
        # current_time = datetime.datetime.now()
        # self.saveHtmlResponse(page_source, 'amazon-'+current_time.strftime("%d-%b-%y-%I-%M-%S-%p"))
        # self.load_next_page()
            

    def saveHtmlResponse(self, content, file_name="workfile"):
        filepath = 'scrap_pages/'+file_name+'.html'
        content = content.encode(encoding='UTF-8')
        Html_file = open(filepath,"wb")
        Html_file.write(content)
        Html_file.close()

    def load_next_page(self):
        bot = self.bot
        next_pagination_els = bot.find_elements_by_class_name("a-last")
        for next_el in next_pagination_els:
            classes = next_el.get_attribute("class")
            
            if classes.find('a-disabled') < 0 :
                self.crawl_page_no = str(int(self.crawl_page_no) + 1)
                bot.get(self.store_front+'&page='+self.crawl_page_no)
                time.sleep(5)
                self.crawl_pages()

    def load_product_details(self, asins):
        bot = self.bot
        if asins :
            for asin in asins :
                
                bot.get('https://www.amazon.com/dp/'+asin)
                time.sleep(2)
                
                images = []
                title = ""
                description = ""
                features = ""
                price = "0"
                instock = "0"

                # GET IMAGES
                try:
                    alternet_img_dev = bot.find_element_by_id('altImages')
                    alternet_images = alternet_img_dev.find_elements_by_tag_name('img')
                    for alternet_image in alternet_images:
                        img_path = alternet_image.get_attribute('src')
                        if img_path.find('https://images-na.ssl-images-amazon.com/images/I/') >= 0:
                            images.append(img_path)
                except Exception as e:
                    pass

                # GET TITLE
                try:
                    title_el = bot.find_elements_by_css_selector('span[id="productTitle"]')
                    title = title_el[0].text
                except Exception as e:
                    pass
                
                # GET DESCRIPTION
                try:
                    description = bot.find_element_by_id('featurebullets_feature_div')
                    description = description.text
                    description= description.replace('About this item', "").replace('Show more', "").strip()
                except Exception as e:
                    pass

                # GET FEATURES
                try:
                    featur_el = bot.find_element_by_id('productOverview_feature_div')
                    features = featur_el.text.strip()
                except Exception as e:
                    pass    

                # GET PRICE
                try:
                    price_el = bot.find_element_by_id('priceblock_ourprice')
                    price = price_el.text.replace('$',"")
                except Exception as e:
                    pass

                #IF PRICE NOT FETCHED
                if price == "0":
                    try:
                        price_els = bot.find_elements_by_css_selector('span[data-action="show-all-offers-display"]')
                        for price_el in price_els:
                            price_links = price_el.find_elements_by_css_selector('a.a-link-normal')
                            for price_link in price_links:
                                if price_link.text.find('$') >= 0:
                                    if price_link.find_elements_by_class_name('a-color-price'):
                                        price = price_link.find_elements_by_class_name('a-color-price')[0].text.replace('$',"")
                    except Exception as e:
                        raise

                # GET INSTOCK FLAG
                try:
                    quantity_el = bot.find_elements_by_css_selector('select[name="quantity"]')
                    instock = 1
                except Exception as e:
                    pass

                try:
                    price = float(price.replace(',',""))
                except Exception as e:
                    price = 0
                
                old_price = 0
                
                # REDUCE 2% FROM ORIGINAL PRICE FOR OLD PRICE
                if price > 0:
                    old_price = price + ((2/100)*price)
                    old_price = round(old_price,2)

                # CURRENT TIMESTAMP FOR IMAGE FOLDER AND PRODUCT CREATED DATE
                timestamp = int(datetime.datetime.now().timestamp())

                # CHECK IF ASIN ALREADY EXIST
                sql = 'SELECT * FROM products where asin = "'+asin+'";'
                self.cursor.execute(sql)
                asin_exist = self.mydb.cursor().fetchone()

                # IF ASIN NOT EXIST
                if not self.cursor.rowcount:
                    #DOWNLOAD PRODUCT IMAGES FROM AMAZON
                    main_image = self.downloadImg(images, asin, timestamp)
                    
                    # CREATE PRODUCT SLUG FROM TITLE
                    url = title.translate({ord(c): "_" for c in "!@#$%^&*()[]{};:,./<>?\|`~-=_+ "})
                    url = url.replace('"','').replace("'","")

                    # INSERT RECORD IN PRODUCT TABLES
                    sql = 'INSERT INTO products (folder,image,time,time_update,visibility,shop_categorie,quantity,procurement,in_slider,url,position,asin) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);'

                    values = (timestamp,main_image,timestamp,timestamp,'1','1','100','0','0',url,'1',asin)
                    self.cursor.execute(sql, values)

                    # GET LAST INSERTED ID
                    for_id = self.cursor.lastrowid

                    # UPDATE SLUG WITH _INSERTED_ID 
                    url = url+'_'+str(for_id)
                    sql = 'UPDATE products SET url = "'+url+'" WHERE id ='+str(for_id)+';'
                    self.cursor.execute(sql)

                    # INSERT ENGLISH TRANSLATION RECORDS
                    sql = 'INSERT INTO products_translations (title,description,basic_description,price,old_price,abbr,for_id) VALUES (%s,%s,%s,%s,%s,%s,%s);'
                    values = (title,features+description,features,price,old_price,'en',for_id)
                    self.cursor.execute(sql, values)

                    # DB COMMIT
                    self.mydb.commit()

    def downloadImg(self, images, asin, timestamp):
        # IMAGE PATH TO STORE IN LOCAL
        main_path = "D:/xampp_7.3_new/htdocs/ecommerce-codeIgniter/attachments/shop_images/"+str(timestamp)

        # CREATE MISSING FOLDER FROM GIVEN PATH
        os.makedirs(main_path)

        main_image = ""
        
        for i in range(len(images)):
            image = images[i]

            #SLIT IMAGE PATH WITH "."
            splitted_img = image.split('.')

            # GET IMAGE EXTENSTION
            image_type = splitted_img[-1]

            # UPDATE IMAGE URL TO LARGE IMAGE
            splitted_img[-2] = '_AC_SX385_'

            large_img_url = '.'.join(splitted_img)
            
            path = main_path+"/"+asin+"_"+str(i)+"."+image_type

            # STORE FIRST IMAGE AS MAIN IMAGE
            if i == 0:
                main_image = asin+"."+image_type
                path = "D:/xampp_7.3_new/htdocs/ecommerce-codeIgniter/attachments/shop_images/"+main_image

            # DOWNLOAD AND STORE IMAGE IN GIVEN PATH
            urllib.request.urlretrieve(large_img_url, path)

        return main_image

    def tearDown(self):
        # CLOSE BROWSER
        self.bot.quit() 

obj = Scrap()
obj.load_url()
obj.change_zipcode('90201')
obj.crawl_pages();
obj.tearDown();
# asins = ['B07HCDMLXM']
# obj.load_product_details(asins)
