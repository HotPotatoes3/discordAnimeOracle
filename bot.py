import os
import random
import shutil
import uuid
import PIL.Image
import discord
from discord.ext import commands, tasks
import requests
import responses
import sqlite3




def run_discord_bot(discord):
    TOKEN = os.environ['TOKEN']

    app_commands = discord.app_commands
    bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())
    bot.remove_command("help")

    @bot.event
    async def on_ready():
        print(f"{bot.user} is ready")
        try:
            synced = await bot.tree.sync()
        except Exception as e:
            print(e)

    @bot.command()
    async def searchanime(ctx):
        input = ctx.message.content[13:]
        url = f'https://api.myanimelist.net/v2/anime?q={input}&limit=5'
        result = responses.makeMALCall(url)
        data = result['data']
        await ctx.reply("Here are your top search results: ")
        for i in data:
            title = i['node']['title']
            id = i['node']['id']
            img = i['node']['main_picture']['medium']

            resp = f'**Title: {title}**\nID: {id}\n{img}'
            view2 = getDetails(id)
            await ctx.send(resp, view=view2)
        view = searchMenu(input)
        await ctx.reply("If you didn't find what you were looking for, click here to get more search results", view = view)


    class searchMenu(discord.ui.View):
        def __init__(self, text):
            super().__init__()
            self.value = None
            self.active = True
            self.text = text

        @discord.ui.button(label="View More Search Results", style=discord.ButtonStyle.blurple)
        async def search(self, interaction: discord.Interaction, button: discord.ui.button):
            url = f'https://api.myanimelist.net/v2/anime?offset=5&q={self.text}&limit=10'
            await interaction.response.defer()
            result = responses.makeMALCall(url)
            data = result['data']
            for i in data:
                title = i['node']['title']
                id = i['node']['id']
                img = i['node']['main_picture']['medium']

                resp = f'**Title: {title}**\nID: {id}\n{img}'

                await interaction.followup.send(resp, ephemeral = True)

    class getRecs(discord.ui.View):
        def __init__(self, recs):
            super().__init__()
            self.value = None
            self.active = True
            self.recs = recs

        @discord.ui.button(label="Get Similar Anime", style=discord.ButtonStyle.green)
        async def recs(self, interaction: discord.Interaction, button: discord.ui.button):
            await interaction.response.defer()
            for i in self.recs:
                title = i['node']['title']
                id = i['node']['id']
                img = i['node']['main_picture']['medium']

                resp = f'**Title: {title}**\nID: {id}\n{img}'
                view2 = getDetails(id)
                await interaction.followup.send(resp, view = view2, ephemeral = True)

    class getDetails(discord.ui.View):

        def __init__(self, id):
            super().__init__()
            self.value = None
            self.active = True
            self.id = id




        @discord.ui.button(label="Get Anime Details", style=discord.ButtonStyle.green)
        async def details(self, interaction: discord.Interaction, button: discord.ui.button):
            url = f'https://api.myanimelist.net/v2/anime/{self.id}?fields=id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,status,genres,my_list_status,num_episodes,start_season,broadcast,source,average_episode_duration,rating,pictures,background,related_anime,related_manga,recommendations,studios,statistics0'
            await interaction.response.defer()
            result = responses.makeMALCall(url)
            data = result

            status = 'Not yet aired'
            if(data['status'] == 'finished_airing'):
                status = 'Finished Airing'
            elif(data['status'] == "currently_airing"):
                status = "Currently Airing"

            age_rating = "Unknown"
            if data['rating'] == 'pg':
                age_rating = 'PG - Children'
            elif data['rating'] == 'pg_13':
                age_rating = 'PG 13 - Teens 13 and Older'
            elif data['rating'] == 'r':
                age_rating = 'R - 17+ (violence & profanity)'
            elif data['rating'] == 'r+':
                age_rating = 'R+ - Profanity & Mild Nudity'
            elif data['rating'] == 'rx':
                age_rating = 'Rx - Hentai'
            elif data['rating'] == 'g':
                age_rating = 'G - All Ages'

            synopsis = 'Synopsis unavailable'
            if len(data['synopsis']) <= 1500:
                synopsis = data['synopsis']
            else:
                synopsis = data['synopsis'][0:1450] + '... Full synopsis available on MAL.'

            genres = ''
            for i in data['genres']:
                genres += i['name'] + ', '

            genres = genres[0:len(genres)-2]


            recommendations = data['recommendations']

            view = getRecs(recommendations)
            await interaction.followup.send(f"**Title: {data["title"]}**\nID: {data['id']}\n\nAlternative Titles:\nEnglish: {data['alternative_titles']['en']}\njapanese:{data['alternative_titles']['ja']}\n\nMAL Rating: {data['mean']}/10\nMAL Rank: #{data['rank']}\n\nStart Date: {data['start_date']}\nStatus: {status}\nNumber of Episodes: {data['num_episodes']}\n\nAge Rating: {age_rating}\nGenres: {genres}\n\nSynopsis:\n{synopsis}\n{data['main_picture']['large']}", view=view)















    bot.run(TOKEN)