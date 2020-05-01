import discord
import re
import mysql.connector
from mysql.connector import Error
import urllib.request
import subprocess
import time
import requests
import random
from discord.utils import get
import discord.utils
from datetime import datetime
from discord import Webhook, RequestsWebhookAdapter, File
import csv
from shutil import copyfile


client = discord.Client(heartbeat_timeout=600)
hangman_game_state = {}
trivia_game_state = {} 
hangman_initial = "|---|\n|   |\n|   \n|   \n|   \n|   \n|----\n"
bad_guess = [""] * 8
bad_guess[0] = hangman_initial
bad_guess[1] = "|---|\n|   |\n|   😧\n|   \n|   \n|   \n|----\n"
bad_guess[2] = "|---|\n|   |\n|   🤬\n|   |\n|   \n|   \n|----\n"
bad_guess[3] = "|---|\n|   |\n|   😭\n|  /|\n|   \n|   \n|----\n"
bad_guess[4] = "|---|\n|   |\n|   😨\n|  /|\\ \n|   \n|   \n|----\n"
bad_guess[5] = "|---|\n|   |\n|   🥺\n|  /|\\ \n|   |\n|   \n|----\n"
bad_guess[6] = "|---|\n|   |\n|   😬\n|  /|\\ \n|   |\n|  /\n|----\n"
bad_guess[7] = "|---|\n|   |\n|   😵\n|  /|\\ \n|   |\n|  /\\ \n|----\n"
screwball_answers = ["I don't give a shit.", "Fuck off.", "Hell to the yes!", "Clear as mud.", "No, so stop asking.", "That's the dumbest question I've ever heard.", "I wouldn't if I were you.", "Ever heard of the Darwin award?", "Yeah, I guess.", "Definitely. Probably. Maybe.", "Absolutely.", "Fuck, no!", "Are you insane?", "What kind of question is that?", "Nah.", "Nope.", "Yeah, sure, why not?", "I dunno.", "Do I look like a psychic?", "Zeus says yes.", "Zeus says no.", "The stars predict that this won't happen.", "My horoscope reading says probably.", "Did a little voice tell you to ask that?", "Wait here, I'll get the men in white coats on the line.", "No way.", "Yes way.", "Aw, hell nah!", "Yeah yeah yeah.", "No! What made you think that was a possibility?", "DOES NOT COMPUTE", "PC Load Letter", "What the fuck does that mean?", "Affirmative.", "How long did that question take you to think up?", "I'll have fries with that.", "No. Just no.", "The lie detector test says that is a lie.", "The lie detector test says that is the truth.", "Yeah, whatever.", "Who knows? Ask someone smart.", "Negative.", "Uh huh.", "Uh-uh.", "-nods-", "-shakes head-", "-shrugs-", "Outlook not so good. Try GMail instead.", "Did you say something? Was I supposed to be listening?", "WHAT? OKAY! YEAH!", "Absolutely nothing, which is what you are about to become.", "My crystal screwball says...NO SIGNAL.", "The tarot card reading says...oh man, you are SCREWED!", "YES && NO || YES && !NO", "Does a bear shit in the woods?", "Is the Pope Catholic?", "Did you check Google first?", "Let me Google that for you...no, I'm even lazier than you!", "Shit shit shit RUN!", "Damn it, the coronavirus has my signals crossed...-violent coughing, flushes without washing hands-", "ERROR: Satellite out of alignment. Try again later.", "Do I look like a psychic?", "Yeah...no.","No...yeah.", "Forecast hazy, try renewable energy.", "Sorry, OUT OF ORDER.", "That divides by zero. If I answer that question, the universe will implode.", "I'd answer, but the B.O. is so strong from you I can't talk without gagging.", "It's the same, but different.", "You don't want to know.", "The answer my friend, is blowing in the wind, and it's coming from the Taco Bell I had earlier.", "What the hell is wrong with you?", "Yes, I just lied.", "No, I just lied.", "I don't care.", "How the heck should I know?", "Ask the genius who wrote this stupid bot.", "Go away, kid, you bother me.", "If a frog had wings, then he wouldn't bump his ass.", r"\"I see,\" said the blind man as he scratched his wooden leg.", "Here's a quarter, call someone who cares and ask them.", "NOOOOO!!!", "I guess?", "Maybe not.", "Who cares?", "I see the Grim for you." ]
used_hint = { } 
guessed_letters = {} 
crystal_game_state = { }
async def get_word(number_of_letters):
    database = "AuthorMaton"
    word_pattern = ""
    for x in range(1,number_of_letters):
        word_pattern = word_pattern + "_"
    sql_query = """SELECT Word,Definitions FROM DictionaryDefs WHERE Word LIKE %s AND Language='English' ORDER BY RAND( ) LIMIT 1;"""
    params = (word_pattern,)
    try:
        connection = mysql.connector.connect(host='localhost', database=database, user='jwoleben', password='nerdvana4097')
        cursor = connection.cursor()
        result = cursor.execute(sql_query, params)
        records = cursor.fetchall()
        await log_message("Returned " + str(records))
        return records
    except mysql.connector.Error as error:
        await log_message("Database error! " + str(error))
        return None
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()    
async def log_message(log_entry):
    current_time_obj = datetime.now()
    current_time_string = current_time_obj.strftime("%b %d, %Y-%H:%M:%S.%f")
    print(current_time_string + " - " + log_entry, flush = True)
    
async def commit_sql(sql_query, params = None):
    await log_message("Commit SQL: " + sql_query + "\n" + "Parameters: " + str(params))
    try:
        connection = mysql.connector.connect(host='localhost', database='Tricksy', user='jwoleben', password='nerdvana4097')    
        cursor = connection.cursor()
        result = cursor.execute(sql_query, params)
        connection.commit()
        return True
    except mysql.connector.Error as error:
        await log_message("Database error! " + str(error))
        return False
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            
                
async def select_sql(sql_query, params = None):
    await log_message("Select SQL: " + sql_query + "\n" + "Parameters: " + str(params))
    try:
        connection = mysql.connector.connect(host='localhost', database='Tricksy', user='jwoleben', password='nerdvana4097')
        cursor = connection.cursor()
        result = cursor.execute(sql_query, params)
        records = cursor.fetchall()
        await log_message("Returned " + str(records))
        return records
    except mysql.connector.Error as error:
        await log_message("Database error! " + str(error))
        return None
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()

async def execute_sql(sql_query):
    try:
        connection = mysql.connector.connect(host='localhost', database='Tricksy', user='jwoleben', password='nerdvana4097')
        cursor = connection.cursor()
        result = cursor.execute(sql_query)
        return True
    except mysql.connector.Error as error:
        await log_message("Database error! " + str(error))
        return False
    finally:
        if(connection.is_connected()):
            cursor.close()
            connection.close()
            
async def direct_message(message, response):
    channel = await message.author.create_dm()
    await log_message("replied to user " + message.author.name + " in DM with " + response)
    try:
        message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
        for chunk in message_chunks:
            await channel.send(">>> " + chunk)
            time.sleep(1)
        
    except discord.errors.Forbidden:
        await dm_tracker[message.author.id]["commandchannel"].send(">>> You have DMs off. Please reply with =answer <reply> in the server channel.\n" + response)
        
async def post_webhook(channel, name, response, picture):
    temp_webhook = await channel.create_webhook(name='Tricksy')
    await temp_webhook.send(content=response, username=name, avatar_url=picture)
    await temp_webhook.delete() 
    
async def reply_message(message, response):
    if not message.guild:
        channel_name = dm_tracker[message.author.id]["commandchannel"].name
        server_name = str(dm_tracker[message.author.id]["server_id"])
    else:
        channel_name = message.channel.name
        server_name = message.guild.name
        
    await log_message("Message sent back to server " + server_name + " channel " + channel_name + " in response to user " + message.author.name + "\n\n" + response)
    
    message_chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
    for chunk in message_chunks:
        await message.channel.send(">>> " + chunk)
        time.sleep(1)

async def admin_check(userid):
    if (userid != 610335542780887050):
        await log_message(str(userid) + " tried to call an admin message!")
        return False
    else:
        return True
		
async def initialize_dm(author_id):
    global dm_tracker
    dm_tracker[author_id] = { }
    dm_tracker[author_id]["currentcommand"] = " "
    dm_tracker[author_id]["currentfield"] = 0
    dm_tracker[author_id]["fieldlist"] = []
    dm_tracker[author_id]["fielddict"] = []
    dm_tracker[author_id]["server_id"] = 0
    dm_tracker[author_id]["commandchannel"] = 0
    dm_tracker[author_id]["parameters"] = " "

def role_check(role_required, user):
    for role in user.roles:
        if role.id == role_required:
            return True

@client.event
async def on_ready():
    global hangman_game_state
    global used_hint
    global trivia_game_state
    global crystal_game_state
    await log_message("Logged into Discord!")
    
    for guild in client.guilds:
        used_hint[guild.id] = False
        hangman_game_state[guild.id] = {} 
        hangman_game_state[guild.id]["Word"] = ""
        hangman_game_state[guild.id]["Defs"] = ""
        hangman_game_state[guild.id]["Event"] = False
        hangman_game_state[guild.id]["Pattern"] = ""
        hangman_game_state[guild.id]["Hangman"] = ""
        hangman_game_state[guild.id]["BadGuesses"] = 0
        
        trivia_game_state[guild.id] = {} 
        trivia_game_state[guild.id]["Question"] = ""
        trivia_game_state[guild.id]["Answer"] = ""
        trivia_game_state[guild.id]["Difficulty"] = ""
        trivia_game_state[guild.id]["Event"] = False
        trivia_game_state[guild.id]["Endless"] = False
        trivia_game_state[guild.id]["GivenDifficulty"] = ""
        trivia_game_state[guild.id]["GivenCategory"] = ""
        
        guessed_letters[guild.id] = []
        
        crystal_game_state[guild.id] = {}
        crystal_game_state[guild.id]["Event"] = False
        crystal_game_state[guild.id]["Crystal"] = ""
        crystal_game_state[guild.id]["ChallengeUser"] = ""
        
        
@client.event
async def on_guild_join(guild):
    global hangman_game_state
    global used_hint
    global trivia_game_state
    global crystal_game_state
    
    await log_message("Joined guild " + guild.name)
    used_hint[guild.id] = False
    hangman_game_state[guild.id] = {} 
    hangman_game_state[guild.id]["Word"] = ""
    hangman_game_state[guild.id]["Defs"] = ""
    hangman_game_state[guild.id]["Event"] = False
    hangman_game_state[guild.id]["Pattern"] = ""
    hangman_game_state[guild.id]["Hangman"] = ""
    hangman_game_state[guild.id]["BadGuesses"] = 0
    
    trivia_game_state[guild.id] = {} 
    trivia_game_state[guild.id]["Question"] = ""
    trivia_game_state[guild.id]["Answer"] = ""
    trivia_game_state[guild.id]["Difficulty"] = ""
    trivia_game_state[guild.id]["Event"] = False
    trivia_game_state[guild.id]["Endless"] = False
    trivia_game_state[guild.id]["GivenDifficulty"] = ""
    trivia_game_state[guild.id]["GivenCategory"] = ""    
    
    crystal_game_state[guild.id] = {}
    crystal_game_state[guild.id]["Event"] = False
    crystal_game_state[guild.id]["Crystal"] = ""
    crystal_game_state[guild.id]["ChallengeUser"] = ""
    
    guessed_letters[guild.id] = []
    for user in guild:
        records = await select_sql("""SELECT LettersRight, LettersWrong, ChallengesWon, ChallengesLost, HintsUsed, WordsSolved FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""",(str(guild.id),str(user.id)))
        if not records:
            result = await commit_sql("""INSERT INTO Scoreboard (ServerId,UserId,LettersRight, LettersWrong, ChallengesWon, ChallengesLost, HintsUsed, WordsSolved) VALUES (%s, %s, 0,0,0,0,0,0);""",(str(guild.id),str(user.id)))
    for member in guild.members:
        try:
            connection = mysql.connector.connect(host='localhost', database='Tricksy', user='jwoleben', password='nerdvana4097')    
            create_score_entry = """INSERT INTO QuizScores (ServerId, UserId, Score) VALUES(%s, %s, %s);"""   
            score_entry = (str(guild.id), str(member.id), str(0))
            cursor = connection.cursor()
            result = cursor.execute(create_score_entry, score_entry)
            connection.commit()
        except mysql.connector.Error as error:
            await message.channel.send("Database error! " + str(error))   
        finally:
            if(connection.is_connected()):
                cursor.close()
                connection.close()
                
@client.event
async def on_guild_remove(guild):
    await log_message("Left guild " + guild.name)
    
@client.event
async def on_member_join(member):
    await log_message("Member " + member.name + " joined guild " + member.guild.name)
    result = await commit_sql("""INSERT INTO Scoreboard (ServerId,UserId,LettersRight, LettersWrong, ChallengesWon, ChallengesLost, HintsUsed, WordsSolved) VALUES (%s, %s, 0,0,0,0,0,0);""",(str(member.guild.id),str(member.id)));
    records = await select_sql("""SELECT LettersRight, LettersWrong, ChallengesWon, ChallengesLost, HintsUsed, WordsSolved FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""",(str(member.guild.id),str(member.id)))
    if not records:
        result = await commit_sql("""INSERT INTO Scoreboard (ServerId,UserId,LettersRight, LettersWrong, ChallengesWon, ChallengesLost, HintsUsed, WordsSolved) VALUES (%s, %s, 0,0,0,0,0,0);""",(str(member.guild.id),str(member.id)))     
    create_score_entry = """INSERT INTO QuizScores (ServerId, UserId, Score) VALUES(%s, %s, %s);"""   
    score_entry = (str(member.guild.id), str(member.id), str(0))
    result = await commit_sql(create_score_entry, score_entry)    
@client.event
async def on_member_remove(member):
    # await log_message("Member " + member.name + " left guild " + member.guild.name)
    create_score_entry = """DELETE FROM QuizScores Where UserId=%s AND ServerId=%s;"""   
    score_entry = (str(member.id),str(member.guild.id))
    result = await commit_sql(create_score_entry, score_entry)
    # await log_message("Deleted quiz score entry for user.")  
    
    
@client.event
async def on_message(message):
    global hangman_game_state
    global hangman_initial
    global bad_guess
    global used_hint
    global screwball_answers
    global guessed_letters
    global trivia_game_state
    
    if message.author == client.user:
        return
    if message.author.bot:
        return

            
    if message.content.startswith('?'):


        command_string = message.content.split(' ')
        command = command_string[0].replace('?','')
        parsed_string = message.content.replace("?" + command,"")
        parsed_string = re.sub(r"^ ","",parsed_string)
        username = message.author.name
        server_name = message.guild.name

        await log_message("Command " + message.content + " called by " + username + " from " + server_name)
        
        if command == 'help' or command == 'info':
            pass
        elif command == 'importtrivia':
            await reply_message(message, "Loading trivia..")
            with open('/home/jwoleben/easy1.csv', newline='\n') as csvfile:
                equipreader = csv.reader(csvfile, delimiter='|')
                for row in equipreader:
                    result = await commit_sql("INSERT INTO TriviaQuestions (Question,Answer,Difficulty) VALUES (%s, %s, %s);", (row[0], row[1], row[2]))
            with open('/home/jwoleben/easy2.csv', newline='\n') as csvfile:
                equipreader = csv.reader(csvfile, delimiter='|')
                for row in equipreader:
                    result = await commit_sql("INSERT INTO TriviaQuestions (Question,Answer,Difficulty) VALUES (%s, %s, %s);", (row[0], row[1], row[2]))         
            with open('/home/jwoleben/hard1.csv', newline='\n') as csvfile:
                equipreader = csv.reader(csvfile, delimiter='|')
                for row in equipreader:
                    result = await commit_sql("INSERT INTO TriviaQuestions (Question,Answer,Difficulty) VALUES (%s, %s, %s);", (row[0], row[1], row[2]))
            with open('/home/jwoleben/nodifficulty.csv', newline='\n') as csvfile:
                equipreader = csv.reader(csvfile, delimiter='|')
                for row in equipreader:
                    result = await commit_sql("INSERT INTO TriviaQuestions (Category,Question,Answer,Difficulty) VALUES (%s, %s, %s, %s);", (row[0], row[1], row[2],row[3])) 
            with open('/home/jwoleben/medium.csv', newline='\n') as csvfile:
                equipreader = csv.reader(csvfile, delimiter='|')
                for row in equipreader:
                    result = await commit_sql("INSERT INTO TriviaQuestions (Question,Answer,Difficulty) VALUES (%s, %s, %s);", (row[0], row[1], row[2]))
            records = await select_sql("""SELECT COUNT(Question) FROM TriviaQuestions;""")
            await reply_message(message, str(records) + " loaded into database.")
                    
        elif command == 'hangman':
        
            if parsed_string == 'easy':
                number_of_letters = random.randint(3,8)
            elif parsed_string == 'medium':
                number_of_letters = random.randint(9,16)
            elif parsed_string == 'hard':
                number_of_letters = random.randint(17,30)
            elif parsed_string == 'nightmare':
                number_of_letters = random.randint(31,40)
            else:
                number_of_letters = random.randint(3,30)
            records = await get_word(number_of_letters)
            for row in records:
                hangman_word = str(row[0])
                hangman_defs = str(row[1])
            hangman_word = re.sub(r"[^A-Za-z]","", hangman_word)    
            parsed_hangman_word = ""
            for x in hangman_word:
                parsed_hangman_word = parsed_hangman_word + x.upper() + " "
              
            hangman_game_state[message.guild.id]["Word"] = parsed_hangman_word
            hangman_game_state[message.guild.id]["Defs"] = hangman_defs
            hangman_game_state[message.guild.id]["Event"] = True
            if not re.search(r"easy|medium|hard|nightmare",parsed_string):
                parsed_string = "any"
            word_state = ""
            await reply_message(message, "New hangman game started by " + message.author.display_name + " on difficulty mode " + parsed_string + "!")
            for x in range(1,number_of_letters):
                word_state = word_state + "_ "
            hangman_game_state[message.guild.id]["Pattern"] = word_state
            hangman_game_state[message.guild.id]["Hangman"] = hangman_initial
            response = "```" + hangman_initial + "\n\n" + word_state + "```"
            await reply_message(message, response)
        elif command == 'solve':
            if parsed_string.upper() == hangman_game_state[message.guild.id]["Word"].replace(" ",""):
                await reply_message(message, "You successfully guessed the word!")
                records = await select_sql("""SELECT WordsSolved FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""", (str(message.guild.id),str(message.author.id)))
                for row in records:
                    words_solved = int(row[0])
                words_solved = words_solved + 1
                result = await commit_sql("""UPDATE Scoreboard SET WordsSolved=%s WHERE ServerId=%s AND UserId=%s;""",(str(words_solved), str(message.guild.id),str(message.author.id)))
                hangman_game_state[message.guild.id]["Event"] = False
                hangman_game_state[message.guild.id]["BadGuesses"] = 0
                hangman_game_state[message.guild.id]["Word"] = ""
                hangman_game_state[message.guild.id]["Pattern"] = 0
                
                guessed_letters[message.guild.id] = []
                del hangman_game_state[message.guild.id]["ChallengeUser"]
                used_hint[message.guild.id] = False                
            else:
                await reply_message(message, "Nope! Guess again, Hemingway!")
                hangman_game_state[message.guild.id]["BadGuesses"] = hangman_game_state[message.guild.id]["BadGuesses"] + 1
                hangman_game_state[message.guild.id]["Hangman"] = bad_guess[hangman_game_state[message.guild.id]["BadGuesses"]]
                response = "```" + hangman_game_state[message.guild.id]["Hangman"] + "\n\n" + hangman_game_state[message.guild.id]["Pattern"] + "```"
                await reply_message(message, response)
                if hangman_game_state[message.guild.id]["BadGuesses"] > 6:
                    await reply_message(message, "Too many bad guesses! The word was " + hangman_game_state[message.guild.id]["Word"] + "!")
                    hangman_game_state[message.guild.id]["Event"] = False
                    hangman_game_state[message.guild.id]["BadGuesses"] = 0
                    hangman_game_state[message.guild.id]["Word"] = ""
                    hangman_game_state[message.guild.id]["Pattern"] = 0
                    guessed_letters[message.guild.id] = []
                    del hangman_game_state[message.guild.id]["ChallengeUser"]
                    used_hint[message.guild.id] = False                
        elif command == 'guess':
            if not parsed_string:
                await reply_message(message, "Try guessing a letter!")
                return
            try:
                hangman_game_state[message.guild.id]["ChallengeUser"]
                if hangman_game_state[message.guild.id]["ChallengeUser"] != message.author:
                    await reply_message(message, "You weren't challenged! Take a hike!")
                    return
            except:
                pass
            if not hangman_game_state[message.guild.id]["Event"]:
                await reply_message(message, "No game is running!")
                return
            if parsed_string.upper() in guessed_letters[message.guild.id]:
                await reply_message(message, "That letter has already been guessed!")
                return
            guessed_letters[message.guild.id].append(parsed_string.upper())
            if parsed_string.upper() in hangman_game_state[message.guild.id]["Word"]:
                counter = 0
                new_pattern = ""
                for x in hangman_game_state[message.guild.id]["Word"]:
                
                    if x == parsed_string.upper():
                        new_pattern = new_pattern + x
                    elif hangman_game_state[message.guild.id]["Pattern"][counter] == '_':
                        new_pattern = new_pattern + '_'
                    elif hangman_game_state[message.guild.id]["Pattern"][counter] == ' ':
                        new_pattern = new_pattern + ' '
                    else:
                        new_pattern = new_pattern + hangman_game_state[message.guild.id]["Pattern"][counter]
                    counter = counter + 1
                hangman_game_state[message.guild.id]["Pattern"] = new_pattern
                await reply_message(message, "Yes! The letter " + parsed_string.upper() + " is in the word!")
                response = "```" + hangman_game_state[message.guild.id]["Hangman"] + "\n\n" + new_pattern + "```"
                await reply_message(message, response)
                records = await select_sql("""SELECT LettersRight FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""",(str(message.guild.id),str(message.author.id)))
                for row in records:
                    words_solved = int(row[0])
                words_solved = words_solved + 1
                result = await commit_sql("""UPDATE Scoreboard SET LettersRight=%s WHERE ServerId=%s AND UserId=%s;""",(str(words_solved), str(message.guild.id),str(message.author.id)))                
                if '_' not in new_pattern:
                    await reply_message(message, "The word has been guessed!")
                    hangman_game_state[message.guild.id]["Event"] = False
                    hangman_game_state[message.guild.id]["BadGuesses"] = 0
                    hangman_game_state[message.guild.id]["Word"] = ""
                    hangman_game_state[message.guild.id]["Pattern"] = 0
                    guessed_letters[message.guild.id] = []
                    used_hint[message.guild.id] = False
                    try:
                        hangman_game_state[message.guild.id]["ChallengeUser"]
                        records = await select_sql("""SELECT ChallengesWon FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""",(str(message.guild.id),str(message.author.id)))
                        for row in records:
                            words_solved = int(row[0])
                        words_solved = words_solved + 1
                        result = await commit_sql("""UPDATE Scoreboard SET ChallengesWon=%s WHERE ServerId=%s AND UserId=%s;""",(str(words_solved), str(message.guild.id),str(message.author.id)))  
                        del hangman_game_state[message.guild.id]["ChallengeUser"]
                    except:
                        pass
                    used_hint[message.guild.id] = False
                    return
            else:
                await reply_message(message, "WRONG!")
                records = await select_sql("""SELECT LettersWrong FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""",(str(message.guild.id),str(message.author.id)))
                for row in records:
                    words_solved = int(row[0])
                words_solved = words_solved + 1
                result = await commit_sql("""UPDATE Scoreboard SET LettersWrong=%s WHERE ServerId=%s AND UserId=%s;""",(str(words_solved), str(message.guild.id),str(message.author.id)))                
                hangman_game_state[message.guild.id]["BadGuesses"] = hangman_game_state[message.guild.id]["BadGuesses"] + 1
                hangman_game_state[message.guild.id]["Hangman"] = bad_guess[hangman_game_state[message.guild.id]["BadGuesses"]]
                response = "```" + hangman_game_state[message.guild.id]["Hangman"] + "\n\n" + hangman_game_state[message.guild.id]["Pattern"] + "```"
                await reply_message(message, response)
                
                if hangman_game_state[message.guild.id]["BadGuesses"] > 6:
                    await reply_message(message, "Too many bad guesses! The word was " + hangman_game_state[message.guild.id]["Word"] + "!")
                    hangman_game_state[message.guild.id]["Event"] = False
                    hangman_game_state[message.guild.id]["BadGuesses"] = 0
                    hangman_game_state[message.guild.id]["Word"] = ""
                    hangman_game_state[message.guild.id]["Pattern"] = 0
                    guessed_letters[message.guild.id] = []
                    used_hint[message.guild.id] = False
                    try:
                        hangman_game_state[message.guild.id]["ChallengeUser"]
                        records = await select_sql("""SELECT ChallengesWon FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""",(str(message.guild.id),str(message.author.id)))
                        for row in records:
                            words_solved = int(row[0])
                        words_solved = words_solved + 1
                        result = await commit_sql("""UPDATE Scoreboard SET ChallengesWon=%s WHERE ServerId=%s AND UserId=%s;""",(str(words_solved), str(message.guild.id),str(message.author.id)))  
                        del hangman_game_state[message.guild.id]["ChallengeUser"]
                    except:
                        pass                    

                    used_hint[message.guild.id] = False
        elif command == 'guessedletters':
            response = "**GUESSED LETTERS**\n\n`"
            for x in guessed_letters[message.guild.id]:
                response = response + x + " "
            response = response + "`"
            await reply_message(message, response)
        elif command == 'hint':
            if hangman_game_state[message.guild.id]["Event"]:
                if used_hint[message.guild.id]:
                    await reply_message(message, "You have already used a hint!")
                    return
                records = await select_sql("""SELECT HintsUsed FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""",(str(message.guild.id),str(message.author.id)))
                for row in records:
                    words_solved = int(row[0])
                words_solved = words_solved + 1
                result = await commit_sql("""UPDATE Scoreboard SET HintsUsed=%s WHERE ServerId=%s AND UserId=%s;""",(str(words_solved), str(message.guild.id),str(message.author.id)))                  
                hint = False
                while not hint:
                    try_letter = random.randint(0,len(hangman_game_state[message.guild.id]["Word"]) - 1)
                    hint_letter = hangman_game_state[message.guild.id]["Word"][try_letter]
                    
                    if hangman_game_state[message.guild.id]["Pattern"][try_letter] == '_':
                        hint = True
                await reply_message(message, "The letter " + hint_letter + " is somewhere in this word.")
                used_hint[message.guild.id] = True
            elif trivia_game_state[message.guild.id]["Event"]:
                words = trivia_game_state[message.guild.id]["Answer"].split(' ')
                hint = " "
                for word in words:
                    hint = hint + re.sub(r"([A-Za-z0-9]).*",r"\1-- ",word)

                await reply_message(message, "**Hint**\n\n" + hint)
            elif crystal_game_state[message.guild.id]["Event"]:
                words = crystal_game_state[message.guild.id]["Crystal"].split(' ')
                hint = " "
                for word in words:
                    hint = hint + re.sub(r"([A-Za-z0-9]).*",r"\1-- ",word)

                await reply_message(message, "**Hint**\n\n" + hint)                
            else:
                await reply_message(message, "No game is currently ongoing!")
        elif command == 'invite':
            await reply_message(message, "Click here to invite me: https://discordapp.com/api/oauth2/authorize?client_id=704079890495832175&permissions=537259072&scope=bot")
        elif command == 'challenge':
            if not message.mentions:
                await reply_message(message, "You didn't mention a user to challenge!")
                return
            user = message.mentions[0]
            
            if 'easy' in parsed_string:
                number_of_letters = random.randint(3,8)
            elif 'medium' in parsed_string:
                number_of_letters = random.randint(9,16)
            elif 'hard' in parsed_string:
                number_of_letters = random.randint(17,30)
            elif 'nightmare' in parsed_string:
                number_of_letters = random.randint(31,40)
            else:
                number_of_letters = random.randint(3,30)
            records = await get_word(number_of_letters)
            for row in records:
                hangman_word = str(row[0])
                hangman_defs = str(row[1])
            hangman_word = re.sub(r"[^A-Za-z]","", hangman_word)    
            parsed_hangman_word = ""
            for x in hangman_word:
                parsed_hangman_word = parsed_hangman_word + x.upper() + " "
              
            hangman_game_state[message.guild.id]["Word"] = parsed_hangman_word
            hangman_game_state[message.guild.id]["Defs"] = hangman_defs
            hangman_game_state[message.guild.id]["Event"] = True
            if not re.search(r"easy|medium|hard|nightmare",parsed_string):
                parsed_string = "any"
            word_state = ""
            await reply_message(message, "New hangman game started by " + message.author.display_name + " on difficulty mode " + parsed_string + "!\n\n<@" + str(user.id) + "> has been challenged!")
            for x in range(1,number_of_letters):
                word_state = word_state + "_ "
            hangman_game_state[message.guild.id]["Pattern"] = word_state
            hangman_game_state[message.guild.id]["Hangman"] = hangman_initial
            hangman_game_state[message.guild.id]["ChallengeUser"] = user
            response = "```" + hangman_initial + "\n\n" + word_state + "```"
            await reply_message(message, response)
        elif command == 'setupscoreboard':
            for user in message.guild.members:
                result = await commit_sql("""INSERT INTO Scoreboard (ServerId,UserId,LettersRight, LettersWrong, ChallengesWon, ChallengesLost, HintsUsed, WordsSolved) VALUES (%s, %s, 0,0,0,0,0,0);""",(str(message.guild.id),str(user.id)))
            await reply_message(message, "Done!")
        elif command == 'screwball':
            await message.channel.send(">>> " + random.choice(screwball_answers))        
        elif command == 'mystats':
            records = await select_sql("""SELECT LettersRight, LettersWrong, ChallengesWon, ChallengesLost, HintsUsed, WordsSolved FROM Scoreboard WHERE ServerId=%s AND UserId=%s;""",(str(message.guild.id),str(message.author.id)))
            if not records:
                await reply_message(message, "No records found for you! Creating one...")
                result = await commit_sql("""INSERT INTO Scoreboard (ServerId,UserId,LettersRight, LettersWrong, ChallengesWon, ChallengesLost, HintsUsed, WordsSolved) VALUES (%s, %s, 0,0,0,0,0,0);""",(str(message.guild.id),str(message.author.id)))
                return
            response = "**YOUR STATS**\n\n"
            for row in records:
                letters_right = str(row[0])
                letters_wrong = str(row[1])
                challenges_won = str(row[2])
                challenges_lost = str(row[3])
                hints_used = str(row[4])
                words_solved = str(row[5])
            response = response + "Letters Guessed Correctly: `" + letters_right + "`\nLetters Guessed Incorrectly: `" + letters_wrong + "`\nChallenges Won: `" + challenges_won + "`\nChallenges Lost: `" + challenges_lost + "`\nHints Used: `" + hints_used + "`\nWords solved: `" + words_solved + "`\n"
            await reply_message(message, response)
        elif (command == 'resetscores'):
            set_score_to_zero = """UPDATE QuizScores Set Score=0 WHERE ServerId=%s;"""
            server_id = message.guild.id
            result = await commit_sql(set_score_to_zero, (server_id,))
            if result:
                await reply_message(message, "Leaderboard reset to zero for all members.")
            else:
                await reply_message(message, "Database error!")
        elif command == 'endlesstrivia':
            difficulty_re = re.compile(r"(?P<difficulty>easy|medium|hard|nightmare)", re.IGNORECASE)
            no_diff = False
            m = difficulty_re.search(parsed_string)
            if m:
                difficulty_string = m.group('difficulty').lower()
            category_string = re.sub(difficulty_re,"",parsed_string).strip()
            try: difficulty_string
            except: difficulty_string = None
            if difficulty_string == 'easy':
                difficulty = "Easy"
            elif difficulty_string == 'medium':
                difficulty = "Medium"
            elif difficulty_string == 'hard':
                difficulty = "Hard"
            elif difficulty_string == 'nightmare':
                difficulty = "Nightmare"
            else:
                no_diff = True
                difficulty = random.choice(['Easy','Medium','Hard','Nightmare'])
            trivia_query = """SELECT Question,Answer,Category FROM TriviaQuestions"""
            trivia_tuple = ()
            if difficulty_string and category_string == "":
                trivia_query = trivia_query + """ WHERE Difficulty=%s ORDER BY RAND( ) LIMIT 1;"""
                trivia_tuple = trivia_tuple + (difficulty,)
            elif category_string != "" and not difficulty_string:
                trivia_tuple = trivia_tuple + (category_string,)
                trivia_query = trivia_query + """ WHERE Category=%s ORDER BY RAND( ) LIMIT 1;"""
            elif category_string != "" and difficulty_string:
                trivia_tuple = trivia_tuple + (difficulty, category_string)
                trivia_query = trivia_query + """ WHERE Difficulty=%s AND Category=%s ORDER BY RAND( ) LIMIT 1;"""                
            else:
                trivia_query = trivia_query + """ ORDER BY RAND( ) LIMIT 1;"""
            
                
            records = await select_sql(trivia_query, trivia_tuple)
            
            for row in records:
                question = str(row[0]).replace('\xa0','')
                answer = str(row[1]).replace('\xa0','')
                category = str(row[2]).replace('\xa0','')
            try: category
            except: category = "None"
            if category is None:
                category = "None"
            
            trivia_game_state[message.guild.id]["Question"] = question
            trivia_game_state[message.guild.id]["Answer"] = answer
            trivia_game_state[message.guild.id]["Difficulty"] = difficulty
            trivia_game_state[message.guild.id]["Category"] = category
            trivia_game_state[message.guild.id]["Event"] = True
            trivia_game_state[message.guild.id]["Endless"] = True
            if not no_diff:
                trivia_game_state[message.guild.id]["GivenDifficulty"] = difficulty
            trivia_game_state[message.guild.id]["GivenCategory"] = category_string
            
            response = "An endless trivia round has been started by " + message.author.name + "!\n\n**Category:** " + category + "\n**QUESTION:** " + question + "\n"
            await reply_message(message, response)        
        elif command == 'trivia':
            difficulty_re = re.compile(r"(?P<difficulty>easy|medium|hard|nightmare)", re.IGNORECASE)
            m = difficulty_re.search(parsed_string)
            if m:
                difficulty_string = m.group('difficulty').lower()
            category_string = re.sub(difficulty_re,"",parsed_string).strip()
            try: difficulty_string
            except: difficulty_string = None
            if difficulty_string == 'easy':
                difficulty = "Easy"
            elif difficulty_string == 'medium':
                difficulty = "Medium"
            elif difficulty_string == 'hard':
                difficulty = "Hard"
            elif difficulty_string == 'nightmare':
                difficulty = "Nightmare"
            else:
                difficulty = random.choice(["Easy","Medium","Hard","Nightmare"])
            trivia_query = """SELECT Question,Answer,Category FROM TriviaQuestions"""
            trivia_tuple = ()
            if difficulty_string and category_string == "":
                trivia_query = trivia_query + """ WHERE Difficulty=%s ORDER BY RAND( ) LIMIT 1;"""
                trivia_tuple = trivia_tuple + (difficulty,)
            elif category_string != "" and not difficulty_string:
                trivia_tuple = trivia_tuple + (category_string,)
                trivia_query = trivia_query + """ WHERE Category=%s ORDER BY RAND( ) LIMIT 1;"""
            elif category_string != "" and difficulty_string:
                trivia_tuple = trivia_tuple + (difficulty, category_string)
                trivia_query = trivia_query + """ WHERE Difficulty=%s AND Category=%s ORDER BY RAND( ) LIMIT 1;"""                
            else:
                trivia_query = trivia_query + """ ORDER BY RAND( ) LIMIT 1;"""
            
                
            records = await select_sql(trivia_query, trivia_tuple)
            
            for row in records:
                question = str(row[0]).replace('\xa0','')
                answer = str(row[1]).replace('\xa0','')
                category = str(row[2]).replace('\xa0','')
            try: category
            except: category = "None"
            if category is None:
                category = "None"
            
            trivia_game_state[message.guild.id]["Question"] = question
            trivia_game_state[message.guild.id]["Answer"] = answer
            trivia_game_state[message.guild.id]["Difficulty"] = difficulty
            trivia_game_state[message.guild.id]["Category"] = category
            trivia_game_state[message.guild.id]["Event"] = True
            
            response = "A trivia round has been started by " + message.author.name + "!\n\n**Category:** " + category + "\n**QUESTION:** " + question + "\n"
            await reply_message(message, response)
        elif command == 'crystal':
            if not crystal_game_state[message.guild.id]["Event"]:
                await reply_message(message, "No one asked about crystals!")
                return
            if crystal_game_state[message.guild.id]["ChallengeUser"] != "":
                if crystal_game_state[message.guild.id]["ChallengeUser"] != message.author:
                    await reply_message(message, "You weren't named as the one who was challenged!")
                    return
            if parsed_string.lower() == crystal_game_state[message.guild.id]["Crystal"].lower():
                await reply_message(message, "**" + message.author.display_name + "** is correct!")
                crystal_game_state[message.guild.id]["Event"] = False
                crystal_game_state[message.guild.id]["ChallengeUser"]  = ""
            else:
                await reply_message(message, "That's not the right crystal! Try again!")
                
        elif command == 'answer':
            if not trivia_game_state[message.guild.id]["Event"]:
                await reply_message(message, "No one asked a question!")
                return
            id_num = message.author.id
            guild_id = message.guild.id
            get_current_score = """SELECT Score FROM QuizScores WHERE ServerId=%s AND UserId=%s;"""
            records = await select_sql(get_current_score, (str(guild_id), str(id_num)))
            if len(records) == 0:
                await reply_message(message, "No score found for the specified user.")
                return
            for row in records:
                quiz_score = int(row[0])
            if parsed_string.upper() == trivia_game_state[message.guild.id]["Answer"].upper():
                await reply_message(message, "Correct! **" + message.author.display_name + "** gets some points!")
                
                if trivia_game_state[message.guild.id]["Difficulty"] == 'Easy':
                    quiz_score = quiz_score + 1
                elif trivia_game_state[message.guild.id]["Difficulty"] == 'Medium':
                    quiz_score = quiz_score + 2
                elif trivia_game_state[message.guild.id]["Difficulty"] == 'Hard':
                    quiz_score = quiz_score + 4
                elif trivia_game_state[message.guild.id]["Difficulty"] == 'Nightmare':
                    quiz_score = quiz_score + 8
                else:
                    quiz_score = quiz_score + 1
                    
                await reply_message(message, "Your new trivia score is **"  + str(quiz_score) + "**.")
  
                update_score_entry = """UPDATE QuizScores Set Score=%s WHERE ServerId=%s AND UserId=%s;"""   
                score_entry = (str(quiz_score), str(guild_id), str(id_num))
                if not trivia_game_state[message.guild.id]["Endless"]:
                    trivia_game_state[message.guild.id]["Question"] = ""
                    trivia_game_state[message.guild.id]["Answer"] = ""
                    trivia_game_state[message.guild.id]["Difficulty"] = ""
                    trivia_game_state[message.guild.id]["Category"] = ""
                    trivia_game_state[message.guild.id]["Event"] = False
                result = await commit_sql(update_score_entry, score_entry)
                if not result:
                    await reply_message(message, "Database error! " + str(error))  
                if trivia_game_state[message.guild.id]["Endless"]:
                    trivia_query = """SELECT Question,Answer,Category,Difficulty FROM TriviaQuestions"""
                    trivia_tuple = ()
                    if trivia_game_state[message.guild.id]["GivenDifficulty"] and trivia_game_state[message.guild.id]["GivenCategory"] == "":
                        trivia_query = trivia_query + """ WHERE Difficulty=%s ORDER BY RAND( ) LIMIT 1;"""
                        trivia_tuple = trivia_tuple + (trivia_game_state[message.guild.id]["GivenDifficulty"],)
                    elif trivia_game_state[message.guild.id]["GivenCategory"] != "" and not trivia_game_state[message.guild.id]["GivenDifficulty"]:
                        trivia_tuple = trivia_tuple + (trivia_game_state[message.guild.id]["GivenCategory"],)
                        trivia_query = trivia_query + """ WHERE Category=%s ORDER BY RAND( ) LIMIT 1;"""
                    elif trivia_game_state[message.guild.id]["GivenCategory"] != "" and trivia_game_state[message.guild.id]["GivenDifficulty"]:
                        trivia_tuple = trivia_tuple + (trivia_game_state[message.guild.id]["GivenDifficulty"], trivia_game_state[message.guild.id]["GivenCategory"])
                        trivia_query = trivia_query + """ WHERE Difficulty=%s AND Category=%s ORDER BY RAND( ) LIMIT 1;"""                
                    else:
                        trivia_query = trivia_query + """ ORDER BY RAND( ) LIMIT 1;"""
                    
                        
                    records = await select_sql(trivia_query, trivia_tuple)
                    
                    for row in records:
                        question = str(row[0]).replace('\xa0','')
                        answer = str(row[1]).replace('\xa0','')
                        category = str(row[2]).replace('\xa0','')
                        difficulty = str(row[3])
                    try: category
                    except: category = "None"
                    if category is None:
                        category = "None"
                    response = "Next question!\n\n**Category:** " + category + "\n**QUESTION:** " + question + "\n"  
                    await reply_message(message, response)
                    trivia_game_state[message.guild.id]["Question"] = question
                    trivia_game_state[message.guild.id]["Answer"] = answer
                    trivia_game_state[message.guild.id]["Difficulty"] = difficulty
                    trivia_game_state[message.guild.id]["Category"] = category 

            
            else:
                await reply_message(message, "Incorrect! Please try again!")
                if trivia_game_state[message.guild.id]["Difficulty"] == 'Easy':
                    quiz_score = quiz_score - 1
                elif trivia_game_state[message.guild.id]["Difficulty"] == 'Medium':
                    quiz_score = quiz_score - 2
                elif trivia_game_state[message.guild.id]["Difficulty"] == 'Hard':
                    quiz_score = quiz_score - 4
                elif trivia_game_state[message.guild.id]["Difficulty"] == 'Nightmare':
                    quiz_score = quiz_score - 8
                else:
                    quiz_score = quiz_score - 1
                    
                await reply_message(message, "Your new trivia score is **"  + str(quiz_score) + "**.")
  
                update_score_entry = """UPDATE QuizScores Set Score=%s WHERE ServerId=%s AND UserId=%s;"""   
                score_entry = (str(quiz_score), str(guild_id), str(id_num))

                result = await commit_sql(update_score_entry, score_entry)
                
        elif command == 'namethatcrystal' or command == 'shiny':
            if message.mentions:
                crystal_game_state[message.guild.id]["ChallengeUser"] = message.mentions[0]
            output = subprocess.run(["/home/jwoleben/crystal/list.sh"], universal_newlines=True, stdout=subprocess.PIPE)
            crystal_list = output.stdout.split('\n')
            crystal = random.choice(crystal_list)
            crystal_name = crystal.replace('-',' ').strip()
            crystal_name = crystal_name.replace('.jpg','').replace("'",'')
            crystal_name = re.sub(r"\(.*\)","",crystal_name).strip()
            copyfile("/home/jwoleben/crystal/" + crystal, "/home/jwoleben/crystal/crystal.jpg")
            await log_message("Picked crystal " + crystal_name)
            await message.channel.send("Name this crystal!",file=discord.File("/home/jwoleben/crystal/crystal.jpg"))
            crystal_game_state[message.guild.id]["Event"] = True
            crystal_game_state[message.guild.id]["Crystal"] = crystal_name
            
            
        elif command == 'endendless':
            trivia_game_state[message.guild.id]["Question"] = ""
            trivia_game_state[message.guild.id]["Answer"] = ""
            trivia_game_state[message.guild.id]["Difficulty"] = ""
            trivia_game_state[message.guild.id]["Category"] = ""
            trivia_game_state[message.guild.id]["Event"] = False    
            trivia_game_state[message.guild.id]["Endless"] = False
            await reply_message(message, "The round is over!")
            
        elif (command == 'giveup'):
            if crystal_game_state[message.guild.id]["Event"]:
                await reply_message(message, message.author.display_name + " is giving up! The answer is " + crystal_game_state[message.guild.id]["Crystal"] + "!")
                return
            await reply_message(message, message.author.display_name + " is giving up! The answer is " + trivia_game_state[message.guild.id]["Answer"] + "!")
            if not trivia_game_state[message.guild.id]["Endless"]:
                trivia_game_state[message.guild.id]["Question"] = ""
                trivia_game_state[message.guild.id]["Answer"] = ""
                trivia_game_state[message.guild.id]["Difficulty"] = ""
                trivia_game_state[message.guild.id]["Category"] = ""
                trivia_game_state[message.guild.id]["Event"] = False
            else:
                trivia_query = """SELECT Question,Answer,Category,Difficulty FROM TriviaQuestions"""
                trivia_tuple = ()
                if trivia_game_state[message.guild.id]["GivenDifficulty"] and trivia_game_state[message.guild.id]["GivenCategory"] == "":
                    trivia_query = trivia_query + """ WHERE Difficulty=%s ORDER BY RAND( ) LIMIT 1;"""
                    trivia_tuple = trivia_tuple + (trivia_game_state[message.guild.id]["GivenDifficulty"],)
                elif trivia_game_state[message.guild.id]["GivenCategory"] != "" and not trivia_game_state[message.guild.id]["GivenDifficulty"]:
                    trivia_tuple = trivia_tuple + (trivia_game_state[message.guild.id]["GivenCategory"],)
                    trivia_query = trivia_query + """ WHERE Category=%s ORDER BY RAND( ) LIMIT 1;"""
                elif trivia_game_state[message.guild.id]["GivenCategory"] != "" and trivia_game_state[message.guild.id]["GivenDifficulty"]:
                    trivia_tuple = trivia_tuple + (trivia_game_state[message.guild.id]["GivenDifficulty"], trivia_game_state[message.guild.id]["GivenCategory"])
                    trivia_query = trivia_query + """ WHERE Difficulty=%s AND Category=%s ORDER BY RAND( ) LIMIT 1;"""                
                else:
                    trivia_query = trivia_query + """ ORDER BY RAND( ) LIMIT 1;"""
                
                    
                records = await select_sql(trivia_query, trivia_tuple)
                
                for row in records:
                    question = str(row[0]).replace('\xa0','')
                    answer = str(row[1]).replace('\xa0','')
                    category = str(row[2]).replace('\xa0','')
                    difficulty = str(row[3]).replace('\xa0','')
                try: category
                except: category = "None"
                if category is None:
                    category = "None"
                response = "Next question!\n\n**Category:** " + category + "\n**QUESTION:** " + question + "\n" 
                trivia_game_state[message.guild.id]["Question"] = question
                trivia_game_state[message.guild.id]["Answer"] = answer
                trivia_game_state[message.guild.id]["Difficulty"] = difficulty
                trivia_game_state[message.guild.id]["Category"] = category
                await reply_message(message, response)
        elif (command == 'myscore'):
            my_id = message.author.id
            guild_id = message.guild.id
            get_my_score = """SELECT Score FROM QuizScores WHERE ServerId=%s AND UserId=%s;"""
            async with message.channel.typing():
                records = await select_sql(get_my_score, (str(guild_id), str(my_id)))
            if len(records) == 0:
                await reply_message(message, "No score found for the specified user.")
                return
            response = "Your current trivia score is **"
            for row in records:
                score = str(row[0])
            response = response + score + "**."
            await reply_message(message, response)
        elif command == 'categories':
            records = await select_sql("""SELECT DISTINCT Category FROM TriviaQuestions;""")
            response = "**Question Categories**\n\n"
            for row in records:
                if row[0] is not None:
                    response = response + row[0] + "\n"
            await reply_message(message, response)
        elif (command == 'leaderboard'):
            get_leaderboard = """SELECT UserId,Score FROM QuizScores WHERE ServerId=%s ORDER BY Score DESC;"""
            guild_id = message.guild.id
            async with message.channel.typing():
                records = await select_sql(get_leaderboard, (str(guild_id),))

            if len(records) == 0:
                await reply_message(message, "No score found for the specified server.")
                return
            response = "**Trivia Leaderboard:**\n\n"
            for row in records:
                username = get(client.get_all_members(), id=int(row[0]))
                response = response + str(username.name) + " - " + str(row[1]) + "\n"
            await reply_message(message, response)               
        elif (command == 'initializeleaderboard'):
            if not await admin_check(message.author.id):
                await reply_message(message, "Admin command only!")
                return
            result = await execute_sql("""DROP TABLE IF EXISTS QuizScores; CREATE TABLE QuizScores (ServerId VarChar(40), UserId VarChar(30), Score Int);""")
            if not result:
                await reply_message(message,"Could not create Quiz Scores!")
            for guild in client.guilds:
                for member in guild.members:
                    create_score_entry = """INSERT INTO QuizScores (ServerId, UserId, Score) VALUES(%s, %s, %s);"""   
                    score_entry = (str(guild.id), str(member.id), str(0))
                    result = await commit_sql(create_score_entry, score_entry)
                    if not result:
                        await reply_message(message, "Database error!")   

            await reply_message(message, "Leaderboard initialized.")                 
                
        else:
            pass
        
client.run('NzA0MDc5ODkwNDk1ODMyMTc1.XqX7rg.6_GBZ3VcRYC90TuQuxt5w0b18Z0')