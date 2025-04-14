import os
from discord.ext import commands, tasks
import responses
import sqlite3
from dotenv import load_dotenv
import random
from datetime import datetime, timezone, timedelta
import asyncio



def run_discord_bot(discord):
    load_dotenv()
    TOKEN = os.getenv('BOT_KEY')

    
    app_commands = discord.app_commands
    bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())
    bot.remove_command("help")
    connection = sqlite3.connect("mydata.db")
    cursor = connection.cursor()

    @bot.event
    async def on_ready():
        print(f"{bot.user} is ready")
        try:
            synced = await bot.tree.sync()
        except Exception as e:
            print(e)

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY,
                username TEXT UNIQUE
            )""")
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS Data (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                data_value TEXT,
                data_value2 INTEGER,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )""")

        print("Initialized database")
        
        check_inactive_channels.start()
        

    chat = responses.create_chat()
    HISTORY_FILE = "conversation_history.txt"
    MAX_LINES = 300  # Set this to the max number of lines you want in the file


    @tasks.loop(minutes=20)
    async def check_inactive_channels():
        now = datetime.now(timezone.utc)
        for channel_id, last_message_time in monitored_channels.items():
            # print(now - last_message_time)
            if now - last_message_time > timedelta(minutes=120):
                channel = bot.get_channel(channel_id)
                if channel:
                    global chat
                    chat = responses.create_chat
                    await channel.send("<@&1341216663416340533> WAKEY WAKEY. You better start talking or I'll MAKE you talk.")


    def save_history(username, user_message, bot_response):
        # Read the existing lines
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []

        # Append the new messages
        lines.append(f"{username}: {user_message}\n")
        lines.append(f"Bot: {bot_response}\n")

        # Trim to the last MAX_LINES
        if len(lines) > MAX_LINES:
            lines = lines[-MAX_LINES:]

        # Write back to the file
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)


    


    @bot.event
    async def on_message(message):
        if message.author != bot.user:
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)

            print(f"{username} said: '{user_message}' ({channel})")
            if user_message[0] != '$':
                if bot.user in message.mentions:
                    resp = chat.send_message(f"Respond relevantly to this chat message from a chatter,{username}, talking to you (<@1232601971870138409> is your ping, ignore it and avoid using it in your message): {user_message}").text
                    await message.reply(resp)
                    save_history(username, user_message, resp)
                elif message.reference is not None:
                    replied_message = await message.channel.fetch_message(message.reference.message_id)
                    if replied_message.author == bot.user:
                        resp = chat.send_message(f"Respond relevantly to this chat message from a chatter, {username}, talking to you): {user_message}").text
                        await message.reply(resp)
                        save_history(username, user_message, resp)
                elif message.guild is None:
                    resp = chat.send_message(f"Respond relevantly to this chat message (it's a dm to you): {user_message}").text
                    await message.author.send(resp)
                    save_history(username, user_message, resp)
                else:
                    rannum = random.randint(1,300)
                    if rannum >= 301:
                        resp = chat.send_message(f"Try to respond relevantly to this chat message from {username}, based on the discord chat history (They are usually not talking to you): {user_message}").text
                        await message.reply(resp)
                        save_history(username, user_message, resp)
                    elif rannum == -1:
                        resp = chat.send_message(f"Make up a random reason to timeout this chatter, {username}, for 5 minutes based on their message: {user_message}").text
                        await message.reply(resp)
                        await message.author.timeout(timedelta(minutes=5),reason = resp)
                        save_history(username, user_message, resp)
                    else:
                        save_history(username, user_message, "")
                        
            else:
                save_history(username, user_message, "")
                await bot.process_commands(message)
        if message.channel.id in monitored_channels:
            monitored_channels[message.channel.id] = datetime.now(timezone.utc)

    monitored_channels = {}
    @bot.command()
    async def monitor(ctx):
        monitored_channels[ctx.channel.id] = datetime.now(timezone.utc)
        await ctx.send(f"I'm monitoring this channel for inactivity, you better start yapping you BUMS.")
    @bot.tree.command(name='monitor', description='List commands (non-slash commands)')
    async def monitor(interaction: discord.Interaction):
        try:
            await interaction.response.send_message("I'm monitoring this channel for inactivity, you better start yapping you BUMS.")
        except Exception as e:
            print(e)
            await interaction.response.send_message("Failed")


    #Reset chat bot
    @bot.command()
    async def resetchat(ctx):
        global chat
        chat = responses.create_chat
        await ctx.send("My memory is wiped 🥀")



    #Commands for inserting/getting from database
    def insert_data(user_id, data, data2):
        cursor.execute('INSERT INTO Data (user_id, data_value, data_value2) VALUES (?, ?, ?)', (user_id, data, data2))
        connection.commit()

    def update_data_2(user_id, data, new_data_2):
        cursor.execute('''
            UPDATE Data 
            SET data_value2 = ? 
            WHERE user_id = ? AND data_value = ?
        ''', (new_data_2, user_id, data))
        connection.commit()

    def get_data(user_id):
        cursor.execute('SELECT data_value, data_value2 FROM Data WHERE user_id = ?', (user_id,))
        return cursor.fetchall()

    def delete_data(user_id, data_value):
        cursor.execute('DELETE FROM Data WHERE user_id = ? AND data_value = ?', (user_id, data_value))
        connection.commit()

    def sort_data_by_average_data_2_for_users(user_ids):
        query = '''
            SELECT data_value, AVG(data_value2) AS avg_data2
            FROM Data
            WHERE user_id IN ({})
            GROUP BY data_value
            ORDER BY avg_data2 DESC
        '''.format(','.join('?' * len(user_ids)))
        cursor.execute(query, user_ids)
        return cursor.fetchall()



    @bot.command()
    async def mylist(ctx):
        list = get_data(ctx.author.id)

        sorted_list = sorted(list, key=lambda x: x[1], reverse=True)

        #Make list (1st page)
        description = ''
        for i in range(len(sorted_list)):
            if i == 15:
                break
            else:
                description += f'**#{i + 1}: ** {sorted_list[i][0]} - **Score: {sorted_list[i][1]}**\n'

        embed = discord.Embed(
            color=discord.Color.dark_teal(),
            description=description,
            title=f"{ctx.author}'s Top Anime"
        )

        embed.set_thumbnail(url=ctx.author.avatar.url)

        if len(sorted_list) > 15:
            view1 = listView1(sorted_list, ctx.author, 0)
            await ctx.reply(embed=embed, view=view1)
        else:
            await ctx.reply(embed=embed)

    @bot.command()
    async def topserver(ctx):

        activeList = []

        for i in ctx.guild.members:
            if len(get_data(i.id)) > 0:
                activeList.append(i.id)

        sorted_list = (sort_data_by_average_data_2_for_users(activeList))

        # Make list (1st page)
        description = ''
        for i in range(len(sorted_list)):
            if i == 15:
                break
            else:
                description += f'**#{i + 1}: ** {sorted_list[i][0]} - **Average Score: {sorted_list[i][1]}**\n'

        embed = discord.Embed(
            color=discord.Color.purple(),
            description=description,
            title=f"{ctx.guild}'s Top 15 Anime"
        )

        embed.set_thumbnail(url=ctx.guild.icon.url)

        await ctx.reply(embed=embed)






    class listView1(discord.ui.View):
        def __init__(self, sorted_list, ctx, num):
            super().__init__()
            self.value = None
            self.active = True
            self.sorted_list = sorted_list
            self.ctx = ctx
            self.num = num

        @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
        async def next(self, interaction: discord.Interaction, button: discord.ui.button):
            self.num += 15
            description = ''
            for i in range(len(self.sorted_list)):
                if (i + self.num) % 15 == 0 and i != 0 or (i + self.num) >= len(self.sorted_list):
                    break
                else:
                    description += f'**#{self.num + i + 1}: ** {self.sorted_list[self.num + i][0]} - **Score: {self.sorted_list[self.num + i][1]}**\n'

            embed = discord.Embed(
                color=discord.Color.dark_teal(),
                description=description,
                title=f"{self.ctx}'s Top Anime"
            )

            embed.set_thumbnail(url=self.ctx.avatar.url)

            print(self.num)

            if len(self.sorted_list) - self.num <= 15:
                await interaction.response.edit_message(embed=embed,
                                                        view=listView2(self.sorted_list, self.ctx, self.num))
            else:
                await interaction.response.edit_message(embed=embed,
                                                        view=listView3(self.sorted_list, self.ctx, self.num))

    class listView2(discord.ui.View):
        def __init__(self, sorted_list, ctx, num):
            super().__init__()
            self.value = None
            self.active = True
            self.sorted_list = sorted_list
            self.ctx = ctx
            self.num = num

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
        async def prev(self, interaction: discord.Interaction, button: discord.ui.button):
            self.num -= 15
            description = ''
            for i in range(len(self.sorted_list)):
                if (i + self.num) % 15 == 0 and i != 0 or (i + self.num) >= len(self.sorted_list):
                    break
                else:
                    description += f'**#{self.num + i + 1}: ** {self.sorted_list[self.num + i][0]} - **Score: {self.sorted_list[self.num + i][1]}**\n'

            embed = discord.Embed(
                color=discord.Color.dark_teal(),
                description=description,
                title=f"{self.ctx}'s Top Anime"
            )

            pagenum = (self.num -1) // 15 + 1
            embed.set_thumbnail(url=self.ctx.avatar.url)

            if self.num == 0:
                await interaction.response.edit_message(embed=embed,
                                                        view=listView1(self.sorted_list, self.ctx, self.num))
            else:
                await interaction.response.edit_message(embed=embed,
                                                        view=listView3(self.sorted_list, self.ctx, self.num))

    class listView3(discord.ui.View):
        def __init__(self, sorted_list, ctx, num):
            super().__init__()
            self.value = None
            self.active = True
            self.sorted_list = sorted_list
            self.ctx = ctx
            self.num = num


        @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
        async def prev(self, interaction: discord.Interaction, button: discord.ui.button):
            self.num -= 15
            description = ''
            for i in range(len(self.sorted_list)):
                if (i + self.num) % 15 == 0 and i != 0 or (i + self.num) >= len(self.sorted_list):
                    break
                else:
                    description += f'**#{self.num + i + 1}: ** {self.sorted_list[self.num + i][0]} - **Score: {self.sorted_list[self.num + i][1]}**\n'

            embed = discord.Embed(
                color=discord.Color.dark_teal(),
                description=description,
                title=f"{self.ctx}'s Top Anime"
            )

            pagenum = (self.num - 1) // 15 + 1
            embed.set_thumbnail(url=self.ctx.avatar.url)

            if self.num == 0:
                await interaction.response.edit_message(embed=embed,
                                                        view=listView1(self.sorted_list, self.ctx, self.num))
            else:
                await interaction.response.edit_message(embed=embed,
                                                        view=listView3(self.sorted_list, self.ctx, self.num))

        @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
        async def next(self, interaction: discord.Interaction, button: discord.ui.button):
            self.num += 15
            description = ''
            for i in range(len(self.sorted_list)):
                if (i + self.num) % 15 == 0 and i != 0 or (i + self.num) >= len(self.sorted_list):
                    break
                else:
                    description += f'**#{self.num + i + 1}: ** {self.sorted_list[self.num + i][0]} - **Score: {self.sorted_list[self.num + i][1]}**\n'

            embed = discord.Embed(
                color=discord.Color.dark_teal(),
                description=description,
                title=f"{self.ctx}'s Top Anime"
            )

            pagenum = (self.num -1) // 15 + 1
            embed.set_thumbnail(url=self.ctx.avatar.url)

            if len(self.sorted_list) - self.num <= 15:
                await interaction.response.edit_message(embed=embed,
                                                        view=listView2(self.sorted_list, self.ctx, self.num))
            else:
                await interaction.response.edit_message(embed=embed,
                                                        view=listView3(self.sorted_list, self.ctx, self.num))

    @bot.command()
    async def addanime(ctx):
        try:
            rating = int(ctx.message.content[len(ctx.message.content) - 2:])
            if rating > 10 or rating < 1:
                await ctx.reply("Wrong input")
                return
        except Exception as e:
            await ctx.reply("Wrong input")
            return

        try:
            anime_id = int(ctx.message.content[10:len(ctx.message.content) - 2])
            title = responses.makeMALCall(f'https://api.myanimelist.net/v2/anime/{anime_id}?fields=title')['title']
        except Exception as e:
            await ctx.reply("Wrong input")
            return

        list = get_data(ctx.author.id)

        for i in list:
            print(i[0])
            if i[0] == title:
                print("Already here")
                update_data_2(ctx.author.id, title, rating)
                await ctx.reply(f"Updated your rating for '{title}'")
                return

        insert_data(ctx.author.id, title, rating)
        await ctx.reply(f"Added '{title}' to your list")

    @bot.command()
    async def removeanime(ctx):
        try:
            target_id = int(ctx.message.content[13:])
            title = responses.makeMALCall(f'https://api.myanimelist.net/v2/anime/{target_id}?fields=title')['title']
        except Exception as e:
            print(e)
            await ctx.reply("Invalid input")
            return

        list = get_data(ctx.author.id)
        for i in list:
            if i[0] == title:
                delete_data(ctx.author.id, title)
                await ctx.reply(f"Removed {title} from your list.")
                return
        await ctx.reply("Title not found in your list")
        return

    # Anime search commands
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
        await ctx.reply("If you didn't find what you were looking for, click here to get more search results",
                        view=view)

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

                await interaction.followup.send(resp, ephemeral=True, view=getDetails(id))

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
                await interaction.followup.send(resp, view=view2, ephemeral=True)

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
            if (data['status'] == 'finished_airing'):
                status = 'Finished Airing'
            elif (data['status'] == "currently_airing"):
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

            genres = genres[0:len(genres) - 2]

            rank = ""
            try:
                rank = data["rank"]
            except Exception as e:
                rank = "N/A"

            recommendations = data['recommendations']

            view = getRecs(recommendations)
            print(result)
            await interaction.followup.send(
                f'**Title: {data["title"]}**\nID: {data["id"]}\n\nAlternative Titles:\nEnglish: {data["alternative_titles"]["en"]}\nJapanese: {data["alternative_titles"]["ja"]}\n\nMAL Rating: {data["mean"]}/10\nMAL Rank: #{rank}\n\nStart Date: {data["start_date"]}\nStatus: {status}\nNumber of Episodes: {data["num_episodes"]}\n\nAge Rating: {age_rating}\nGenres: {genres}\n\nSynopsis:\n{synopsis}\n{data["main_picture"]["large"]}',
                view=view)

    @bot.tree.command(name='searchanime', description='Search for an anime')
    @app_commands.describe(input="What do you want to search?")
    async def searchanime(interaction: discord.Interaction, input: str):
        await interaction.response.defer()
        url = f'https://api.myanimelist.net/v2/anime?q={input}&limit=5'
        result = responses.makeMALCall(url)
        data = result['data']
        await interaction.followup.send("Here are your top search results: ")
        for i in data:
            title = i['node']['title']
            id = i['node']['id']
            img = i['node']['main_picture']['medium']

            resp = f'**Title: {title}**\nID: {id}\n{img}'
            view2 = getDetails(id)
            await interaction.followup.send(resp, view=view2)
        view = searchMenu(input)
        await interaction.followup.send(
            "If you didn't find what you were looking for, click here to get more search results",
            view=view)

    @bot.command()
    async def searchmanga(ctx):
        input = ctx.message.content[13:]
        url = f'https://api.myanimelist.net/v2/manga?q={input}&limit=5'
        result = responses.makeMALCall(url)
        data = result['data']
        await ctx.reply("Here are your top search results: ")
        for i in data:
            title = i['node']['title']
            id = i['node']['id']
            img = i['node']['main_picture']['medium']

            resp = f'**Title: {title}**\nID: {id}\n{img}'
            view2 = getDetails2(id)
            await ctx.send(resp, view=view2)
        view = searchMenu2(input)
        await ctx.reply("If you didn't find what you were looking for, click here to get more search results",
                        view=view)

    class searchMenu2(discord.ui.View):
        def __init__(self, text):
            super().__init__()
            self.value = None
            self.active = True
            self.text = text

        @discord.ui.button(label="View More Search Results", style=discord.ButtonStyle.blurple)
        async def search(self, interaction: discord.Interaction, button: discord.ui.button):
            url = f'https://api.myanimelist.net/v2/manga?offset=5&q={self.text}&limit=10'
            await interaction.response.defer()
            result = responses.makeMALCall(url)
            data = result['data']
            for i in data:
                title = i['node']['title']
                id = i['node']['id']
                img = i['node']['main_picture']['medium']

                resp = f'**Title: {title}**\nID: {id}\n{img}'

                await interaction.followup.send(resp, ephemeral=True)

    class getRecs2(discord.ui.View):
        def __init__(self, recs):
            super().__init__()
            self.value = None
            self.active = True
            self.recs = recs

        @discord.ui.button(label="Get Similar Manga", style=discord.ButtonStyle.green)
        async def recs(self, interaction: discord.Interaction, button: discord.ui.button):
            await interaction.response.defer()
            for i in self.recs:
                title = i['node']['title']
                id = i['node']['id']
                img = i['node']['main_picture']['medium']

                resp = f'**Title: {title}**\nID: {id}\n{img}'
                view2 = getDetails2(id)
                await interaction.followup.send(resp, view=view2, ephemeral=True)

    class getDetails2(discord.ui.View):

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
            if (data['status'] == 'finished_airing'):
                status = 'Finished Airing'
            elif (data['status'] == "currently_airing"):
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

            genres = genres[0:len(genres) - 2]

            rank = ""
            try:
                rank = data["rank"]
            except Exception as e:
                rank = "N/A"

            recommendations = data['recommendations']

            view = getRecs(recommendations)
            print(result)
            await interaction.followup.send(
                f'**Title: {data["title"]}**\nID: {data["id"]}\n\nAlternative Titles:\nEnglish: {data["alternative_titles"]["en"]}\nJapanese: {data["alternative_titles"]["ja"]}\n\nMAL Rating: {data["mean"]}/10\nMAL Rank: #{rank}\n\nStart Date: {data["start_date"]}\nStatus: {status}\nNumber of Episodes: {data["num_episodes"]}\n\nAge Rating: {age_rating}\nGenres: {genres}\n\nSynopsis:\n{synopsis}\n{data["main_picture"]["large"]}',
                view=view)

    @bot.tree.command(name='searchmanga', description='Search for a manga')
    @app_commands.describe(input="What do you want to search?")
    async def searchmanga(interaction: discord.Interaction, input: str):
        await interaction.response.defer()
        url = f'https://api.myanimelist.net/v2/manga?q={input}&limit=5'
        result = responses.makeMALCall(url)
        data = result['data']
        await interaction.followup.send("Here are your top search results: ")
        for i in data:
            title = i['node']['title']
            id = i['node']['id']
            img = i['node']['main_picture']['medium']

            resp = f'**Title: {title}**\nID: {id}\n{img}'
            view2 = getDetails(id)
            await interaction.followup.send(resp, view=view2)
        view = searchMenu2(input)
        await interaction.followup.send(
            "If you didn't find what you were looking for, click here to get more search results",
            view=view)

    @bot.command()
    async def topMAL(ctx):
        url = f'https://api.myanimelist.net/v2/anime/ranking?ranking_type=all&limit=5'
        result = responses.makeMALCall(url)
        data = result['data']
        await ctx.reply("Here are the top 5 anime on MAL: ")
        count = 1
        for i in data:
            title = i['node']['title']
            id = i['node']['id']
            img = i['node']['main_picture']['medium']
            resp = f'**#{count}: {title}**\nID: {id}\n{img}'
            view2 = getDetails(id)
            await ctx.send(resp, view=view2)
            count += 1
        view = searchMenu3()
        await ctx.reply("Click here to see the next 15 top anime of all time",
                        view=view)

    class searchMenu3(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.value = None
            self.active = True

        @discord.ui.button(label="View More Results", style=discord.ButtonStyle.blurple)
        async def search(self, interaction: discord.Interaction, button: discord.ui.button):
            url = f'https://api.myanimelist.net/v2/anime/ranking?ranking_type=all&offset=5&limit=15'
            await interaction.response.defer()
            result = responses.makeMALCall(url)
            data = result['data']
            count = 6
            for i in data:
                title = i['node']['title']
                id = i['node']['id']
                img = i['node']['main_picture']['medium']
                resp = f'**#{count}: {title}**\nID: {id}\n{img}'
                count += 1
                view = getDetails(id)
                await interaction.followup.send(resp, ephemeral=True, view=view)

    @bot.tree.command(name='mylist', description="View the your anime list")
    async def mylist(interaction: discord.Interaction):
        list = get_data(interaction.user.id)

        sorted_list = sorted(list, key=lambda x: x[1], reverse=True)

        # Make list (1st page)
        description = ''
        for i in range(len(sorted_list)):
            if i == 15:
                break
            else:
                description += f'**#{i + 1}: ** {sorted_list[i][0]} - **Score: {sorted_list[i][1]}**\n'

        embed = discord.Embed(
            color=discord.Color.dark_teal(),
            description=description,
            title=f"{interaction.user}'s Top Anime"
        )

        embed.set_thumbnail(url=interaction.user.avatar.url)


        if len(sorted_list) > 15:
            view1 = listView1(sorted_list, interaction.user, 0)
            await interaction.response.send_message(embed=embed, view=view1)
        else:
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name='topserver', description="View the server's top anime")
    @app_commands.describe()
    async def topserver(interaction: discord.Interaction):

        activeList = []

        for i in interaction.guild.members:
            if len(get_data(i.id)) > 0:
                activeList.append(i.id)

        sorted_list = (sort_data_by_average_data_2_for_users(activeList))

        # Make list (1st page)
        description = ''
        for i in range(len(sorted_list)):
            if i == 15:
                break
            else:
                description += f'**#{i + 1}: ** {sorted_list[i][0]} - **Average Score: {sorted_list[i][1]}**\n'

        embed = discord.Embed(
            color=discord.Color.purple(),
            description=description,
            title=f"{interaction.guild}'s Top 15 Anime"
        )

        embed.set_thumbnail(url=interaction.guild.icon.url)

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name='topmal', description="View the server's top anime")
    async def topmal(interaction: discord.Interaction):
        url = f'https://api.myanimelist.net/v2/anime/ranking?ranking_type=all&limit=5'
        await interaction.response.defer()
        result = responses.makeMALCall(url)
        data = result['data']
        await interaction.followup.send("Here are the top 5 anime on MAL: ")
        count = 1
        for i in data:
            title = i['node']['title']
            id = i['node']['id']
            img = i['node']['main_picture']['medium']
            resp = f'**#{count}: {title}**\nID: {id}\n{img}'
            view2 = getDetails(id)
            await interaction.followup.send(resp, view=view2)
            count += 1
        view = searchMenu3()
        await interaction.followup.send("Click here to see the next 15 top anime of all time",
                        view=view)

    @bot.tree.command(name='addanime', description="Add an anime to your list")
    @app_commands.describe(animeid="The ID of the anime you want to add. Use $searchanime if you don't know it.", rating = "The rating of the show. It must be from 1-10")
    async def addanime(interaction: discord.Interaction, animeid: int, rating: int):

        if rating > 10 or rating < 1:
            await interaction.response.send_message("Rating must be from 1-10")
            return

        try:
            title = responses.makeMALCall(f'https://api.myanimelist.net/v2/anime/{animeid}?fields=title')['title']
        except Exception as e:
            await interaction.response.send_message("An error has occured.")
            return

        list = get_data(interaction.id)

        for i in list:
            print(i[0])
            if i[0] == title:
                print("Already here")
                update_data_2(interaction.id, title, rating)
                await interaction.response.send_message(f"Updated your rating for '{title}'")
                return

        insert_data(interaction.id, title, rating)
        await interaction.response.send_message(f"Added '{title}' to your list")

    @bot.tree.command(name='removeanime', description="Remove an anime title from your list")
    @app_commands.describe(animeid="The ID of the anime you want to remove. Use $searchanime if you don't know it.")
    async def removeanime(interaction: discord.Interaction, animeid: int):

        try:
            title = responses.makeMALCall(f'https://api.myanimelist.net/v2/anime/{animeid}?fields=title')['title']
        except Exception as e:
            await interaction.response.send_message("Title not found in your list")
            return

        list = get_data(interaction.id)
        for i in list:
            if i[0] == title:
                delete_data(interaction.id, title)
                await interaction.response.send_message(f"Removed {title} from your list.")
                return
        await interaction.response.send_message("Title not found in your list")
        return

    @bot.tree.command(name='askgojo', description='Responds as Gojo Satoru from Jujutsu Kaisen')
    @app_commands.describe(input="What do you want to ask/tell Gojo?")
    async def askgojo(interaction: discord.Interaction, input: str):
        try:
            await interaction.response.defer()
            resp = responses.ai_response("askgojo", input, None)
            await interaction.followup.send(resp)
        except Exception as e:
            print(e)
            await interaction.response.send_message("Failed")


    @bot.tree.command(name='help', description='List commands (non-slash commands)')
    async def help(interaction: discord.Interaction):
        try:
            await interaction.response.send_message("**Commands:**\n\n**$searchanime {Your query}:** Search for an anime title\n**$topMAL:** Gives the top rated anime on MyAnimeList\n**$mylist:** Sends your list of anime\n**$addanime {animeid}:** Adds an anime to your list based on the anime id (use $searchanime to find it)\n**$removeanime {animeid}: **Removes an anime from your list based on the anime id\n**$topserver:** Takes the average rating of all users on the current server to return the top 15 highest rated anime.")
        except Exception as e:
            print(e)
            await interaction.response.send_message("Failed")

    @bot.command()
    async def help(ctx):
        await ctx.message.reply("**Commands:**\n\n**$searchanime {Your query}:** Search for an anime title\n**$topMAL:** Gives the top rated anime on MyAnimeList\n**$mylist:** Sends your list of anime\n**$addanime {animeid}:** Adds an anime to your list based on the anime id (use $searchanime to find it)\n**$removeanime {animeid}: **Removes an anime from your list based on the anime id\n**$topserver:** Takes the average rating of all users on the current server to return the top 15 highest rated anime.")

    @bot.command()
    async def askgojo(ctx):
        try:
            input = ctx.message.content[10:]
            resp = responses.ai_response("askgojo", input, None)
            await ctx.message.reply(resp)
        except Exception as e:
            print(e)
            await ctx.message.reply("Please check your input and try again")

    
    bot.run(TOKEN)
