import math
import regex as re
import gspread
import mysql
from discord.ext import commands, tasks
from discord.ui import View, Modal, InputText, Button, button
import datetime
from datetime import time
import discord
from dateutil import relativedelta
from bot import bot
from cogs.commands import admin
from cogs.commands.admin import datetime_to_string
from cogs.commands.dropSubmit import getDisplayNameFromListOfuserIDs
from cogs.handlers.diaryHandler import checkUserDiary
from cogs.handlers.DatabaseHandler import get_all_ranks, get_all_users, updateUserRank, mycursor, getUserData, db, \
    insert_Point_Tracker, db_user, updatersn, \
    getUserData, get_all_active_users, get_channel, insert_audit_Logs, fetchranksGracePeriod, update_user_points, \
    insert_Point_Tracker, turnListOfIds_into_names, add_user_todb, bingoModeCheck, get_all_inactive_users
from cogs.handlers.EmbedHandler import embedVariable
from cogs.util.CoreUtil import get_diary_difficulty
import requests
print("Bot loading loops cog")

"""
2 checks required:
 1. check if database matches discord -> loop through every member in server
 2. check if user from server is missing in DB

Loops:
 1. Check if users are not added, or retired
 2. check if points / diary reqs > threshold for next rankup ---- unless we check when drops are accepted -> change from loop to normal command and trigger from accept
    - need something to check the diary / master diary points hmmge"""

def updateRefStatusClaimed(userId:int):
    mycursor.execute(
        f"update sanity2.users set refPointsGiven = 1 where userId = {userId}"
    )
    db.commit()

def insertRankUpDelay(userId:int):
    today = datetime.datetime.now()

    # Find the first day of the next month
    next_month = today.replace(day=28) + datetime.timedelta(days=4)  # Ensures we go to the next month
    first_day_next_month = next_month.replace(day=1)

    # Subtract one day to get the last day of the current month
    last_day_of_month = first_day_next_month - datetime.timedelta(days=1)

    mycursor.execute(
        "insert into sanity2.rankupdelay (memberId, dateDelayedFrom)"
        "VALUES (%s,%s)",
        (userId, last_day_of_month)
    )

    db.commit()

def getUserRefs(userId:int):
    mycursor.execute(
        f"select referredBy, userId,displayName from sanity2.users where userId = {userId}"
    )
    data = mycursor.fetchall()

    try:
        refs = data[0][0]
        displayName = data[0][2]
    except:
        refs = None
        displayName = None

    if refs:
        split_refs = refs.split(",")
        number_of_refs = len(split_refs)
        ref_base_amount = 100
        ref_amount = math.floor(ref_base_amount/number_of_refs)

        for id in split_refs:
            try:
                member_id = int(id)
                fail = 0
            except:
                fail = 1
                member_id = None

            if fail == 0:  # add points
                update_user_points(member_id, ref_amount)
                insert_Point_Tracker(member_id, ref_amount, datetime.datetime.now(), f"{displayName} ref / {number_of_refs} refs")

        #updateRefStatusClaimed(userId)

        #return list of ref names
        string_sql_participants, clannies_names = getDisplayNameFromListOfuserIDs(split_refs)

        return clannies_names
    else:
        return None


def getUserPointsThisMonth(userId :int):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year

    mycursor.execute(
        f"SELECT sum(pointtracker.points) from sanity2.pointtracker inner join sanity2.users on pointtracker.userId = users.userId "
        f" where month(`date`) = {month} and year(`date`) = {year} and users.userId = {userId}"
    )
    dataThisMonth = mycursor.fetchall()
    if len(dataThisMonth) > 0:
        return dataThisMonth[0][0]
    else:
        return 0



def getUserPointsPrevious2Month(userId :int):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year
    prevmonth = 0

    if month == 2:
        year -= 1
        month = 12
    else:
        prevmonth += 2


    if month == 1:
        year -= 1
        month = 11
    else:
        prevmonth += 2


    if prevmonth == 4:
        month -= 2

    mycursor.execute(
        f"SELECT sum(pointtracker.points) from sanity2.pointtracker inner join sanity2.users on pointtracker.userId = users.userId "
        f" where month(`date`) = {month} and year(`date`) = {year} and users.userId = {userId}"
    )
    dataPastMonth = mycursor.fetchall()
    if len(dataPastMonth) > 0:
        return dataPastMonth[0][0]
    else:
        return 0

def readytodemotecheck(userID : int):
    mycursor.execute(
        f"select * from sanity2.rankupdelay where memberID = {userID} and dateDelayedFrom > now() order by dateDelayedFrom desc"
    )
    data = mycursor.fetchall()

    #print(f"userID {userID} len {len(data)} data{data}")

    if len(data) == 0: #no msg to delay
        return True
    else: # DEMOTE
        return False


def getUserPointsPreviousMonth(userId :int):
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year

    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    mycursor.execute(
        f"SELECT sum(pointtracker.points) from sanity2.pointtracker inner join sanity2.users on pointtracker.userId = users.userId "
        f" where month(`date`) = {month} and year(`date`) = {year} and users.userId = {userId}"
    )
    dataPastMonth = mycursor.fetchall()
    if len(dataPastMonth) > 0:
        return dataPastMonth[0][0]
    else:
        return 0


def updateNick(userId : int, NewNick : str):
    mycursor.execute(
        f"update sanity2.users set displayName = '{NewNick}' where userId = {userId}"
    )
    db.commit()

def updateDiaryTier(userId :int, tierClaimed: int):
    mycursor.execute(
        f"update sanity2.users set diaryTierClaimed = {tierClaimed} where userId = {userId}"
    )
    db.commit()

def getUserDiaryTier(userId :int):
    mycursor.execute(
        f"select diaryTierClaimed from sanity2.users where userId = {userId}"
    )
    tierClaimed = mycursor.fetchall()[0][0]

    return tierClaimed

def getDiaryPointReward(diaryTier):
    mycursor.execute(
        f"select points from sanity2.diaryrewards where diaryTier = {diaryTier}"
    )
    data = mycursor.fetchall()

    return data[0][0]

def getRoleId(name : str):
    mycursor.execute(
        f"select * from sanity2.roles where name = '{name}'"
    )
    data = mycursor.fetchall()
    if len(data) > 0:
        return data[0][1]
    else:
        return None

def updateLatestNameChangeIdWom(newId:int):
    mycursor.execute(
        f"update sanity2.wiseoldmannamechanges set latestnamechangeid = {newId}"
    )
    db.commit()

def latestNameChangeIdWom():
    mycursor.execute(
        f"select * from sanity2.wiseoldmannamechanges"
    )
    latestnameChangeId = mycursor.fetchall()[0][0]

    return latestnameChangeId

def latestNameChanges(groupId):
    x = requests.get(f'https://api.wiseoldman.net/v2/groups/{groupId}/name-changes?limit=50' ) #?limit=5 removed
    return x.json()

def checkIfRSNinDB(rsn : str):
    mycursor.execute(
        f"select * from sanity2.users where mainRSN = '{rsn}'"
    )
    data = mycursor.fetchall()

    if data:
        return data
    else:
        return None




class diaryPointClaimerView(View):  # for council / drop acceptors etc in #posted-drops
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction):
        mycursor.execute(
            "select discordRoleId,name from sanity2.roles where adminCommands = 1"
        )
        data = mycursor.fetchall()
        list = [i[0] for i in data]

        interaction_user_roleID_list = [role.id for role in interaction.user.roles]

        check = any(role in interaction_user_roleID_list for role in list)
        return check

    @button(label="Give pts!", custom_id="acceptor-accept-button-66" ,style=discord.ButtonStyle.green, emoji="✅")
    async def givepts(self, button: Button, interaction: discord.Interaction):
        channel = interaction.message.channel
        msg_to_edit = await channel.fetch_message(interaction.message.id)
        for embed in msg_to_edit.embeds:
            embed_dict = embed.to_dict()

        now = datetime.datetime.now()
        #title = int(str(embed_dict["title"]))
        tiersClaimed = int(embed_dict["fields"][0]["value"])
        thisTier = int(embed_dict["fields"][1]["value"])
        points = int(embed_dict["fields"][2]["value"])
        userId = int(embed_dict["fields"][3]["value"])

        #print(memberId, previousRankId, newRankId)

        embed = discord.Embed.from_dict(embed_dict)
        embed.color = discord.Color.green()


        insert_audit_Logs(interaction.user.id, 5, now, f"DiaryTierClaimed {tiersClaimed} - pts {points} ",userId)
        update_user_points(userId,points)
        insert_Point_Tracker(userId,points,datetime.datetime.now(),f"Diary tier {thisTier}")

        #set diaryTier in users table to max(current claimed / prev claim)
        tiersClaimedDb = getUserDiaryTier(userId)
        updateDiaryTier(userId,max(tiersClaimedDb,thisTier))

        await interaction.message.edit(embed=embed,view=None)
        #await interaction.response.send_message("drop accepted and points given",)


    @button(label="Already claimed higher tier", custom_id="acceptor-decline-button-77", style=discord.ButtonStyle.danger, emoji="✖️")
    async def alreadyclaimedpts(self, button: Button, interaction: discord.Interaction):
        channel = interaction.message.channel
        msg_to_edit = await channel.fetch_message(interaction.message.id)
        for embed in msg_to_edit.embeds:
            embed_dict = embed.to_dict()

        now = datetime.datetime.now()
        # title = int(str(embed_dict["title"]))
        tiersClaimed = int(embed_dict["fields"][0]["value"])
        thisTier = int(embed_dict["fields"][1]["value"])
        points = int(embed_dict["fields"][2]["value"])
        userId = int(embed_dict["fields"][3]["value"])

        embed = discord.Embed.from_dict(embed_dict)
        embed.color = discord.Color.red()

        tiersClaimedDb = getUserDiaryTier(userId)
        insert_audit_Logs(interaction.user.id, 5, now, f"DiaryTierClaimed set to {max(tiersClaimedDb, thisTier)} - no pts", userId)
        updateDiaryTier(userId, max(tiersClaimedDb, thisTier))

        await interaction.message.edit(embed=embed,view=None)
        #await interaction.response.send_message("The submission has been removed")

"""@task.loop(seconds=30)
async def auditlogposter():"""

@tasks.loop(time=[time(hour=16,minute=14)]) #UPDATE RSN changes time=[time(hour=16,minute=14)]
async def rsnwiseoldmanupdater():
    text = latestNameChanges(230)

    latestNameIdUpdated = latestNameChangeIdWom()

    lengthJson = len(text)
    for x in range(len(text)):
        entry = (text[lengthJson-x-1])

        prevRSN = entry["oldName"]
        nameChangeId = entry['id']
        #print(nameChangeId)
        checkRSN = checkIfRSNinDB(prevRSN)
        #print(checkRSN)
        status = entry['status']

        if checkRSN and status == 'approved' and nameChangeId > latestNameIdUpdated:
            newRsn = entry['newName']
            dbUserId = checkRSN[0][0]
            updatersn(dbUserId,1,newRsn)
            print(f"updated {dbUserId} rsn to {newRsn}")
            updateLatestNameChangeIdWom(nameChangeId)

    print("done updating names!")

@rsnwiseoldmanupdater.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
rsnwiseoldmanupdater.start()


@tasks.loop(time=[time(hour=17,minute=41)]) #]
async def updatealldairiepoints():
    try:
        all_users = get_all_users()
        #print(all_users)
        user_ids = [user[0] for user in all_users]

        for user_id in user_ids:
            #print(user_id)
            embed, diaryPoints, masterDiaryPoints = checkUserDiary(user_id)

        print("FINISHED UPDATING DAIRIESSSSSSSSSSS")
    except:
        print("failed updating diary points - updatealldairiepoints - might have worked still")

@updatealldairiepoints.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
updatealldairiepoints.start()

@tasks.loop(minutes=1)
async def bingoSheetUpdater():
    bingoVal = bingoModeCheck()
    #print(bingoVal)
    if bingoVal == 1:
        #DO BINGO STUFF
        #print(F"UPDATING BINGO SHEET---")
        try:
            sa = gspread.service_account("sanitydb-v-363222050972.json")
            sheet = sa.open(f"bingo")
            test = 1
        except gspread.exceptions.APIError:
            test = 0
            print("API ERROR UPDATING GSPREAD sheet")

        if test == 1:
            # tableList = [table[0] for table in mycursor.fetchall()]
            # print(tableList)
            # for table in tableList:
            # print(f"TABLE ==== {table}")
            workSheet = sheet.worksheet("Ark1")
            # Get the values from column A
            column_values = workSheet.col_values(1)
            len_gsheet = len(column_values)
            if len_gsheet > 0:
                joinedFormat = f"({','.join(str(value) for value in column_values if str(value) != 'Id')})"
            else:
                joinedFormat = "(0,1,2)"

            # print(joinedFormat)

            # NEW bingo drops from past 15 days
            mycursor.execute(
                f"SELECT Id,userId,participants,value,imageUrl,notes,submittedDate from sanity2.submissions where bingo = 1 "
                f"  and status = 2  and Id not in {joinedFormat}"
                # and submittedDate  BETWEEN NOW() - INTERVAL 15 DAY AND NOW() <- only past 15 days
            )
            table = mycursor.fetchall()
            # descriptions = [[str(item[0]) for item in mycursor.description]]

            actualTable = [list(tuple) for tuple in table]

            datetime_to_string(actualTable)  # gspread doesnt like datetime.datetime obj -> converts to string
            workSheet.update(values=actualTable, range_name=f'A{len_gsheet + 1}')




@bingoSheetUpdater.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
bingoSheetUpdater.start()


"""@tasks.loop(time=[time(hour=i, minute=43) for i in range(24)])
#@tasks.loop(minutes=2) #uncomment above
async def sanityOverViewUpdater():  # update the sheets #users and #drops
    if db_user == "admin":
        print("==========UPDATING SHEETS STARTED==========")

        sheetlist = [("personalbests","submissionId"),("pointtracker","Id"),("users","userId"),("submissions","Id")]

        for item in sheetlist:
            sheetname = item[0]
            orderbyitem = item[1]

            try:
                sa = gspread.service_account("sanitydb-v-363222050972.json")
                sheet = sa.open(f"{sheetname}")
                test = 1
            except gspread.exceptions.APIError:
                test = 0
                print("API ERROR UPDATING GSPREAD sheet")

            if test == 1:
                mycursor.execute(
                    f"SELECT * from sanity2.{sheetname} order by {orderbyitem} desc limit 5000"
                )
                table = mycursor.fetchall()
                descriptions = [[str(item[0]) for item in mycursor.description]]
                actualTable = [list(tuple) for tuple in table]

                datetime_to_string(actualTable)  # gspread doesnt like datetime.datetime obj -> converts to string
                # print(test)
                # print(F"====== DESCRIPTIONS==============")
                # print(descriptions)

                # print(F"======= TABLE =========")
                # print(actualTable)

                # Write the array to worksheet starting from the A2 cell
                try:
                    workSheet = sheet.worksheet("Ark1")
                    workSheet.clear()
                    workSheet.update(values=descriptions, range_name='A1')  # insert description / header
                    workSheet.update(values=actualTable, range_name='A2')  # insert data
                except:
                    print(f"{sheetname} update FAILED - API unavilable usually!!!")

                try:
                    print(f"Sheet **{sheetname}** has been updated")
                except:
                    print(f"Sheet **{sheetname}** has been updated")
            else:
                print(f"sheet did not update - api error!")

        ##### update drops
        print("==========UPDATING SHEETS FINISHED==========")"""


"""@sanityOverViewUpdater.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
sanityOverViewUpdater.start()"""


@tasks.loop(time=[time(hour=20,minute=14)])
async def elderRankGiver():
    active_users_list = get_all_active_users()
    sanity = bot.get_guild(301755382160818177)
    now = datetime.datetime.now()

    for member in active_users_list:
        joinDate = member[7]
        relativeDif = relativedelta.relativedelta(now, joinDate)
        years = relativeDif.years
        elder_role_id = getRoleId("1YEAR")
        #new_elder_role_id = getRoleId("ELDER")

        if years > 0:
            member_disc = sanity.get_member(member[0])
            if member_disc:
                """print(f"{member_disc.display_name}")"""
                member_ranks = [rank.id for rank in member_disc.roles]
                if elder_role_id not in member_ranks:
                    new_role = sanity.get_role(elder_role_id)
                    #print(f"added elder role to {member[0]}")
                    await member_disc.add_roles(new_role)
                    insert_audit_Logs(member_disc.id,8,datetime.datetime.now(),"Elder role assigned",member_disc.id)
                """if new_elder_role_id not in member_ranks:
                    new_role = sanity.get_role(new_elder_role_id)
                    #print(f"added elder role to {member[0]}")
                    await member_disc.add_roles(new_role)
                    insert_audit_Logs(member_disc.id,8,datetime.datetime.now(),"Elder role v2 assigned",member_disc.id)"""

@elderRankGiver.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
elderRankGiver.start()

@tasks.loop(time=[time(hour=18)]) #
async def diaryPointsClaimer():
    mycursor.execute(
        "select userId ,displayName ,max(diaryPoints) ,max(masterDiaryPoints) ,max(diaryTierClaimed), max(d.diaryTier), max(d.diaryPointsReq)  from sanity2.users u"
        " inner join sanity2.diaryrewards d on u.diaryPoints >= (d.diaryPointsReq/100 * (select sum(CASE when maxDifficulty = 1 then 1 when maxDifficulty = 2 then 3 when maxDifficulty = 3 then 6 when maxDifficulty = 4 then 10 when maxDifficulty = 5 then 15 END) from sanity2.diarytimes d)) "
        " where rankId != 1"
        " group by userId,displayName "
        " having max(u.diaryTierClaimed) < max(d.diaryTier)"
    )
    diaryPointDif = mycursor.fetchall()

    #print(diaryPointDif)

    if len(diaryPointDif) > 0:
        channel = await bot.fetch_channel(get_channel("rank-updates"))
        for user in diaryPointDif:
            userId = user[0]
            claimedTiers = user[4]
            tiersToClaim = user[5]

            for x in range(tiersToClaim-claimedTiers):
                textdifficulty = get_diary_difficulty(claimedTiers+x+1)
                pointReward = getDiaryPointReward(claimedTiers+x+1)
                embed = embedVariable(f"<:diary:1302709942255489044> {user[1]} - {textdifficulty} diary points",discord.Colour.yellow(),("Tiers claimed",str(claimedTiers)),("Tier to claim",claimedTiers+x+1),("Points",pointReward),("UserID",userId))

                view = diaryPointClaimerView()
                await channel.send(embed=embed,view=view)

@diaryPointsClaimer.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
diaryPointsClaimer.start()

@tasks.loop(time=[time(hour=i, minute=5) for i in range(24)]) #check if people missing in db
async def checkUsersMissingDb():
    print("STARTING USER CHECK=")
    rank_id_list = get_all_ranks()
    #print(rank_id_list)
    db_rank_ids = [dbrank[2] for dbrank in rank_id_list]
    flex_rank_ids = [(dbrank[0],dbrank[2]) for dbrank in rank_id_list]
    #print(flex_rank_ids)

    user_ids_in_DB = [user[0] for user in get_all_users()]

    sanity = bot.get_guild(301755382160818177)

    for member in sanity.members:
        #print(member)
        if member.id in user_ids_in_DB:
            #print(member.display_name, member.id)
            #sync databse to what discord actually has
            #get highest rank of role -> check if matching db
            member_ranks = [rank.id for rank in member.roles]
            clan_ranks = [role for role in member_ranks if role in db_rank_ids]
            try:
                max_role_id = max([flex_id[0] for flex_id in flex_rank_ids if flex_id[1] in clan_ranks])
            except:
                max_role_id = 0

            if member.nick:
                memberDisplayName = member.nick
            else:
                memberDisplayName = member.display_name

            memberDisplayName = re.sub(r'[^a-zA-Z0-9 ]', '', memberDisplayName)
            user_data = getUserData(member.id)

            display_Name_DB = user_data[1]
            user_rank_indb = user_data[4]

            #print(display_Name_DB, user_rank_indb, max_role_id)

            if user_rank_indb != max_role_id:
                #update user rank to max_role_di
                updateUserRank(member.id,max_role_id)
                print(f"UPDATED {member.id} to {max_role_id}")
                insert_audit_Logs(userId=228143014168625153,actionType=8,actionDate=datetime.datetime.now(),actionNote=f"UPDATED {member.id} RANK from {user_rank_indb} to {max_role_id}",affectedUsers=f"{member.id}")

            if memberDisplayName != display_Name_DB:
                updateNick(member.id, memberDisplayName)
                #print(f"UPDATED {member.id} to {memberDisplayName}")
                insert_audit_Logs(userId=228143014168625153, actionType=8, actionDate=datetime.datetime.now(),
                                  actionNote=f"UPDATED {member.id} NAME from {display_Name_DB} to {memberDisplayName}",
                                  affectedUsers=f"{member.id}")

            #print(F"HIGHEST RANK FOR {member.display_name} is {max_role_id}")

        else:
            member_ranks = [rank.id for rank in member.roles]
            if any(rank in db_rank_ids for rank in member_ranks):
                print(f"==========={member.display_name} MISSING FROM DB===========")
                add_user_todb(member.id,member.display_name,1,0,1,datetime.datetime.now(), "None")
                #DO SOMETHING!

    print("===FINISHED USER CHECK=")


@checkUsersMissingDb.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
checkUsersMissingDb.start()


#### members ready for rankup!
@tasks.loop(time=[time(hour=17, minute=1)]) #
async def checkIsInactiveList():
    print("START IsActive=0 checker!")
    active_users_list = get_all_inactive_users()

    rank_list = get_all_ranks()
    # print(rank_list)

    # db_rank_ids = [dbrank[2] for dbrank in rank_id_list]
    flex_rank_ids = [(dbrank[0], dbrank[2]) for dbrank in rank_list]
    # print(flex_rank_ids)
    sanity = bot.get_guild(301755382160818177)
    # sanity = bot.get_guild(305380209366925312) #test

    # print(rank_list)
    rank_ids = [rank[0] for rank in rank_list]
    int_index = [i for i in range(len(rank_ids))]
    rank_Name = [rank[1] for rank in rank_list]
    rank_discordId = [rank[2] for rank in rank_list]
    rank_points = [rank[3] for rank in rank_list]
    rank_diaryReq = [rank[4] for rank in rank_list]
    rank_masterdiaryReq = [rank[5] for rank in rank_list]
    rank_maintenancePoints = [rank[6] for rank in rank_list]

    gracePeriod = fetchranksGracePeriod()
    now = datetime.datetime.now()
    # print(now > gracePeriod)
    # print(gracePeriod)

    #channel = await bot.fetch_channel(get_channel("rank-updates"))

    # await channel.send("=================New Rank Update MSG==================")

    for member in active_users_list:
        # if member[1] == "Mike":
        member_disc = sanity.get_member(member[0])

        if member_disc:
            """print(f"{member_disc.display_name}")"""

            member_ranks = [rank.id for rank in member_disc.roles]
            # print(F"ROLES {member_ranks}")
            clan_ranks = [role for role in member_ranks if role in rank_discordId]
            if len(clan_ranks) != 0:

                # print(F"CLAN RANKS {clan_ranks}")
                # print(f"{member} FKS IT UP")
                max_role_id = max([flex_id[0] for flex_id in flex_rank_ids if flex_id[1] in clan_ranks])
                # ======================
                # their CURRENT role!

                # Now for calculating actual rank
                points = member[5]
                currentRank = member[4]
                join_date = member[7]
                diaryPoints = member[11]
                masterdiaryPoints = member[12]
                # print(points, currentRank,join_date, diaryPoints, masterdiaryPoints)

                # print(((diaryPoints >= rank_diaryReq[x]) or (masterdiaryPoints >= rank_masterdiaryReq[0])))
                userPointsLast2Month = getUserPointsPrevious2Month(member_disc.id)
                if not userPointsLast2Month:
                    userPointsLast2Month = 0

                userPointsLastMonth = getUserPointsPreviousMonth(member_disc.id)
                if not userPointsLastMonth:
                    userPointsLastMonth = 0

                # print(f"last month pts {userPointsLastMonth}")
                userPointsThisMonth = getUserPointsThisMonth(member_disc.id)
                if not userPointsThisMonth:
                    userPointsThisMonth = 0

                # print(f"current month pts {userPointsThisMonth}")
                maxMonthPoints = max(userPointsThisMonth, userPointsLastMonth, userPointsLast2Month)

                if maxMonthPoints > 50:
                    mycursor.execute(
                        f"update sanity2.users set isActive = 0 where userId = {member[0]}"
                    )
                    db.commit()
    print("FINISHED IsActive=0 checker!")

@checkIsInactiveList.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
checkIsInactiveList.start()


@tasks.loop(hours=1) #time=[time(hour=1, minute=49)]
async def updateUserStatsTable():
    print("started UpdateUserStats tasks")

    # --- API Configuration ---
    BASE_URL = "https://api.wiseoldman.net/v2/groups/230/gained"
    # 2. Get all existing display names and column names from the userStats table
    mycursor.execute("SELECT displayName FROM sanity2.userStats")
    db_players = {row[0] for row in mycursor.fetchall()}
    print(f"Found {len(db_players)} unique players in the database.")

    mycursor.execute("SHOW COLUMNS FROM sanity2.userStats")
    all_columns = [column[0] for column in mycursor.fetchall()]
    print(f"Found columns: {all_columns}")

    # This map helps convert parts of a column name to an API period
    periods_map = {"Weekly": "week"}  # Only processing weekly as per previous request

    # 3. Iterate through columns, parse them, fetch data, and update DB
    for column_name in all_columns:
        metric = None
        period = None

        # Attempt to parse the column name to find a period and metric
        for period_str, api_period in periods_map.items():
            if period_str in column_name:
                try:
                    # --- FIX: Parse the metric from the beginning of the column name ---
                    # Assumes format like {metric}Weekly... e.g., ehbWeeklyEhb or chambers_of_xericWeeklyEhb
                    metric_part = column_name.split(period_str)[0]
                    if metric_part:
                        # The metric for the API call is the part before the period string
                        metric = metric_part.lower()
                        period = api_period
                        break  # Found a match, stop searching this column name
                except IndexError:
                    continue

        if not metric or not period:
            print(f"\n--- Skipping column '{column_name}' (does not match naming convention) ---")
            continue

        print(f"\n--- Processing: {column_name} (Metric: {metric}, Period: {period}) ---")

        # 3a. Fetch data from the Wise Old Man API
        api_params = {"metric": metric, "period": period, "limit": 400}
        api_data = None
        try:
            response = requests.get(BASE_URL, params=api_params)
            response.raise_for_status()
            api_data = response.json()
            print(f"Successfully fetched data from API for metric '{metric}'.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400 and e.response.json().get("message") == "Invalid enum value for 'metric'.":
                print(f"Ignoring column '{column_name}': Invalid metric '{metric}' for WOM API.")
                continue
            print(f"HTTP Error fetching data for metric '{metric}': {e}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"A network error occurred: {e}")
            continue

        if api_data is None:  # Use is None to handle empty list case
            print(f"No data received from API for {column_name}. Skipping update.")
            continue

        # 3b. Update active players and zero out inactive players

        # Prepare data for active players
        values_to_update = []
        for player in api_data:
            display_name = player.get('player', {}).get('displayName')
            gained_value = player.get('data', {}).get('gained', 0)
            if display_name:
                values_to_update.append((display_name, gained_value))

        # Update the active players from the API data
        if values_to_update:
            sql_update_active = f"""
                        INSERT INTO sanity2.userStats (displayName, `{column_name}`)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE `{column_name}` = VALUES(`{column_name}`);
                    """
            mycursor.executemany(sql_update_active, values_to_update)
            db.commit()
            print(f"Successfully updated/inserted {mycursor.rowcount} active records for column '{column_name}'.")
        else:
            print(f"No active player data to update for column '{column_name}'.")

        # Find players in the DB who are NOT in the API response and set their value to 0
        api_player_names = {item[0] for item in values_to_update}
        inactive_players = db_players - api_player_names

        if inactive_players:
            print(f"Found {len(inactive_players)} inactive players to zero out for '{column_name}'.")
            sql_zero_out_inactive = f"UPDATE sanity2.userStats SET `{column_name}` = 0 WHERE displayName = %s"
            inactive_players_tuples = [(name,) for name in inactive_players]
            mycursor.executemany(sql_zero_out_inactive, inactive_players_tuples)
            db.commit()
            print(f"Successfully zeroed out {mycursor.rowcount} inactive records for column '{column_name}'.")
    print("finished updating userStats table")

@updateUserStatsTable.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
updateUserStatsTable.start()


def updateMiscRoleId(rolename:str, userId:int):
    mycursor.execute(
        f"update sanity2.miscRoles set userId = {userId} where roleName = '{rolename}'"
    )
    db.commit()

### get discordProfileUrl
@tasks.loop(time=[time(hour=6,minute=14)])
async def getMiscRoles():
    print("started getting discord misc")
    sanity_guild_id = 301755382160818177
    leaderRoleId = 301755450536361984
    motmRoleId = 360727972543594497
    motyRoleId = 1054807254668423240
    #officialsRoleId = 456561385896280085

    # 1. Get the guild and role objects
    sanity_guild = bot.get_guild(sanity_guild_id)
    if not sanity_guild:
        print(f"Error: Bot could not find guild with ID {sanity_guild_id}.")
        return

    leaderRole = sanity_guild.get_role(leaderRoleId)
    motmRoleId = sanity_guild.get_role(motmRoleId)
    motyRoleId = sanity_guild.get_role(motyRoleId)

    for member in leaderRole.members:
        updateMiscRoleId("leader",member.id)

    for member in motmRoleId.members:
        updateMiscRoleId("motm", member.id)

    for member in motyRoleId.members:
        updateMiscRoleId("moty",member.id)
@getMiscRoles.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
getMiscRoles.start()

### get discordProfileUrl
@tasks.loop(time=[time(hour=6,minute=4)])
async def getDiscordImageUrl():
    print("started getting discord image url")
    sanity_guild_id = 301755382160818177
    sanity_role_id = 1240423750394970193
    users_table = "users"
    profile_url_table = "discordProfileImageUrl"

    # --- Logic ---
    try:
        # 1. Get the guild and role objects
        sanity_guild = bot.get_guild(sanity_guild_id)
        if not sanity_guild:
            print(f"Error: Bot could not find guild with ID {sanity_guild_id}.")
            return

        sanity_role = sanity_guild.get_role(sanity_role_id)
        if not sanity_role:
            print(f"Error: Could not find role with ID {sanity_role_id} in the guild.")
            return

        # 2. --- NEW: Fetch all existing user IDs from the parent 'users' table ---
        mycursor.execute(f"SELECT userId FROM sanity2.{users_table}")
        # Store IDs in a set for very fast lookups
        existing_user_ids = {row[0] for row in mycursor.fetchall()}
        print(f"Found {len(existing_user_ids)} users in the '{users_table}' table to check against.")

        # 3. Get members with the role
        members_with_role = sanity_role.members
        if not members_with_role:
            print("No members found with the specified role.")
            return

        # 4. Prepare profile picture data, skipping members who are not in the users table
        profile_url_data_to_update = []
        skipped_count = 0
        for member in members_with_role:
            # Check if the member's ID exists in our set of users
            if member.id in existing_user_ids:
                profile_url_data_to_update.append((member.id, member.display_avatar.url))
            else:
                # If not, skip them and print a notice
                print(f"Skipping {member.id} (ID: {member.id}) - not found in '{users_table}'.")
                skipped_count += 1

        print(f"Prepared to update {len(profile_url_data_to_update)} members. Skipped {skipped_count} members.")

        # 5. Execute the database query if there is data to update
        if profile_url_data_to_update:
            sql_update_urls = f"""
                    INSERT INTO sanity2.{profile_url_table} (userId, discordProfileImageUrl)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE discordProfileImageUrl = VALUES(discordProfileImageUrl)
                """
            mycursor.executemany(sql_update_urls, profile_url_data_to_update)

            # 6. Commit the changes to the database
            db.commit()

            print(f"Database updated successfully. {mycursor.rowcount} rows were affected in '{profile_url_table}'.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        db.rollback()

@getDiscordImageUrl.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
getDiscordImageUrl.start()

#### members ready for rankup!
@tasks.loop(time=[time(hour=18, minute=1)]) #
async def checkRankUps():
    print("START CheckRankUPS!")

    active_users_list = get_all_active_users()
    #get tuple of ranks!

    rank_list = get_all_ranks()
    #print(rank_list)

    #db_rank_ids = [dbrank[2] for dbrank in rank_id_list]
    flex_rank_ids = [(dbrank[0], dbrank[2]) for dbrank in rank_list]
    #print(flex_rank_ids)
    sanity = bot.get_guild(301755382160818177)
    #sanity = bot.get_guild(305380209366925312) #test

    #print(rank_list)
    rank_ids = [rank[0] for rank in rank_list]
    int_index = [i for i in range(len(rank_ids))]
    rank_Name = [rank[1] for rank in rank_list]
    rank_discordId = [rank[2] for rank in rank_list]
    rank_points = [rank[3] for rank in rank_list]
    rank_diaryReq = [rank[4] for rank in rank_list]
    rank_masterdiaryReq = [rank[5] for rank in rank_list]
    rank_maintenancePoints = [rank[6] for rank in rank_list]

    gracePeriod = fetchranksGracePeriod()
    now = datetime.datetime.now()
    #print(now > gracePeriod)
    #print(gracePeriod)

    channel = await bot.fetch_channel(get_channel("rank-updates"))

    #await channel.send("=================New Rank Update MSG==================")

    for member in active_users_list:
        #if member[1] == "Mike":
        member_disc = sanity.get_member(member[0])

        if member_disc:
            """print(f"{member_disc.display_name}")"""

            member_ranks = [rank.id for rank in member_disc.roles]
            #print(F"ROLES {member_ranks}")
            clan_ranks = [role for role in member_ranks if role in rank_discordId]
            if len(clan_ranks) != 0:

                #print(F"CLAN RANKS {clan_ranks}")
                #print(f"{member} FKS IT UP")
                max_role_id = max([flex_id[0] for flex_id in flex_rank_ids if flex_id[1] in clan_ranks])
                #======================
                #their CURRENT role!


                #Now for calculating actual rank
                points = member[5]
                currentRank = member[4]
                join_date = member[7]
                diaryPoints = member[11]
                masterdiaryPoints = member[12]
                #print(points, currentRank,join_date, diaryPoints, masterdiaryPoints)



                #print(((diaryPoints >= rank_diaryReq[x]) or (masterdiaryPoints >= rank_masterdiaryReq[0])))
                userPointsLast2Month = getUserPointsPrevious2Month(member_disc.id)
                if not userPointsLast2Month:
                    userPointsLast2Month = 0

                userPointsLastMonth = getUserPointsPreviousMonth(member_disc.id)
                if not userPointsLastMonth:
                    userPointsLastMonth = 0

                #print(f"last month pts {userPointsLastMonth}")
                userPointsThisMonth = getUserPointsThisMonth(member_disc.id)
                if not userPointsThisMonth:
                    userPointsThisMonth = 0

                #print(f"current month pts {userPointsThisMonth}")
                maxMonthPoints = max(userPointsThisMonth,userPointsLastMonth,userPointsLast2Month)
                #print(f"max {maxMonthPoints}")

                """print(f"{member_disc.display_name} points last month = {userPointsLastMonth}")"""
                calculated_rank = max([x for x in int_index if points >= rank_points[x] and ((diaryPoints >= rank_diaryReq[x]) or (masterdiaryPoints >= rank_masterdiaryReq[x])) and (maxMonthPoints >= rank_maintenancePoints[x])]) #
                #print(f"{member_disc.display_name} LONG STUFF {rank_list[calculated_rank][0]} ")

                #print("=================================")
                #if member_disc.id == 143306878779260929:
                    #print("TIIIIIIIZKU=====================")
                #print(f"embedVariable {member_disc.display_name} rank change MemberdiscID {member_disc.id} Previous rankID {max_role_id}) New rankID {rank_list[calculated_rank][0]}")

                #print(calculated_rank)
                #rankdown
                if max_role_id > rank_list[calculated_rank][0] and now > gracePeriod and int(max_role_id) != 1: #DEMOTE
                    #PROPOSE RANK CHANGE

                    #check if demotions delayed
                    check = readytodemotecheck(member_disc.id)
                    if check == True: #DEMOTE
                        view = rankChangerView()

                        old_rank_name = [id[1] for id in rank_list if id[0] == max_role_id][0]
                        new_rank_name = [id[1] for id in rank_list if id[0] == rank_list[calculated_rank][0]][0]

                        embed = embedVariable(f"<:rankdown:1302709875905794088> {member_disc.display_name} rank change",discord.Colour.yellow(),("MemberdiscID",member_disc.id), ("Previous rankID",max_role_id), ("New rankID", rank_list[calculated_rank][0]),("Old rank name",old_rank_name),("New rank name",new_rank_name))

                        await channel.send(embed=embed, view=view)
                #rankup
                elif max_role_id < rank_list[calculated_rank][0] and int(max_role_id) != 1: #PROMOTE
                    #PROPOSE RANK CHANGE
                    view = rankChangerView()

                    old_rank_name = [id[1] for id in rank_list if id[0] == max_role_id][0]
                    new_rank_name = [id[1] for id in rank_list if id[0] == rank_list[calculated_rank][0]][0]



                    embed = embedVariable(f"<:rankup:1302709869744230522> {member_disc.display_name} rank change",discord.Colour.yellow(),("MemberdiscID",member_disc.id), ("Previous rankID",max_role_id), ("New rankID", rank_list[calculated_rank][0]),
                                              ("Old rank name",old_rank_name),("New rank name",new_rank_name))
                    await channel.send(embed=embed, view=view)

            else:
                print(f"{member[0]} IS IN SERVer -> BUT NO ROLES")  # -> set to -1
                mycursor.execute(
                    f"update sanity2.users set isActive = 0, rankId = -1, leaveDate = '{datetime.datetime.now()}' where userId = {member[0]}"
                )
                db.commit()

                now = datetime.datetime.now()
                insert_audit_Logs(228143014168625153, 8, now, f"{member[0]} has left disc", member[0])

        else:
            print(f"{member[0]} IS MISSING FROM SANITY DISC SERVER") #-> set to -1
            mycursor.execute(
                f"update sanity2.users set isActive = 0, rankId = -1, leaveDate = '{datetime.datetime.now()}' where userId = {member[0]}"
            )
            db.commit()

            now = datetime.datetime.now()
            insert_audit_Logs(228143014168625153,8,now,f"{member[0]} has left disc",member[0])

    print("FINISHED checkRankUPS")


@checkRankUps.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
checkRankUps.start()



@tasks.loop(time=[time(hour=18, minute=5)])
async def nitroPoints():
    # check if day = first of month
    dayOfMonth = datetime.datetime.now().day
    if dayOfMonth == 1:
        mycursor.execute(
            f"select * from sanity2.pointtracker p where notes = 'nitro points' and (MONTH(date) = month(now()) and year(date) = year(now()))"
        )
        nitroPointsGiven = mycursor.fetchall()
        print(f"LEN NITROPOINTS {len(nitroPointsGiven)}")

        if len(nitroPointsGiven) < 2:
            print("START NITRO POINTS!")


            sanity = bot.get_guild(301755382160818177)
            nitro_role = sanity.get_role(586808186003259404)
            role_member_ids = [member.id for member in nitro_role.members]
            #print(f"OLD ID LIST {role_member_ids}")

            clannies_names, new_id_list = turnListOfIds_into_names(role_member_ids)
            #print(f"NEW ID LIST {new_id_list}")

            for member_id in new_id_list:
                #give nitro points
                #print(member_id)
                update_user_points(member_id,50)
                insert_Point_Tracker(member_id,50,datetime.datetime.now(),"nitro points")

                #add points -> add into point tracker for each user

            insert_audit_Logs(userId=979856389868494898,actionType=8,actionDate=datetime.datetime.now(),actionNote="Added monthly nitro points!")
            print("FINISHED NITRO POINTS")

@nitroPoints.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
nitroPoints.start()


class rankChangerView(View):  # for council / drop acceptors etc in #posted-drops
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction):
        mycursor.execute(
            "select discordRoleId,name from sanity2.roles where adminCommands = 1"
        )
        data = mycursor.fetchall()
        list = [i[0] for i in data]

        interaction_user_roleID_list = [role.id for role in interaction.user.roles]

        check = any(role in interaction_user_roleID_list for role in list)
        return check

    @button(label="Assign Rank", custom_id="acceptor-accept-button-4" ,style=discord.ButtonStyle.green, emoji="✅")
    async def assignrank(self, button: Button, interaction: discord.Interaction):
        channel = interaction.message.channel
        msg_to_edit = await channel.fetch_message(interaction.message.id)
        for embed in msg_to_edit.embeds:
            embed_dict = embed.to_dict()

        now = datetime.datetime.now()
        #title = int(str(embed_dict["title"]))
        memberId = int(embed_dict["fields"][0]["value"])
        previousRankId = int(embed_dict["fields"][1]["value"])
        newRankId = int(embed_dict["fields"][2]["value"])

        #print(memberId, previousRankId, newRankId)


        embed = discord.Embed.from_dict(embed_dict)

        embed.color = discord.Color.green()

        rank_ids = get_all_ranks()
        db_rank_ids = [dbrank[2] for dbrank in rank_ids]
        #print(db_rank_ids)

        sanity = bot.get_guild(301755382160818177)
        member = sanity.get_member(int(memberId))

        mycursor.execute(
            f"select discordRoleId from sanity2.ranks where id = {newRankId}"
        )
        New_rank_id = mycursor.fetchall()[0][0]
        new_role = sanity.get_role(int(New_rank_id))


        #ref points
        """if newRankId == 3: #if advanced/3 add points
            refs = getUserRefs(memberId)
            if refs:
                await interaction.channel.send(f"Added ref points for {member.display_name} refs - {refs}")"""

        #fix member roles
        await member.add_roles(new_role)

        for rankId in db_rank_ids:
            # get role and remove from user
            role = sanity.get_role(rankId)
            member_roles = [role.id for role in member.roles]

            if rankId != new_role.id and rankId in member_roles:
                await member.remove_roles(role)

        insert_audit_Logs(interaction.user.id, 5, now, f"updated {member.id} RANK from {previousRankId} to {newRankId}",member.id)
        updateUserRank(member.id,newRankId)

        await interaction.message.edit(embed=embed,view=None)
        #await interaction.response.send_message("drop accepted and points given",)


    @button(label="Delay until next month", custom_id="acceptor-decline-button-5", style=discord.ButtonStyle.danger, emoji="✖️")
    async def removeSubmission(self, button: Button, interaction: discord.Interaction):
        channel = interaction.message.channel
        msg_to_edit = await channel.fetch_message(interaction.message.id)
        for embed in msg_to_edit.embeds:
            embed_dict = embed.to_dict()

        memberId = int(embed_dict["fields"][0]["value"])

        embed = discord.Embed.from_dict(embed_dict)
        embed.color = discord.Color.red()

        await interaction.message.edit(embed=embed,view=None)

        insertRankUpDelay(memberId)
        #await interaction.response.send_message("The submission has been removed")


class Loops(commands.Cog):
    def __init__(self, bot):
        self.client = bot

    @discord.slash_command(guild_ids=[301755382160818177], name="checkrank",
                           description="checkrank test")
    async def checkrank(self, ctx, membercheck: discord.Member, rankidcheck: int):

        active_users_list = get_all_active_users()

        rankidcheck += 1

        for member in active_users_list:
            if member[0] == membercheck.id:
                sanity = ctx.guild
                member_disc = sanity.get_member(member[0])
                # print("START CheckRankUPS!")

                rank_list = get_all_ranks()
                # print(rank_list)

                # db_rank_ids = [dbrank[2] for dbrank in rank_id_list]
                flex_rank_ids = [(dbrank[0], dbrank[2]) for dbrank in rank_list]
                # print(flex_rank_ids)
                # sanity = bot.get_guild(301755382160818177)
                # sanity = bot.get_guild(305380209366925312) #test

                # print(rank_list)
                rank_ids = [rank[0] for rank in rank_list]
                # print(F"RANK IDS: {rank_ids}")
                int_index = [i for i in range(len(rank_ids))]
                rank_Name = [rank[1] for rank in rank_list]
                rank_discordId = [rank[2] for rank in rank_list]
                rank_points = [rank[3] for rank in rank_list]
                rank_diaryReq = [rank[4] for rank in rank_list]
                rank_masterdiaryReq = [rank[5] for rank in rank_list]
                rank_maintenancePoints = [rank[6] for rank in rank_list]

                gracePeriod = fetchranksGracePeriod()
                now = datetime.datetime.now()
                # print(now > gracePeriod)
                # print(gracePeriod)

                # channel = await bot.fetch_channel(get_channel("rank-updates"))

                # await channel.send("=================New Rank Update MSG==================")

                member_disc = membercheck

                if member_disc:
                    """print(f"{member_disc.display_name}")"""

                    member_ranks = [rank.id for rank in member_disc.roles]
                    # print(F"ROLES {member_ranks}")
                    clan_ranks = [role for role in member_ranks if role in rank_discordId]
                    if len(clan_ranks) != 0:

                        # print(F"CLAN RANKS {clan_ranks}")
                        # print(f"{member} FKS IT UP")
                        max_role_id = max([flex_id[0] for flex_id in flex_rank_ids if flex_id[1] in clan_ranks])
                        print(f"MAX ROLE ID: {max_role_id}")
                        # ======================
                        # their CURRENT role!

                        # Now for calculating actual rank
                        points = member[5]
                        currentRank = member[4]
                        join_date = member[7]
                        diaryPoints = member[11]
                        masterdiaryPoints = member[12]
                        # print(points, currentRank,join_date, diaryPoints, masterdiaryPoints)

                        # print(((diaryPoints >= rank_diaryReq[x]) or (masterdiaryPoints >= rank_masterdiaryReq[0])))
                        userPointsLast2Month = getUserPointsPrevious2Month(member_disc.id)
                        if not userPointsLast2Month:
                            userPointsLast2Month = 0

                        userPointsLastMonth = getUserPointsPreviousMonth(member_disc.id)
                        if not userPointsLastMonth:
                            userPointsLastMonth = 0

                        # print(f"last month pts {userPointsLastMonth}")
                        userPointsThisMonth = getUserPointsThisMonth(member_disc.id)
                        if not userPointsThisMonth:
                            userPointsThisMonth = 0

                        # print(f"current month pts {userPointsThisMonth}")
                        maxMonthPoints = max(userPointsThisMonth, userPointsLastMonth, userPointsLast2Month)
                        # print(f"max {maxMonthPoints}")
                        # print(type(maxMonthPoints))
                        # print(maxMonthPoints>150)

                        """print(f"{member_disc.display_name} points last month = {userPointsLastMonth}")"""
                        calculated_rank = max([x for x in int_index if points >= rank_points[x] and (
                                (diaryPoints >= rank_diaryReq[x]) or (
                                    masterdiaryPoints >= rank_masterdiaryReq[x])) and (
                                                       maxMonthPoints >= rank_maintenancePoints[x])])  #
                        # print(f"{member_disc.display_name} LONG STUFF {rank_list[calculated_rank][0]} ")

                        # print("=================================")
                        # if member_disc.id == 143306878779260929:
                        # print("TIIIIIIIZKU=====================")
                        # print(f"embedVariable {member_disc.display_name} rank change MemberdiscID {member_disc.id} Previous rankID {max_role_id}) New rankID {rank_list[calculated_rank][0]}")

                        # print(calculated_rank)
                        # rankdown
                        # if max_role_id > rank_list[calculated_rank][0] and now > gracePeriod and int(max_role_id) != 1:  # DEMOTE
                        # PROPOSE RANK CHANGE

                        # check if demotions delayed
                        check = readytodemotecheck(member_disc.id)
                        # if check == True:  # DEMOTE
                        old_rank_name = [id[1] for id in rank_list if id[0] == max_role_id][0]
                        new_rank_name = [id[1] for id in rank_list if id[0] == rank_list[calculated_rank][0]][0]

                        #### REASON TO DERANK

                        embed = embedVariable(f"{member_disc.display_name} rank check",
                                              discord.Colour.yellow(), ("MemberdiscID", member_disc.id),
                                              ("Previous rankID", max_role_id),
                                              ("New rankID", rank_list[calculated_rank][0]),
                                              ("Old rank name", old_rank_name), ("New rank name", new_rank_name),
                                              ("Points", f"{points}/{rank_points[rankidcheck]}"),
                                              ("Maintenance points (max of past 3 months", {maxMonthPoints}),
                                              ("Diary pts", f"{diaryPoints}/{rank_diaryReq[rankidcheck]}"),
                                              ("Master diary pts",
                                               f"{masterdiaryPoints}/{rank_masterdiaryReq[rankidcheck]}"))

                        await ctx.respond(embed=embed)



def setup(bot):
    bot.add_cog(Loops(bot))