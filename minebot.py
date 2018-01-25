import re
from mattermost_bot.bot import Bot, respond_to, listen_to

import termine

@respond_to('Bonjour', re.IGNORECASE)
def hi(message):
    response = termine.init()
    message.send('Bonjour ! ')

@listen_to('lance termine', re.IGNORECASE)
def init(message):
    response = termine.init()
    message.send('Termine lancé ! ')
    message.send(response)

@listen_to('(^[A-Za-z]{1}[0-9]{1,2}$)', re.IGNORECASE)
def step(message, coords):
    response = termine.step(coords)
    message.send('Ouverture de la cellule ' + coords + ':')
    message.send(response)

@listen_to('(^[Ff]{1}[A-Za-z]{1}[0-9]{1,2}$)', re.IGNORECASE)
def flag(message, coords):
    response = termine.step(coords)
    message.send('Flag ' + coords + ':')
    message.send(response)

@listen_to('help', re.IGNORECASE)
def help(message):
    message.send('- "Lance Termine" permet de lancer une partie')
    message.send('- Écrire une lettre puis un numéro sans espace pour ouvrir une cellule, exemple : "C4".')
    message.send('- Ajouter F devant pour mettre un drapeau, exemple : "FB6"')

if __name__ == "__main__":
    Bot().run()
