import datetime
from datetime import timedelta
from discord.ext import commands, tasks, bridge
import discord
from bot import bot
from .DatabaseHandler import mycursor, db, testingservers, get_all_users, get_all_active_users
from .VCTracker import getTimeSpentInVcWithoutFriendos, getTimeSpentInVcWithoutFriendosBetweenDays
from datetime import time
from discord.ext.commands import is_owner
from math import floor, ceil

def getloggedmsgs():
    mycursor.execute(
        f"select messageId from sanity2.loggedmsgs"
    )
    data = mycursor.fetchall()

    alreadyLoggedMsgs = [item[0] for item in data]
    return alreadyLoggedMsgs

def logmsg(message):
    message_id = int(message.id)
    message_chan = int(message.channel.id)
    author_id = int(message.author.id)
    guild_id = int(message.guild.id)
    message_content = str(message.content)
    message_creation = message.created_at

    if len(message_content) > 999:
        message_content = message_content[0:998]

    message_content = message_content.encode("ascii", "ignore")
    message_content = message_content.decode()

    # try:
    mycursor.execute(
        f"INSERT INTO sanity2.loggedmsgs (messageID, authorID, messageChan, guildID, messageContent, datetimeMSG) VALUES (%s, %s, %s, %s, %s, %s)",
        (message_id, author_id, message_chan, guild_id, message_content, message_creation))

    db.commit()

def insertUserDiscordElo(userId:int):
    mycursor.execute(
        f"INSERT INTO sanity2.discordelo (userId) VALUES (%s)", (userId,)
    )
    db.commit()

def checkDiscordEloUsers():
    mycursor.execute(
        f"select * from sanity2.discordelo"
    )
    discordEloData = mycursor.fetchall()
    usersInDiscordElo = [user[0] for user in discordEloData]
    usersInUsers = [user[0] for user in get_all_active_users()]

    for userId in usersInUsers:
        if userId not in usersInDiscordElo:
            insertUserDiscordElo(userId)

def getAllChatsBetweenDays(pastxdays:int):
    mycursor.execute(
        f"select count(*),authorId from sanity2.loggedmsgs"
        f" where datetimeMSG >= NOW() - INTERVAL {pastxdays} DAY and  datetimeMSG <= NOW() - INTERVAL {pastxdays-1} DAY"
        f" group by 2"
    )
    chatdata = mycursor.fetchall()

    mycursor.execute(
        f"select count(*) from sanity2.loggedmsgs"
        f" where datetimeMSG >= NOW() - INTERVAL {pastxdays} DAY and  datetimeMSG <= NOW() - INTERVAL {pastxdays-1} DAY"
    )
    summsgs = mycursor.fetchall()[0][0]

    return chatdata,summsgs

def getAllChats():
    mycursor.execute(
        f"select count(*),authorId from sanity2.loggedmsgs"
        f" where datetimeMSG >= NOW() - INTERVAL 1 DAY"
        f" group by 2"
    )
    chatdata = mycursor.fetchall()

    mycursor.execute(
        f"select count(*) from sanity2.loggedmsgs"
        f" where datetimeMSG >= NOW() - INTERVAL 1 DAY"
    )
    summsgs = mycursor.fetchall()[0][0]

    return chatdata,summsgs

def getUserDiscordElo(userId:int):
    mycursor.execute(
        f"select * from sanity2.discordelo where userId = {userId}"
    )
    data = mycursor.fetchall()

    if len(data) > 0:
        return int(data[0][1])
    else:
        return None

def getDiscordEloSum():
    mycursor.execute(
        f"select sum(discordElo) from sanity2.discordelo"
    )
    data = mycursor.fetchall()

    return data[0][0] #total elo in system

def updateUserElo(userId:int, newElo:int, elochange:int):
    mycursor.execute(
        f"update sanity2.discordelo set discordElo = {newElo},discordEloChange = {elochange} "
        f" where userId = {userId} "
    )
    db.commit()

def getAllEloTiers():
    mycursor.execute(
        f"select userId, discordElo from sanity2.discordelo order by discordElo desc"
    )
    data = mycursor.fetchall()

    eloRanking = [rank[1] for rank in data]

    return eloRanking

def updateDiscordEloTier(tier:int, tierPointReq:int):
    mycursor.execute(
        f"update sanity2.discordelotiers set tierPointReq = {tierPointReq} where tier = {tier}"
    )
    db.commit()


@tasks.loop(time=[time(hour=8, minute=10)]) #check if people missing in db
async def discordEloTierGen():
    """
    Ranks:
    Master: Top 10
    Elite: Top 30
    Hard: Top 90
    Medium: Top 150
    Easy: >150
    """
    discordEloData = getAllEloTiers()

    master = 9
    elite = 29
    hard = 89
    medium = 149

    masterReq = discordEloData[master]
    eliteReq = discordEloData[elite]
    hardReq = discordEloData[hard]
    mediumReq = discordEloData[medium]

    updateDiscordEloTier(5,masterReq)
    updateDiscordEloTier(4, eliteReq)
    updateDiscordEloTier(3, hardReq)
    updateDiscordEloTier(2, mediumReq)

@discordEloTierGen.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
discordEloTierGen.start()

@tasks.loop(time=[time(hour=23, minute=0)]) #check if people missing in db
async def discordEloGen():
    """
    Steps:
    1. Check if all users are in discordEloDB
    2. Get ranking for Chatting+VC -> if not ranked in BOTH
    3. Decay inactive users
    """
    print("STARTING DISCORD ELO STUFF")

    #check if all users are in
    checkDiscordEloUsers()

    #get chatting + vc ranking
    result = getTimeSpentInVcWithoutFriendos(228143014168625153)

    all_users = [user[0] for user in get_all_active_users()]

    #chatting stats
    chatdata, msgsToday = getAllChats()

    # elo sum
    sumOfAllElos = getDiscordEloSum()
    averageElo = floor(sumOfAllElos / len(all_users))

    # calculate how many points to give for chatting, based on msgs on a given day
    chatting_point_scalng = max(5, min(30, round(5 + (25 * (msgsToday - 300)) / 1200)))

    for userId in all_users:
        try:
            vcRank = result.loc[result['userId'] == userId, 'Rank'].values[0]
        except:  # no rank
            vcRank = None

        chattingRank = None
        for i, sublist in enumerate(chatdata):
            if sublist[0] == userId:
                chattingRank = i
                break

        userCurrentElo = getUserDiscordElo(userId)
        if vcRank == None and chattingRank == None:  # decay
            updateUserElo(userId, floor(userCurrentElo * 0.999),-(userCurrentElo-floor(userCurrentElo * 0.999)))  # 1% decay daily on inactivity
        else:  # add elo

            # calculate performance score

            expectedScore = userCurrentElo / sumOfAllElos

            performanceScoreChat = None
            if chattingRank:
                performanceScoreChat = float(1 - (chattingRank - 1) / len(all_users)) ** 2

            performanceScoreVC = None
            if vcRank:
                performanceScoreVC = float(1 - ((vcRank - 1) / len(all_users))) ** 2

            if performanceScoreChat:
                chatEloChange = floor((chatting_point_scalng * averageElo / userCurrentElo) * (
                            float(performanceScoreChat) - float(expectedScore)))
            else:
                chatEloChange = 0

            if performanceScoreVC:
                vcEloChange = floor(
                    (15 * averageElo / userCurrentElo) * (float(performanceScoreVC) - float(expectedScore)))
            else:
                vcEloChange = 0

            newElo = userCurrentElo + chatEloChange + vcEloChange
            updateUserElo(userId, newElo, chatEloChange + vcEloChange)

        #print(f"{userId} - vc rank: {vcRank} - chattingrank : {chattingRank}")


@discordEloGen.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
discordEloGen.start()


class messagelogger(commands.Cog):
    def __init__(self, bot):
        self.client = bot

    @bridge.bridge_command(guild_ids=testingservers, name="calcdiscordelo",
                           description="calcdiscordelo")
    @is_owner()
    async def calcdiscordelo(self, ctx: discord.ApplicationContext,
                    pastxdays: discord.Option(int, "calc discordelo past x days")):

        for x in range(pastxdays):
            reversex = pastxdays -x
            checkDiscordEloUsers()
            all_active_users = get_all_active_users()
            all_users = [user[0] for user in all_active_users]
            join_dates = [user[7] for user in all_active_users]

            # get chatting + vc ranking
            result = getTimeSpentInVcWithoutFriendosBetweenDays(reversex)

            # chatting stats
            chatdata, msgsToday = getAllChatsBetweenDays(reversex)

            # elo sum
            sumOfAllElos = getDiscordEloSum()
            averageElo = floor(sumOfAllElos / len(all_users))

            # calculate how many points to give for chatting, based on msgs on a given day
            chatting_point_scalng = max(5, min(15, round(5 + (10 * (msgsToday - 300)) / 1200)))


            daycalc = datetime.datetime.now() - timedelta(days=reversex)
            print(f"started {daycalc} discord elo calc")

            count = 0
            for userId in all_users:
                join_date = datetime.datetime(join_dates[count].year, join_dates[count].month, join_dates[count].day)
                if join_date < daycalc:  #join date after day calc
                    try:
                        vcRank = result.loc[result['userId'] == userId, 'Rank'].values[0]
                    except:  # no rank
                        vcRank = None

                    chattingRank = None
                    for i, sublist in enumerate(chatdata):
                        if sublist[0] == userId:
                            chattingRank = i
                            break

                    userCurrentElo = getUserDiscordElo(userId)
                    if vcRank == None and chattingRank == None:  # decay
                        updateUserElo(userId, floor(userCurrentElo * 0.999), userCurrentElo-floor(userCurrentElo * 0.999))  # 0.1% decay daily on inactivity
                    else:  # add elo

                        # calculate performance score

                        expectedScore = userCurrentElo / sumOfAllElos

                        performanceScoreChat = None
                        if chattingRank:
                            performanceScoreChat = float(1 - (chattingRank - 1) / len(all_users)) ** 2

                        performanceScoreVC = None
                        if vcRank:
                            performanceScoreVC = float(1 - ((vcRank - 1) / len(all_users))) ** 2

                        if performanceScoreChat:
                            chatEloChange = floor((chatting_point_scalng * averageElo/userCurrentElo) * (float(performanceScoreChat) - float(expectedScore)))
                        else:
                            chatEloChange = 0

                        if performanceScoreVC:
                            vcEloChange = floor((10 * averageElo/userCurrentElo) * (float(performanceScoreVC) - float(expectedScore)))
                        else:
                            vcEloChange = 0

                        newElo = userCurrentElo + chatEloChange + vcEloChange
                        updateUserElo(userId, newElo, chatEloChange + vcEloChange)

                count += 1

            print(f"{x}/{pastxdays} done")



    @discord.slash_command(guild_ids=testingservers, name="logmsgs", description="logmsgs")
    @is_owner()
    async def logmsgs(self, ctx, limit=None):
        """logs msgs"""

        if ctx.author.id == 228143014168625153:
            loggedMessageIds = getloggedmsgs()
            for channel in ctx.guild.text_channels:
                #print(channel)
                try:
                    async for message in channel.history(limit=limit):
                        if message.guild and not message.author.bot and message.id not in loggedMessageIds:
                            logmsg(message)

                except discord.Forbidden:
                    continue #no access to channel

                except Exception as e:
                    print(f"error on {channel.id}: {e}")

        print("DONE")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild and not message.author.bot:
            #print(message.content)
            if message.guild.id != 305380209366925312:
                logmsg(message)


def setup(bot):
    bot.add_cog(messagelogger(bot))