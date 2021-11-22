import discord
from dotenv import dotenv_values
import requests
import pandas as pd
from fuzzywuzzy import fuzz
import os

client = discord.Client()

id_map = pd.read_csv("id_map.csv")
r = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
elements = pd.DataFrame(r.json()['elements'])
elements = pd.merge(elements, id_map, left_on="id", right_on="fpl_id", how="left")

@client.event
async def on_ready():
    print(f'Bot is working! {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.guild.name != 'FPL Analytics Community':
        return
    if message.content.startswith('fbref'):
        words = message.content.split()
        if len(words) > 1:
            player = words[1]
        else:
            await message.channel.send('Use "fbref player_name stat_name(optional) number_of_games(optional)" to request. Example: "fbref Salah xG 5"')
            return

        def get_ratio(row):
            name = row['web_name']
            return fuzz.token_sort_ratio(name, player)

        el_copy = elements.copy()
        el_copy['match'] = elements.apply(get_ratio, axis=1)
        el_copy.sort_values(by='match', inplace=True, ascending=False)
        player_entry = el_copy.iloc[0].to_dict()

        # keywords = ['goal', 'assist', 'xG', 'xA']

        if len(words) == 2: # and words[-1] not in keywords:
            # general info
            print(message)
            print(player_entry)
            fbref_id = player_entry['fbref_id']
            url = f"https://fbref.com/en/players/{fbref_id}/"
            df = pd.read_html(url)
            target = df[0].dropna()
            await message.channel.send("```" + target.to_string() + "```\nLink: " + str(url))

try:
    config = dotenv_values(".env")
except:
    config = {}
client.run(config.get('TOKEN', os.environ('TOKEN')))
