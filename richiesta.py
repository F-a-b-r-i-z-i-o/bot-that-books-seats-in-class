import logging, requests
from bs4 import BeautifulSoup as bs
import sys

#utilizzo librerie logging e requests per fare una richietsa post al sito dell'unipg
#utilizzo libreria beautifulsoup per prendere i tag html che mi interessano dopo aver fatto la richiesta.
 




#funzione che si occupa di fare lo scrap delle pagine dei professori 
def name2link(string):
    #link interrogato
    base_url = 'https://www.unipg.it/personale/{}.{}/didattica'
    #gestione delle eccezioni dei nomi
    name = ''
    surname = ''
    compositions = ['de', 'del', 'della', 'delli', 'dello', 'dal', 'la', 'lo', 'lu', 'li']

    splitted_name = string.lower().split()
    name = splitted_name[0]

    if splitted_name[1] in compositions:
        surname = splitted_name[1]+splitted_name[2]
    elif "'" in splitted_name[1]:
        surname = splitted_name[1].replace("'", "")
    else:
        surname = splitted_name[1]

    return base_url.format(name, surname)

#funzione che si occupa di fare lo scrap del sito.
def scraping(text):
    parsed=[]
    data={'query': text}
    #richiesta fatta in post al sito
    response = requests.post("https://www.unistudium.unipg.it/unistudium/cercacorso.php?p=0", data=data)
    soup = bs(response.text, features='lxml')
    table=soup.find('table')

    if not table:
        return None
    
    #selezionamento tag da prendere
    rows = table.find_all('tr')
    
    # for che si occupa di prendere le colonne della pagimna web
    for row in rows[1:]:
        #creazione dizionario
        data = {}
        #selezionamento tag specifico
        cols = row.find_all('td')
        #selezionamento link 
        link = cols[-1].find('a')['href']
        #selezionamento ultima colonna pagina web
        cols = [ele.text.strip() for ele in cols[:-1]]
        cols.append(link)
        #corrispondenza parola dizionario colonna
        data['nome_corso'] = cols[0]
        data['docente'] = cols[1]
        data['corso_laurea'] = cols[2]
        data['link_meeting'] = link
        data['link_docente'] = name2link(cols[1])

        parsed.append(data)
 
    return parsed