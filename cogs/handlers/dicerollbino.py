import datetime
import discord
from discord.ext import commands, bridge, tasks
from discord.ext.commands import has_any_role
from matplotlib import pyplot as plt
import pandas as pd
from cogs.handlers.DatabaseHandler import get_all_ranks, testingservers, get_adminCommands_roles, mycursor, db, \
    bingoModeCheck
from random import randint
from bot import bot
from PIL import Image, ImageDraw,ImageFont

def descriptionOnlyEmbed(desc : str, title : str = None):
    if title:
        embed = discord.Embed(
            title=title,
            description=desc,
            colour=discord.Colour.blue()
        )
    else:
        embed = discord.Embed(
            description=desc,
            colour=discord.Colour.blue()
        )

    return embed

def completeTile(tileId:int,teamName:str): #NEED TO BE TESTED
    mycursor.execute(
        f"update dicerollbingo.rolls set tileDone = 1 where endTile = {tileId} and teamName = '{teamName}'"
    )
    db.commit()

def getTileInfo(tileId:int):
    mycursor.execute(
        f"select * from dicerollbingo.tiles where tileId = {tileId}"
    )
    data = mycursor.fetchall()
    print(f"TILeID GETINFODATA {tileId}")
    print(F"GET TILEFINFODATA: {data}")
    return data[0]

def getUnDoneTiles(teamName:str):
    mycursor.execute(
        f"select * from dicerollbingo.rolls where tileDone = 0 and teamName = '{teamName}'"
    )
    data = mycursor.fetchall()
    print(f"getUnDoneTiles{data}")
    return data


def getUsersTeamName(userId:int):
    mycursor.execute(
        f"select * from dicerollbingo.teamTable where teamMemberIds like '%{userId}%'"
    )
    data = mycursor.fetchall()
    if data:
        #print(data)
        return data[0][0]
    else:
        return None

def updateTeamPosition(teamName:str, newPosition:int):
    mycursor.execute(
        f"update dicerollbingo.teamTable set position = {newPosition} where teamName = '{teamName}'"
    )
    db.commit()

def getCurrentTeamTile(teamName:str):
    mycursor.execute(
        f"select * from dicerollbingo.teamTable where teamname = '{teamName}'"
    )
    data = mycursor.fetchall()
    return data[0][2]

def insertRollToDB(teamName:str,roll:int, startTile:int, endTile:int):

    now = datetime.datetime.now()

    mycursor.execute(
        "insert into dicerollbingo.rolls (teamName, diceRoll,startTile, endTile,timestamp)"
        "VALUES (%s,%s,%s,%s,%s)",
        (teamName, roll, startTile, endTile,now)
    )

    db.commit()

    return mycursor.lastrowid

def updateTileProgress(rollId:int,newAmountReceived:int,DropIds:str,tileDone=None):
    if tileDone == True:
        mycursor.execute(
            f"update dicerollbingo.rolls set dropAmountReceived = {newAmountReceived}, tileDone = 1, dropId='{DropIds}' where rollid = {rollId} "
        )
        db.commit()
    else:
        mycursor.execute(
            f"update dicerollbingo.rolls set dropAmountReceived = {newAmountReceived}, dropId='{DropIds}' where rollid = {rollId} "
        )
        db.commit()


def checkTileDropAmount(dropName:str, teamName:str):
    mycursor.execute(
        f"select r.rollId,r.teamName,r.endTile,r.tileDone,r.dropId,r.dropAmountReceived,t.dropAmountReq,t.dropItems  from dicerollbingo.rolls r "
        f" left join dicerollbingo.tiles t on t.tileId = r.endTile where r.tileDone = 0 and  teamName = '{teamName}' and dropItems like '%{dropName}%'"
    )
    data = mycursor.fetchall()
    return data

@tasks.loop(seconds=60)
async def diceRollBingoDropFixer():
    """ Do stuff in SQL
    1. check drops submitted past x time
    2. assign dropIds to rolls
    3. add count of received items for rolsl
    4. if received drop count = count req for a roll = tile complete"""

    bingoVal = bingoModeCheck()
    # print(bingoVal)
    if bingoVal == 1:
        mycursor.execute(
            f"select s.* from sanity2.submissions s where not EXISTS ( select dropId from dicerollbingo.rolls r "
            f"where FIND_IN_SET(s.Id, r.dropId) > 0) and bingo = 1 and status = 2 and submittedDate >= NOW() - INTERVAL 2 HOUR"
        )
        bingoDropsPastHour = mycursor.fetchall()
        #print(len(bingoDropsPastHour))

        for drop in bingoDropsPastHour:
            #print(f"dicerollbingoloop userid {drop[1]} {drop[7]}")
            teamName = getUsersTeamName(drop[1])
            matchedRollTile = checkTileDropAmount(drop[7],teamName)
            #print(matchedRollTile)
            if matchedRollTile:
                #print("IS HERE")
                amountReceived = matchedRollTile[0][5]
                #print(F"AMOUNT RECeIVED {amountReceived}")
                amountReq = matchedRollTile[0][6]
                #print(F" AMOUNT REQ {type(amountReq)}")
                dropIds = matchedRollTile[0][4]
                if dropIds:
                    dropIds = f"{dropIds},{drop[0]}"
                else:
                    dropIds = drop[0]

                #print(dropIds)

                if amountReceived+1 >= amountReq:
                    #print("SHOULD BE DONE HERE")
                    updateTileProgress(matchedRollTile[0][0],amountReceived+1,dropIds,True)
                else:
                    updateTileProgress(matchedRollTile[0][0], amountReceived + 1,dropIds)


def calculate_position(tile_number):
    """Calculate x,y coordinates for a given tile number in zigzag pattern"""

    TILE_WIDTH = 170
    TILE_HEIGHT = 170
    BOARD_COLS = 6
    BOARD_ROWS = 8
    START_X = 825
    START_Y = 1235

    # Calculate row and column (0-based)
    row = (tile_number - 1) // BOARD_COLS
    col = (tile_number - 1) % BOARD_COLS

    # Reverse column for even rows (right-to-left)
    if row % 2 == 1:
        col = (BOARD_COLS - 1) - col

    x = START_X + col * TILE_WIDTH
    y = START_Y - row * TILE_HEIGHT

    return x, y

def getCurrentTileStatus(teamName:str, tileId:int):
    mycursor.execute(
        f"select * from dicerollbingo.rolls r where endTile = {tileId} and teamName = '{teamName}' and tileDone = 0"
    )
    data = mycursor.fetchall()
    if data:
        return data
    else:
        return None

@diceRollBingoDropFixer.before_loop  # REMOVES
async def before():
    await bot.wait_until_ready()
diceRollBingoDropFixer.start()


class dicerollbino(commands.Cog):
    def __init__(self, bot):
        self.client = bot

    admin_roles = get_adminCommands_roles()
    admin_roles_ids = [role[1] for role in admin_roles]

    all_ranks = get_all_ranks()
    rank_ids = [rank[2] for rank in all_ranks]

    @bridge.bridge_command(guild_ids=testingservers)
    @has_any_role(*admin_roles_ids)
    async def completetile(self, ctx, tile:int,team:str):
        """Compelte a tile manually if bot is stuck"""

        completeTile(tile,team)

        await ctx.respond(f"Tile `{tile}` has been manually marked as complete for `{team}`.")

    @bridge.bridge_command(guild_ids=testingservers)
    @has_any_role(*rank_ids)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def bingochart(self, ctx):
        """show progression over time"""

        REFERENCE_TIME = datetime.datetime(2025, 4, 19, 16, 0)  # 18:00 on April 19, 2025 #starttime of bingo
        mycursor.execute("SELECT teamName, endTile, timestamp FROM dicerollbingo.rolls ORDER BY teamName, timestamp")
        results = mycursor.fetchall()
        # print(results)

        # Read data into a pandas DataFrame
        df = pd.DataFrame(results, columns=['teamName', 'endTile', 'timestamp'])

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Calculate hours since reference time
        df['hours_since_ref'] = (df['timestamp'] - REFERENCE_TIME).dt.total_seconds() / 3600

        # Create the plot
        plt.figure(figsize=(12, 7))

        # Group by team and plot each team's progression
        for team, group in df.groupby('teamName'):
            plt.plot(group['hours_since_ref'], group['endTile'],
                     marker='o', label=team, linestyle='-')

        # Customize the plot
        plt.title(f'Team Progression: End Tile Since {REFERENCE_TIME.strftime("%H:%M %d %b %Y")}', fontsize=14)
        plt.xlabel(f'Hours since bingo start', fontsize=12)
        plt.ylabel('End Tile Position', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)

        # Add reference time marker
        plt.axvline(x=0, color='gray', linestyle=':', alpha=0.5)
        plt.text(0.1, plt.ylim()[1] * 0.95, 'Reference time', color='gray', alpha=0.7)

        # Add legend
        plt.legend(title='Team Name', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Adjust layout
        plt.tight_layout()

        # Save the plot instead of showing it
        output_filename = 'imgs/team_progression.png'
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        plt.close()

        file = discord.File("imgs/team_progression.png")
        await ctx.respond(file=file)


    @bridge.bridge_command(guild_ids=testingservers)
    @has_any_role(*rank_ids)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def board(self, ctx):
        """show bingo board"""
        base_img = Image.open(r"imgs/sanityDiceRollboardv1.png")
        image_editable = ImageDraw.Draw(base_img)

        mycursor.execute(
            f"select * from dicerollbingo.teamTable tt left join dicerollbingo.teamColor tc on tc.teamName = tt.teamName order by position desc"
        )
        teamsInfo = mycursor.fetchall()

        count = 0
        prevTile = 100
        sameTile = 0
        font = "imgs/Roboto-Medium.ttf"
        rsnFont = ImageFont.truetype(font, 55)

        for team in teamsInfo:
            """
            1. put teams on side for info
            2. put teams on board"""

            teamName = team[0]
            teamPosition = team[2]
            teamColor = team[4]

            #teams on side 350x, 720y text size
            points_img = Image.open(fr"imgs/{teamColor}piece.png")
            base_img.paste(points_img, (50, 720+count*65), points_img)
            image_editable.text((50+35, 735+count*65), f"{teamName} - {teamPosition}",font=rsnFont, fill=(0, 0, 0), anchor="lt")  # black shadow/outline
            image_editable.text((50+35, 735+count*65), f"{teamName} - {teamPosition}",font=rsnFont, fill=(167, 239, 252), anchor="lt")  # actual text

            #put in brick on board - 812 1230
            x,y = calculate_position(teamPosition)
            print(teamPosition)
            print(x,y)
            if prevTile == teamPosition and teamPosition != 0:
                #offset right+down
                points_img = Image.open(fr"imgs/{teamColor}piece.png")
                base_img.paste(points_img, (x+35*(sameTile+1), y), points_img)
                sameTile += 1

            else: #normal position. default 170 wide 170 tall
                points_img = Image.open(fr"imgs/{teamColor}piece.png")
                base_img.paste(points_img, (x,y), points_img)
                sameTile = 0


            prevTile = teamPosition
            count += 1

        base_img.save("imgs/bingoboard.png")
        file = discord.File("imgs/bingoboard.png")

        await ctx.respond(file=file)

    @bridge.bridge_command(guild_ids=testingservers)
    @has_any_role(*rank_ids)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def progress(self, ctx, user : discord.Member = None):
        """progress of a team / undone tiles"""
        if not user:
            user = ctx.author
        teamName = getUsersTeamName(user.id)
        if not teamName:
            await ctx.respond(f"{user.mention} is are not in a bingo team (or someone fked up teams)")

        else:
            currentTile = getCurrentTeamTile(teamName)
            unDoneTiles = getUnDoneTiles(teamName)
            print(f"len undoentiles team{teamName} : {len(unDoneTiles)}")

            # check if uncompleted tiles -> allow to roll ahead as drop approval can be delayed
            unDoneTiletext = ""
            if len(unDoneTiles) > 0:

                for tile in unDoneTiles:
                    print(f"TILE [3] test {tile[4]}")
                    tileId, tileType, snakeLadderTile, bossName, dropDescription, dropAmountReq, dropItems = getTileInfo(tile[4])

                    tilestatus = getCurrentTileStatus(teamName, tileId)
                    try:
                        amountReceived = tilestatus[0][7]
                        dropIds = tilestatus[0][6]
                    except:
                        amountReceived = 0
                        dropIds = 'None'
                    unDoneTiletext += f"{tileId}․ **{bossName}**: {dropDescription} - `{amountReceived}/{dropAmountReq}` \n dropIds: {dropIds} \n"
                # print text saynig which tiles are uncompleted - if error -> council manual complete

            embed = descriptionOnlyEmbed(title=f"{teamName} tiles",desc=f"{teamName} is currently on tile `{currentTile}`\n"
                                             f"Tiles in progress/awaiting drop approval: \n{unDoneTiletext}\n\n"
                                             f"If tiles are not completed @ drop approvers or council to manually `/completetile tile# {teamName}`")

            await ctx.respond(embed=embed)


    @bridge.bridge_command(guild_ids=testingservers)
    @has_any_role(*rank_ids)
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def roll(self, ctx):
        """Roll dice bingo roller"""

        #check which team -> check if team tile done (allow 2 tiles headroom for approval)
        teamName = getUsersTeamName(ctx.author.id)
        if not teamName:
            await ctx.respond(f"{ctx.author.mention} you are not in a bingo team (or someone fked up teams)")

        else:
            currentTile = getCurrentTeamTile(teamName)
            unDoneTiles = getUnDoneTiles(teamName)
            print(f"len undoentiles team{teamName} : {len(unDoneTiles)}")

            #check if uncompleted tiles -> allow to roll ahead as drop approval can be delayed
            if len(unDoneTiles) > 1:
                unDoneTiletext = ""
                for tile in unDoneTiles:
                    print(f"TILE [3] test {tile[4]}")
                    tileId, tileType, snakeLadderTile, bossName, dropDescription, dropAmountReq, dropItems = getTileInfo(tile[4])
                    unDoneTiletext += f"{tileId}․ **{bossName}**: {dropDescription}\n"
                #print text saynig which tiles are uncompleted - if error -> council manual complete

                embed = descriptionOnlyEmbed(f"Cannot roll until {teamName} completes your current tiles:\n"
                                  f"{unDoneTiletext}\n"
                                  f"If this a mistake ask drop approvers to approve drop or council to manually /completetile tile# {teamName}")

                await ctx.respond(embed=embed)

            #if
            else:
                print(currentTile)
                if currentTile == 0:
                    roll = 1
                else:
                    roll = randint(1,6) #if roll too high

                print(f"ROLL ROLLED {roll}")

                #calc endTile + some text about hitting ladder/snake
                startTile = getCurrentTeamTile(teamName)
                print(f"getEndTile1 {startTile}")

                if (startTile + roll) > 48:
                    newTile = 48-(startTile+roll-48)
                else:
                    newTile = startTile + roll


                tileId, tileType, snakeLadderTile, bossName, dropDescription, dropAmountReq, dropItems = getTileInfo(newTile)

                print(f"TEST SNAKER LADDER TILEEEEEEEEEE {snakeLadderTile}")

                if tileType != "drop":
                    if tileType == "snake":
                        bonusTextSnakeLadder = f"Whoops {teamName} hit a :game_die:{roll}:game_die: and landed on a 🐍snake🐍 and went back to tile {snakeLadderTile}!"
                        tileId, tileType, newTileSnake, bossName, dropDescription, dropAmountReq, dropItems = getTileInfo(snakeLadderTile)
                        print(f"TEST SNAKER LADDER TILEEEEEEEEEE {tileId}")
                        rollId = insertRollToDB(teamName, roll, startTile, tileId)
                        updateTeamPosition(teamName, tileId)

                        embed = descriptionOnlyEmbed(title=f"{teamName} roll #{rollId}",desc=f"{bonusTextSnakeLadder}. \n\n "
                               f"{teamName}'s current tile is **{bossName}** - `{dropAmountReq}x` `{dropDescription}`. \n\n Avaiable drops: `{dropItems}`")

                    elif tileType == "ladder":
                        bonusTextSnakeLadder = f"Whoop Whoop {teamName} hit a :game_die:{roll}:game_die: and landed on a 🪜ladder🪜 and went up to tile {snakeLadderTile}!"
                        tileId, tileType, newTileLadder, bossName, dropDescription, dropAmountReq, dropItems = getTileInfo(snakeLadderTile)
                        print(f"TEST SNAKER LADDER TILEEEEEEEEEE {tileId}")
                        rollId = insertRollToDB(teamName, roll, startTile, tileId)
                        updateTeamPosition(teamName, tileId)

                        embed = descriptionOnlyEmbed(title=f"{teamName} roll #{rollId}", desc=f"{bonusTextSnakeLadder}. \n\n "
                                                                                    f"{teamName}'s current tile is **{bossName}** - `{dropAmountReq}x` `{dropDescription}`. \n\n Avaiable drops: `{dropItems}`")
                    else:
                        embed = descriptionOnlyEmbed(desc="Something broke")

                else:
                    #text about new tile
                    updateTeamPosition(teamName, newTile)
                    rollId = insertRollToDB(teamName, roll, startTile, tileId)
                    embed = descriptionOnlyEmbed(title=f"{teamName} roll #{rollId}", desc=f"{teamName} hit a :game_die:{roll}:game_die: and hit tile `{newTile}` **{bossName}** - `{dropAmountReq}x` `{dropDescription}`. \n\n Avaiable drops: `{dropItems}`")


                await ctx.respond(embed=embed)












def setup(bot):
    bot.add_cog(dicerollbino(bot))