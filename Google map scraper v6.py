from bs4 import BeautifulSoup
#import os
import pandas as pd
import time


from selenium import webdriver
#from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
#driver = webdriver.Chrome(ChromeDriverManager().install())

def grab_links(urls):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--log-level=OFF')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)
    driver.set_page_load_timeout(30)
    driver.get(urls)
    time.sleep(2)
    ActionChains(driver).send_keys(Keys.END).pause(1).send_keys(Keys.END).perform()
    time.sleep(2)
    html = driver.page_source
    print('getting links')
    soup = BeautifulSoup(html, features="html.parser")
    links = []        #getting links from the google maps search
    for link in soup.find_all('a'):
        if link.get('href') != None:
            if 'https://www.google.com/maps/place/' in link.get('href'):
                links.append(link.get('href'))
    page_link = links
    print("there are {} links on the first page".format(len(page_link)))
    
    while len(page_link) == 20:
        page_link = []
        try:             #finding next page button
            next_page_e = driver.find_element_by_css_selector("button[jslog^='12696']")
            next_page_e.click()
            print("next page")
            time.sleep(2)
            e = driver.find_element_by_css_selector("a[href^='https://www.google']")
            ActionChains(driver).move_to_element_with_offset(e,10,-10).click().send_keys(Keys.END).pause(1).send_keys(Keys.END).perform()
            time.sleep(2)
            html2 = driver.page_source
            soup2 = BeautifulSoup(html2, features="html.parser")
            for link in soup2.find_all('a'):
                if link.get('href') != None:
                    if 'https://www.google.com/maps/place/' in link.get('href'):
                        page_link.append(link.get('href'))
                        links.append(link.get('href'))
            print("there are {} links on the next page".format(len(page_link)))
    
        except Exception as e:
            print(e)
            print("no next page")
    
    driver.quit()
    return links
             
def grab_html(urls):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('log-level=3')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)
    driver.set_page_load_timeout(30)
    print('getting html')
    driver.get(urls)
    time.sleep(1)
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, features="html.parser")
    return soup

def clean_extra(a):
    a = str(a)
    a = a.replace(' St,', ' Street,')
    a = a.replace(' Rd,', ' Road,')
    a = a.replace(' Ave,', ' Avenue,')
    a = a.replace(' Cct,', ' Circuit,')
    a = a.replace(' Tce,', ' Terrace,')
    a = a.replace(' Pl,', ' Place,')
    a = a.replace('Level ','L')
    a = a.replace(' Dr,', ' Drive,')
    
    slash_index = a.find('/')
    unit = ""
    if slash_index != -1:
        unit = a[:slash_index]
        a = a[slash_index+1:]

    words = a.split()
    postcode = words[-1]
    words = words[:-1]
    state = words[-1]
    words = words[:-1]
    suburb = words[-1]
    words = words[:-1]
    
    #If suburb is Capitalised:
    if words[-1].isupper():
        suburb = words[-1] + " " + suburb
        words = words[:-1]
    
    #If there's a comma seperating street and suburb:
    if a.find('-1') !=-1 and words[-1].find(',') == -1:
        suburb = words[-1] + " " + suburb
        words = words[:-1]
    
    number = ''
    street = ''
    for word in words:
        word = word.replace(',', '')
        if not word.isalpha():
            number = number + ' ' + word
        else:
            street = street + ' ' + word
            

    if len(number)>0 and unit =='':
        number = number[1:]
        number = number.split()
        unit = ' '.join(number[:-1])
        number = number[-1]

    street = street[1:]
    
    return unit, number, street, suburb, state, postcode
    

df = pd.DataFrame()
base_url = "https://www.google.com/maps/search/{0}+{1}+{2}+{3}+{4}+directory/"
emdr = pd.read_excel(r'N:\TS\Alex\EMDR - not enough tenant.xlsx')
A = emdr.loc[:,"Address"]
BuildingId = emdr.loc[:,'SiteBuildingId']


try:
    for i in range(len(A)): #
        address = A[i]
        U, N, St, Su, S, P = clean_extra(address)

        url = base_url.format(N,St.replace(' ','+'),Su.replace(' ','+'),S,P)
        print(url)
        links = grab_links(url)
        BID = BuildingId[i]
#grabbing phone and address from place locations
        for link in links:
            soup3 = grab_html(link)
            title = soup3.title.contents
            dictt = {}
            dictt['Search term'] = address
            dictt['Building Id'] = BID
            dictt['Title'] = title[0].replace(' - Google Maps','')
            dictt['Address'] = None
            dictt['Website'] = None
            dictt['Phone'] = None
            dictt['Does Address Match'] = None
            for button in soup3.find_all('button'):
                i = button.get('data-item-id')
                if i == 'address':
                    ad = button.get('aria-label').replace('Address: ','')
                    dictt['Address'] = ad
                    try:
                        unitx, numberx, streetx, suburbx, statex, postcodex = clean_extra(ad)
                        number = numberx.replace(' ','')
                        if (number == str(N) or number.find(str(N))!=-1 or str(N).find(number)!=-1 )and streetx == St:
                            dictt['Does Address Match'] = 'Yes'
                        else:
                            dictt['Does Address Match'] = 'No'
                    except Exception as e:
                        print(e)
                        dictt['Does Address Match'] = 'No'
                if i != None:
                    if i.find('phone:') != -1:
                        phone_temp = button.get('aria-label').replace('Phone: ','')
                        phone_temp = phone_temp.replace(' ','')
                        phone_temp = phone_temp.replace('(','')
                        phone_temp = phone_temp.replace(')','')
                        dictt['Phone'] = phone_temp
                    
            for el in soup3.find_all('a'):
                    if el.get('data-item-id') == 'authority':
                        dictt['Website'] = el.get('href')
            print(dictt)
            df_temp = pd.DataFrame([dictt])
            df = pd.concat([df, df_temp],ignore_index=True)
            
except KeyboardInterrupt:
    print('Stopped searching Google Maps, now preparing results')
    pass


import difflib
import re

def clean(t,n,s,EN,u,b,p,c):
    l = n.lower()
    vert = 'Office'
    if l.find('meats') != -1 or l.find('abattoir')!=-1:
        vert = 'Abattoirs'
    if l.find('aged care') != -1 or l.find('nursing home')!=-1:
        vert = 'Aged Care'
    if l.find('airport') != -1:
        vert = 'Airport'
    if l.find('pool')!=-1 or l.find('swim')!=-1 or l.find('aquatic')!=-1:
        vert = 'Aquatic'
    if l.find('early learn')!=-1 or l.find('childcare')!=-1 or l.find('child care')!=-1 or l.find('pre school')!=-1:
        vert ='Child Care'
    if l.find('church')!=-1:
        vert = 'Churches'
    if l.find('cinema')!=-1:
        vert = 'Cinema'
    if l.find('club')!=-1:
        vert = 'Club (with Poker machines)'
    if l.find('centre')!=-1 and (l.find('conference')!=-1 or l.find('convention')!=-1):
        vert = 'Conference centres'
    if l.find('school')!=-1 or l.find('college')!=-1 or l.find('academy')!=-1:
        vert = 'Independent school-HS or College'
    if l.find('gym')!=-1 or l.find('fitness')!=-1:
        vert = 'Gym / leisure'
    health_list = ['medic', 'health','doctor', 'patholog', 'dr ','clinic','massage', 'dr.',
                   'dental','psychother','counsellin', 'physiolog','orthopaedic','psycholog','optomet']
    for item in health_list:
        if l.find(item)!=-1:
            vert = 'Health'
    if l.find('hospital')!=-1:
        vert = 'Hospital'
    if l.find('hotel')!=-1 or l.find('resort')!=-1:
        vert = 'Hotel'
    if l.find('factory')!=-1 or l.find('wharf')!=-1:
        vert = 'Industrial site'
    if l.find('motel')!=-1 or l.find('motor inn')!=-1:
        vert = 'Motel / Hostels'
    if l.find('museum')!=-1 or l.find('gallery')!=-1 or l.find(' art ')!=-1:
        vert = 'Museums/ Art Galleries'
    if l.find('parking')!=-1 or l.find('carpark')!=-1 or l.find ('car park')!=-1:
        vert = 'Parking Stations'
    if l.find('rugby')!=-1 or l.find('tennis')!=-1 or l.find('sport')!=-1 or l.find(' park ')!=-1 or l.find('football')!=-1 or l.find('netball')!=-1 or l.find('basketball')!=-1:
        vert = 'Public Domain  /sporting centre'
    if l.find('tavern')!=-1 or l.find(' inn')!=-1:
        vert = 'Pubs'
    retail_list = ['cafe','shop ','restaurant','pharmac','hairdres','newsagenc','florist','barber','café']
    for item in retail_list:
        if l.find(item)!=-1:
            vert = 'Retail - shops'
    if l.find('shopping')!=-1 or l.find('plaza')!=-1 or l.find(' mall ')!=-1:
        vert = 'Shopping centre'
    if l.find('stadium')!=-1:
        vert = 'Stadium'
    if l.find('theatre')!=-1 or l.find('opera')!=-1 or l.find('entertainment')!=-1:
        vert = 'Theatres/Operas/ Ent Centres'
    if l.find('universit')!=-1 or l.find('tafe')!=-1:
        vert = 'University'
    #return vert

    check = []
    if t.find(n)!=-1 and t.find(s)!=-1:
        check.append('Company is Building')
    
    ct = t.title()
    if ct.find('|') !=-1:
        ct = ct[:ct.find('|')]
    if ct.find('-') > 7 :
        ct = ct[:ct.find('-')]
        
    #Removing chinese characters
    for n in re.findall(r'[\u4e00-\u9fff]+', ct):
        ct = ct.replace(n,'')
    
    match_ratio = 0
    for existingname in EN:
        tempmatch = int(difflib.SequenceMatcher(None, existingname, ct).ratio()*100)
        if tempmatch > match_ratio:
            match_ratio = tempmatch
            
    if match_ratio >80:    #Percentage match
        check.append('Company exists in building')
    
    if len(ct)>50:
        check.append('Long Company name')
    #return ct, t_check

    words = b.split()
    unit = u.split()
    cleared_unit = u.split()
    for k in range(len(unit)):
        for j in range(len(words)):
            if unit[k].find(words[j])!=-1:
                try:
                    cleared_unit.remove(unit[k])
                except:
                    break
    unit_cleaned = ' '.join(cleared_unit)
    
    if len(unit_cleaned)>20:
        check.append('Long unit')
        
    #return unit_cleaned, u_check
    
    phone = str(p)
    phone = phone.replace('+61','0')
    if phone.find('+64')!=-1 and phone.find('+')!=-1:
        check.append('International number')
    if phone[:4] == '1300' or phone[:4] == '1800' or len(phone)==6:
        check.append('Check for better phone')
    elif phone[0] != str(0):
        check.append('Check phone')
    
    #return phone, phone_check
        
    c = list(c)
    ntstenp = c.count('TSTENP')
    ntscall = c.count('TSCALL')
    
    if vert == 'Retail - shops':
        cod = 'SMSHOP'
        f = 0
    else:
        if ntstenp > 0 and ntscall == 0:
            cod = 'TSTENP'
            f = 3
        elif ntstenp == 0 and ntscall > 0:
            cod = 'TSCALL'
            f = 3
        elif ntstenp ==0 and ntscall == 0:
            cod = 'TENANT'
            f = 0
        else:
            cod = 'TENANT'
            f = 0
            check.append('Check Code')
    
    return vert,ct,unit_cleaned,phone, cod, f, check 

bdb = pd.read_excel(r'N:\TS\Kevin\Building name vs code.xlsx')
alp = pd.read_excel(r'N:\TS\Kevin\All phones.xlsx')
allphones = list(alp.loc[:,"Phone"])

Address = df.loc[:,"Address"]
Title = df.loc[:,"Title"]
Phone = df.loc[:,"Phone"]
Bu_Id = df.loc[:,"Building Id"]
Does_Address_Match = df.loc[:,'Does Address Match']


google_url ='https://www.google.com/search?q='

keys = ['Google link','Name','Size','Unit','Number','Street','Suburb','State','Postcode','Phone','Vertical','BuildingName','Code','CallFrequency','Check', 'Notes']
df2 = pd.DataFrame()
for i in range(len(Address)): 
    values = [None]*len(keys)
    d = dict(zip(keys,values))
    if Does_Address_Match[i] == 'Yes' and allphones.count(Phone[i]) == 0 and Phone[i]!= None:
        Unit, Number, Street, Suburb, State, Postcode = clean_extra(Address[i])

        #determining code to use
        dd = bdb.loc[bdb['BuildingId'] == Bu_Id[i]]
        BuildingName = dd['BuildingName'].iloc[0]
        Codes = dd['Code']
        ExistingNames = dd['Name']
        
        vertical,Title_cleaned,Unit_cleaned,Cleaned_Phone,Code,freq,Check = clean(Title[i],Number,Street,ExistingNames,Unit,BuildingName,Phone[i],Codes)
        
        d['Google link'] = google_url+Title[i].replace(' ','+')+'+'+Address[i].replace(' ','+')
        d['Name'] = Title_cleaned   #'Name'
        d['Size'] = '025'    #size
        d['Unit'] = Unit_cleaned.title()   #unit
        d['Number'] = Number.replace(' ','')    #Street number
        d['Street'] = Street     # Street
        d['Suburb'] = Suburb.upper()     # Suburb
        d['State'] = State      # State
        d['Postcode'] = Postcode   # Postcode
        d['Phone'] =  Cleaned_Phone # Phone
        d['Vertical'] = vertical  #Vertical
        d['BuildingName'] = BuildingName #Building name
        d['Code'] = Code              #Code
        d['Check'] = '/'.join(Check)
        d['CallFrequency'] = freq   #Call Frequency
      
        #df = df.append(pd.DataFrame([values], columns=column), ignore_index=True)
        df2_temp = pd.DataFrame([d])
        df2 = pd.concat([df2, df2_temp],ignore_index=True)

df2.to_excel('Check EMDR sites 19 July.xlsx')

df.to_excel('Google Maps Scrape results 19.07.2022.xlsx')
