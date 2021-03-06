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

element_type = {1: 'GK', 2: 'DF', 3: 'MD', 4: 'FW'}

# todo: add slash commands!

@client.event
async def on_ready():
    print(f'Bot is working! {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.guild.name != 'FPL Analytics Community':
        return

    allowed_channels = ['⚛bot-test-area', '⚙bot']
    if message.channel.name not in allowed_channels:
        return
    if message.content.lower().startswith('fbref') or message.content.lower().startswith('!fbref'):
        words = message.content.split()

        if len(words) == 1:
            await message.channel.send('Use "fbref player_name to request. Example: "fbref Salah"')
            return
        
        keywords = ['info', 'goal', 'assist', 'xG', 'xA']
        key = 'info'

        if len(words) == 2:
            player = words[1]
        elif words[1] in keywords:
            key = words[1]
            player = ' '.join(words[2:])
        else:
            player = ' '.join(words[1:])

        def get_ratio(row):
            name = row['web_name']
            return fuzz.token_sort_ratio(name, player)

        el_copy = elements.copy()
        el_copy.dropna(subset=['fbref_id'], inplace=True)
        el_copy['match'] = elements.apply(get_ratio, axis=1)
        el_copy.sort_values(by='match', inplace=True, ascending=False)
        player_entry = el_copy.iloc[0].to_dict()

        if key == 'info':
            # general info
            print(message)
            print(player_entry)
            if player_entry['match'] < 80:
                await message.channel.send(f'Could not find `{player}` among FPL API web names. Did you mean {player_entry["web_name"]}? [Match: {player_entry["match"]}%]')
                return
           
            fbref_id = player_entry['fbref_id']
            url = f"https://fbref.com/en/players/{fbref_id}/"
            try:
                df = pd.read_html(url)
            except:
                await message.channel.send(f'Error when reading {player_entry["web_name"]} overview page')
                return
            target = df[0].dropna()
            embed = discord.Embed(title=f"{player_entry['first_name']} {player_entry['second_name']} - Overview", url=url, description="", color=discord.Color.blue())
            values = target.to_dict(orient='records')
            # embed.set_thumbnail(url=f"https://fbref.com/req/202005121/images/headshots/{fbref_id}_2018.jpg")
            embed.set_thumbnail(url="https://resources.premierleague.com/premierleague/photos/players/110x140/p" + player_entry['photo'].replace(".jpg", ".png"))
            # embed.add_field(name='Name', value=player_entry['web_name'], inline=True)
            # embed.add_field(name='Position', value=element_type[player_entry['element_type']], inline=True)
            for v in values:
                try:
                    embed.add_field(name=v['Statistic'], value=f"{v['Per 90']}  **Per 90**\n{v['Percentile']}  **Percentile**", inline=True)
                except:
                    await message.channel.send(f"Error occurred while reading stats for player {player}, fbref url: {url}")
                    return
            await message.channel.send(embed=embed)

try:
    config = dotenv_values(".env")
except:
    config = {}
client.run(config.get('TOKEN', os.environ.get('TOKEN')))

