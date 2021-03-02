import telebot
from richiesta import scraping
from telebot import types
from telebot.apihelper import ApiException
import sqlite3
import os.path

"""
FUNZIONAMENTO DEL BOT:

Viene effettuata una richiesta in post al sito, dove vengono 'parsati' alcuni tag html, successivame i risultati trovati vengono stampati.
Dopo aver stampato i risultati si aprono dei bottoni in cui e' possibile prenotare un'eventuale lezione fisica, o partecipare ad un'eventuale lezione online, inoltre e' possibile verificare il sito web dedicato al professore del corso torvato.

Se si vuole partecipare alla lezione online 
si clicca sul bottone dedicato e si viene rimandato al link della lezione.

Se si vuole prenotare una lezione in sede 
si clicca anche qui sul bottone dedicato e viene occupato un posto.

Il sistema delle prenotazioni fisiche 
e' gestito tramite un db locale, dove non si fa altro che aggiungere o tolgiere la prenotazione effettuata da un dato studente.

Il meto 'antifalsificazione' 
che abbiamo utilizzato entra in gioco mediante la prenotazione. 
Quando uno studente prenota un posto viene stampato il suo id telegram, che corrispondera' sicuramente a quella data persona.
Per non creare confusione il professore puo' chiedere agli alunni di cambiare il proprio id telegram con la propria matricola o con il propio nome e cognome quando si acquisisce una prenotazione.
"""



#modulo telebot si occupa di gestire le funzioni del bot, come mandare i messaggi, o far apparire i bottoni.
#importo file dove faccio lo scraping
#importo il modulo types da telebot per creare la tastiera successivamente.
#sqlite3 e' un modulo per creare un db in python veloce integrato nelle applicazioni, invece di usare un programma server di database separato tipo MySQL, PostgreSQL ed Oracle.
#os.path e' un modulo di py3 che facilita' la scrittura di codice. 


#Definizione capacita' massima aula fisica
MAX_CAPACITY = 30

API_TOKEN = '927219217:AAGDUvyYrU8A5u_L8fmVaoKyc2YLcIWc7Fk'

#Collegamento api del bot
bot = telebot.TeleBot(API_TOKEN)

#Comando help
@bot.message_handler(commands=['help'])
def help(message):
    chat_id=message.chat.id
    bot.send_message(chat_id, """I comandi selezionabili sono:
    /start 
    /search 
    /help

    
    se vuoi avviare bot:
     /start
    se vuoi cercare la lezione:
     /search + nome professore o lezione\
    """)

#Comando start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id=message.chat.id
    #invio messaggio dal bot
    bot.send_message(chat_id, """\
Ciao il mio nome e' UNIPrenotazione, sono qui per aiutartia prenotare un posto a lezione.
Per prima cosa cerca la lezione a cui vuoi prenotarti.
Prima di procedere visualizza i comandi.

Selezioando /help\
""")

#Comando search
@bot.message_handler(commands=['search'])
def search(message):

    chat_id=message.chat.id
    #divide la stringa in base agli spazi
    keywords = message.text.split()
    #controllo per verifica che i comandi inseriti siano corretti
    if len(keywords) < 2:
        bot.send_message(chat_id, text="""\
            Errore.
            Digitare /search nome del corso o docente.
            Per effettuare la ricerca\
        """)
        
        return

    #richiamo funzione do_search
    do_search(keywords[1], chat_id, message.from_user.username)
    

def do_search(message, chat_id, username):
    #richiamo la funzione di scrap, interpretandola come una matrice
    matrix = scraping(message)
    print(matrix)
    #gestisco le eccezioni in caso l'indagine nel sito non abbia portato risultati
    if not matrix:
        bot.send_message(chat_id, text='NESSUN RISULTATO')
        return

    markup = types.InlineKeyboardMarkup(row_width=1)

    #stampo solo i primi 10 risultati, in quanto corsi molto grandi, darebbero errori.
    for row in matrix[:10]:
        try:
            code = row['nome_corso'].split('--')[1].split()[0]
        except IndexError:
            pass

        #creazione dei bottoni    
        markup.add(
            types.InlineKeyboardButton(text=row['nome_corso'], url=row['link_meeting']),
            types.InlineKeyboardButton(text=row['docente'], url=row['link_docente']),
            types.InlineKeyboardButton(text='Prenota \U00002714', callback_data=str("pren-"+code+"-"+username)),
            types.InlineKeyboardButton(text='Annulla prenotazione \U0000274C', callback_data=str("unpren-"+code+"-"+username)),
            types.InlineKeyboardButton(text='\U0001F539', callback_data='sep'),
        )
    #gestisco eventuali corsi o docenti non presenti
    bot.send_message(chat_id, text='Se il tuo corso non è tra quelli mostrati fai una ricerca più specifica', reply_markup=markup, parse_mode='HTML')

#funzione che si occupa di inserire la prenotazione all'interno del db, tutte le azioni effettuate, vengono inserite all'interno dei bottoni presenti.
@bot.callback_query_handler(lambda query: query.data.startswith("pren-"))
def pren_callback(query):
    #setto prenotazioni a zero
    n_pren = 0

    chat_id = query.message.chat.id
    #stampo query db
    print(query.data)
    course_id = query.data.split('-')[1]
    student = query.data.split('-')[2]
    #stampo id corso e studente, presete nel db
    print(course_id, student)
   

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "prenotazioni.db")
    #connesione db con sqlite3 crato precedentemente
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()

        # controllo se la capacita massima e stata raggiunta
        data = (course_id, )
        c.execute('SELECT COUNT(*) FROM CorsiStudenti GROUP BY corso HAVING corso = ?', data)
        #gestisco il limiti di posti che un'aula puo' contenere
        try:
            if c.fetchone()[0] == MAX_CAPACITY:
                bot.send_message(chat_id, text='Capacita di studenti massima raggiunta per questa lezione')
                return
        except TypeError:
            pass
        
        # controllo se ha gia prenotato
        data = (student, course_id,)
        c.execute('SELECT * FROM CorsiStudenti AS cs WHERE cs.studente = ? AND cs.corso = ?', data)
        if c.fetchone():
            bot.send_message(chat_id, text='Hai gia prenotato questa lezione')
        else:
            
            data = (course_id,)
            c.execute('SELECT * FROM Corso AS c WHERE c.id=?;', data)
            
            # controlla se il corso si trova nel db
            if not c.fetchone():

                data = (course_id,)
                c.execute('INSERT INTO Corso (id) VALUES (?);', data)

            data = (student,)
            c.execute('SELECT * FROM Studente AS s WHERE s.telegram_id=?;', data)

            # controllo se lo studente si trova nel db
            if not c.fetchone():
                data = (student,)
                c.execute('INSERT INTO Studente (telegram_id) VALUES (?);', data)
            
            # inserisco la prenotazione
            data = (student, course_id,)
            c.execute('INSERT INTO CorsiStudenti (studente, corso) VALUES (?, ?)', data)

            data = (course_id, )
            c.execute('SELECT COUNT(*) FROM CorsiStudenti GROUP BY corso HAVING corso = ?', data)
            
            try:
                n_pren = c.fetchone()[0]
            except TypeError:
                n_pren = 0
            
            bot.send_message(chat_id, text=str('Lezione prenotata, rimangono '+str(MAX_CAPACITY-n_pren) + ' posti su ' + str(MAX_CAPACITY)))

#funzione che si occupa di eliminare la prenotazione all'interno del db, tutte le azioni effettuate, vengono inserite all'interno dei bottoni presenti.
@bot.callback_query_handler(lambda query: query.data.startswith("unpren-"))
def unpren_callback(query):
    #setto prenotazioni a 0
    n_pren = 0

    chat_id = query.message.chat.id
    #stampo query db
    print(query.data)
    course_id = query.data.split('-')[1]
    student = query.data.split('-')[2]
    #stampo id corso
    print(course_id, student)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "prenotazioni.db")
    #connesione db mysql3 crato precedentemente
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()

        
        # controllo se ha gia prenotato
        data = (student, course_id,)
        c.execute('SELECT * FROM CorsiStudenti AS cs WHERE cs.studente = ? AND cs.corso = ?', data)
        if not c.fetchone():
            bot.send_message(chat_id, text='Non hai prenotato questa lezione')
        else:
            
            # elimino la prenotazione
            data = (student, course_id,)
            c.execute('DELETE FROM CorsiStudenti AS cs WHERE cs.studente=? AND cs.corso=?', data)

            data = (course_id, )
            c.execute('SELECT COUNT(*) FROM CorsiStudenti GROUP BY corso HAVING corso = ?', data)
            
            try:
                n_pren = c.fetchone()[0]
            except TypeError:
                n_pren = 0
            
            bot.send_message(chat_id, text=str('Prenotazione cancellata, rimangono '+str(MAX_CAPACITY-n_pren) + ' posti su ' + str(MAX_CAPACITY)))
        
#metodo che mantiene bot in ascolto
bot.polling()