# start.py
# By: PVCPipe01
# contains the start command

import discord
import os
from discord.ext import commands

import math
import random
import asyncio
import urllib.request
from urllib.request import urlopen
from PIL import Image
import time
import aiorwlock
import operator
import pickle

import globalValues

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX
WINNER_INDEX = globalValues.WINNER_INDEX

##############################################################################################################################################

async def start(ctx, arg):

    name = arg

    accessState = -1
    errorCode = -1

    brawl = None
    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        if not globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name):
            errorCode = 5

        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 0:
            errorCode = 0
            
        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 1:
            errorCode = 1

        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 3:
            errorCode = 3

        else:
            accessState = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX]
            globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 3
    
    if errorCode != -1:
        if errorCode == 5:
            await error(ctx, 5, name)
        elif errorCode == 0:
            await error(ctx, 0, name)
        elif errorCode == 1:
            await error(ctx, 1, name)
        elif errorCode == 3:
            await error(ctx, 3, name)
        return

    brawlInfo = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)

    try:
        await ctx.message.delete()
    except:
        pass

    await competitionTimer(ctx, arg, brawlInfo)

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        await globalValues.store()

##############################################################################################################################################

async def competitionTimer(ctx, name, brawlInfo):

    if brawlInfo[TYPE_INDEX] == "brawl":

        await brawlTimer(ctx, name, brawlInfo)

    else:

        await tournamentTimer(ctx, name, brawlInfo)

##############################################################################################################################################

def getTimeStr(timeList):
    timeStr = ""
    for i in range(len(timeList)):
        if i == 0 and timeList[i] != 0:
            timeStr = timeStr + str(timeList[i])
            timeStr = timeStr + " day"
            if timeList[i] != 1:
                timeStr = timeStr + "s"
            timeStr = timeStr + " "
        elif i == 1 and timeList[i] != 0:
            timeStr = timeStr + str(timeList[i])
            timeStr = timeStr + " hour"
            if timeList[i] != 1:
                timeStr = timeStr + "s"
            timeStr = timeStr + " "
        elif i == 2 and timeList[i] != 0:
            timeStr = timeStr + str(timeList[i])
            timeStr = timeStr + " minute"
            if timeList[i] != 1:
                timeStr = timeStr + "s"
            timeStr = timeStr + " "
        elif i == 3 and timeList[i] != 0:
            timeStr = timeStr + str(timeList[i])
            timeStr = timeStr + " second"
            if timeList[i] != 1:
                timeStr = timeStr + "s"
            timeStr = timeStr + " "
    return timeStr[:-1]

##############################################################################################################################################

async def brawlTimer(ctx, name, brawlInfo):
    
    backgroundTuple = brawlInfo[BACKGROUND_INDEX]
    fileList = brawlInfo[FILE_INDEX]
    reactionList = brawlInfo[REACTION_INDEX]
    timeList = brawlInfo[TIME_INDEX]

    timeStr = getTimeStr(timeList)

    globalValues.getFile(str(ctx.guild.id), fileList[0])
    imageFile = discord.File(fileList[0])
    embedVar = discord.Embed(title=name + " starts now!", description="This brawl ends in: " + timeStr)
    embedVar.set_image(url="attachment://" + fileList[0])
    message = await ctx.channel.send(file=imageFile, embed=embedVar)
    os.remove(fileList[0])

    for reaction in reactionList:
        await message.add_reaction(reaction)

    timeInSeconds = timeList[0] * 24 * 60 * 60 + timeList[1] * 60 * 60 + timeList[2] * 60 + timeList[3]

    await asyncio.sleep(timeInSeconds)
    
    reactionCount = []
    for reaction in reactionList:
        reactionCount.append(0)

    message = await ctx.fetch_message(message.id)
    for reaction in message.reactions:
        for i in range(len(reactionList)):
            if reaction.emoji == reactionList[i]:
                reactionCount[i] = reaction.count - 1
                break

    totalVotes = 0
    for count in reactionCount:
        totalVotes += count

    votesInfo = []
    
    for i in range(len(reactionList)):
        info = (reactionCount[i], reactionList[i], fileList[i + 1][0], fileList[i + 1][1])
        votesInfo.append(info)

    sortedVotes = sorted(votesInfo, key=operator.itemgetter(0), reverse=True)

    firstPlaceIndex = []
    firstPlaceCount = -1

    secondPlaceIndex = []
    secondPlaceCount = -1

    thirdPlaceIndex = []
    thirdPlaceCount = -1

    i = 0
    if i < len(sortedVotes):
        firstPlaceIndex = [i]
        firstPlaceCount = sortedVotes[i][0]

        i += 1
        while i < len(sortedVotes) and firstPlaceCount == sortedVotes[i][0]:
            firstPlaceIndex.append(i)
            i += 1

    if i < len(sortedVotes) and i < 3:
        secondPlaceIndex = [i]
        secondPlaceCount = sortedVotes[i][0]

        i += 1
        while i < len(sortedVotes) and secondPlaceCount == sortedVotes[i][0]:
            secondPlaceIndex.append(i)
            i += 1
    
    if i < len(sortedVotes) and i < 3:
        thirdPlaceIndex = [i]
        thirdPlaceCount = sortedVotes[i][0]

        i += 1
        while i < len(sortedVotes) and thirdPlaceCount == sortedVotes[i][0]:
            thirdPlaceIndex.append(i)
            i += 1
    

    votesStr = "Total votes: " + str(totalVotes) + "\n"
    for votes in sortedVotes:
        votesStr = votesStr + "Votes for " + votes[1] + " : " + str(votes[0]) + "\n"

    embedVar = discord.Embed(title=name + " is over!", description=votesStr)
    await ctx.channel.send(embed=embedVar)

    firstPlaceList = []
    secondPlaceList = []
    thirdPlaceList = []

    if len(reactionList) >= 4:
        if len(firstPlaceIndex) > 0:
            if len(firstPlaceIndex) == 1:
                embedVar = discord.Embed(title="1st Place Winner of " + name + "!", color=discord.Color.gold())
                embedVar = discord.Embed(description="Congratulations <@" + str(sortedVotes[firstPlaceIndex[0]][3]) + ">", color=discord.Color.gold())
                globalValues.getFile(str(ctx.guild.id), sortedVotes[firstPlaceIndex[0]][2])
                imageFile = discord.File(sortedVotes[firstPlaceIndex[0]][2])
                embedVar.set_image(url="attachment://" + sortedVotes[firstPlaceIndex[0]][2])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(sortedVotes[firstPlaceIndex[0]][2])
            
                firstPlaceList.append(embedVar, sortedVotes[firstPlaceIndex[0]][2])
            else:
                embedVar = discord.Embed(title="1st Place Winners of " + name + "!", color=discord.Color.gold())
                await ctx.channel.send(embed=embedVar)

                for i in firstPlaceIndex:
                    embedVar = discord.Embed(description="Congratulations <@" + str(sortedVotes[i][3]) + ">", color=discord.Color.gold())
                    globalValues.getFile(str(ctx.guild.id), sortedVotes[i][2])
                    imageFile = discord.File(sortedVotes[i][2])
                    embedVar.set_image(url="attachment://" + sortedVotes[i][2])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(sortedVotes[i][2])

                    firstPlaceList.append(embedVar, sortedVotes[i][2])

        if len(secondPlaceIndex) > 0:
            if len(secondPlaceIndex) == 1:
                embedVar = discord.Embed(title="2nd Place Winner of " + name + "!", color=0xAAA9AD)
                embedVar = discord.Embed(description="Congratulations <@" + str(sortedVotes[secondPlaceIndex[0]][3]) + ">", color=0xAAA9AD)
                globalValues.getFile(str(ctx.guild.id), sortedVotes[secondPlaceIndex[0]][2])
                imageFile = discord.File(sortedVotes[secondPlaceIndex[0]][2])
                embedVar.set_image(url="attachment://" + sortedVotes[secondPlaceIndex[0]][2])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(sortedVotes[secondPlaceIndex[0]][2])

                secondPlaceList.append(embedVar, sortedVotes[secondPlaceIndex[0]][2])
            else:
                embedVar = discord.Embed(title="2nd Place Winners of " + name + "!", color=0xAAA9AD)
                await ctx.channel.send(embed=embedVar)

                for i in secondPlaceIndex:
                    embedVar = discord.Embed(description="Congratulations <@" + str(sortedVotes[i][3]) + ">", color=0xAAA9AD)
                    globalValues.getFile(str(ctx.guild.id), sortedVotes[i][2])
                    imageFile = discord.File(sortedVotes[i][2])
                    embedVar.set_image(url="attachment://" + sortedVotes[i][2])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(sortedVotes[i][2])

                    secondPlaceList.append(embedVar, sortedVotes[i][2])

        if len(thirdPlaceIndex) > 0:
            if len(thirdPlaceIndex) == 1:
                embedVar = discord.Embed(title="3rd Place Winner of " + name + "!", color=0xCD7F32)
                embedVar = discord.Embed(description="Congratulations <@" + str(sortedVotes[thirdPlaceIndex[0]][3]) + ">", color=0xCD7F32)
                globalValues.getFile(str(ctx.guild.id), sortedVotes[thirdPlaceIndex[0]][2])
                imageFile = discord.File(sortedVotes[thirdPlaceIndex[0]][2])
                embedVar.set_image(url="attachment://" + sortedVotes[thirdPlaceIndex[0]][2])
                os.remove(sortedVotes[thirdPlaceIndex[0]][2])
                await ctx.channel.send(file=imageFile, embed=embedVar)

                thirdPlaceList.append(embedVar, sortedVotes[thirdPlaceIndex[0]][2])
            else:
                embedVar = discord.Embed(title="3rd Place Winners of " + name + "!", color=0xCD7F32)
                await ctx.channel.send(embed=embedVar)

                for i in thirdPlaceIndex:
                    embedVar = discord.Embed(description="Congratulations <@" + str(sortedVotes[i][3]) + ">", color=0xCD7F32)
                    globalValues.getFile(str(ctx.guild.id), sortedVotes[i][2])
                    imageFile = discord.File(sortedVotes[i][2])
                    embedVar.set_image(url="attachment://" + sortedVotes[i][2])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(sortedVotes[i][2])

                    thirdPlaceList.append(embedVar, sortedVotes[i][2])

    else:
        if len(firstPlaceIndex) > 0:
            if len(firstPlaceIndex) == 1:
                embedVar = discord.Embed(title="Winner of " + name + "!", color=discord.Color.gold())
                embedVar = discord.Embed(description="Congratulations <@" + str(sortedVotes[firstPlaceIndex[0]][3]) + ">", color=discord.Color.gold())
                globalValues.getFile(str(ctx.guild.id), sortedVotes[firstPlaceIndex[0]][2])
                imageFile = discord.File(sortedVotes[firstPlaceIndex[0]][2])
                embedVar.set_image(url="attachment://" + sortedVotes[firstPlaceIndex[0]][2])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(sortedVotes[firstPlaceIndex[0]][2])

                firstPlaceList.append(embedVar, sortedVotes[firstPlaceIndex[0]][2])
            else:
                embedVar = discord.Embed(title="Winners of " + name + "!", color=discord.Color.gold())
                await ctx.channel.send(embed=embedVar)

                for i in firstPlaceIndex:
                    embedVar = discord.Embed(description="Congratulations <@" + str(sortedVotes[i][3]) + ">", color=discord.Color.gold())
                    globalValues.getFile(str(ctx.guild.id), sortedVotes[i][2])
                    imageFile = discord.File(sortedVotes[i][2])
                    embedVar.set_image(url="attachment://" + sortedVotes[i][2])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(sortedVotes[i][2])

                    firstPlaceList.append(embedVar, sortedVotes[i][2])

    globalValues.removeFile(str(ctx.guild.id), fileList[0]);

    for i in range(len(sortedVotes)):
        if i not in firstPlaceIndex and i not in secondPlaceIndex and i not in thirdPlaceIndex:
            globalValues.removeFile(str(ctx.guild.id), sortedVotes[i][0]);
            pass

    winnerList = [firstPlaceList, secondPlaceList, thirdPlaceIndex]

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        globalValues.savedCompetitions[str(ctx.guild.id)][name][WINNER_INDEX] = winnerList

##############################################################################################################################################

async def tournamentTimer(ctx, name, brawlInfo):

    backgroundTuple = brawlInfo[BACKGROUND_INDEX]
    fileList = brawlInfo[FILE_INDEX]
    reactionList = brawlInfo[REACTION_INDEX]
    timeList = brawlInfo[TIME_INDEX]

    removeList = []

    durationList = timeList[0]
    tiebreakerList = timeList[1]
    delayList = timeList[2]

    durationStr = getTimeStr(durationList)
    tiebreakerStr = getTimeStr(tiebreakerList)
    delayStr = getTimeStr(delayList)

    durationInSeconds = durationList[0] * 24 * 60 * 60 + durationList[1] * 60 * 60 + durationList[2] * 60 + durationList[3]
    tiebreakerInSeconds = tiebreakerList[0] * 24 * 60 * 60 + tiebreakerList[1] * 60 * 60 + tiebreakerList[2] * 60 + tiebreakerList[3]
    delayInSeconds = delayList[0] * 24 * 60 * 60 + delayList[1] * 60 * 60 + delayList[2] * 60 + timeList[2][3]

    numRounds = int(math.log((len(fileList) * 2), 2))

    embedVar = discord.Embed(title=name + " begins now!", 
                             description="Rounds: " + str(numRounds) + "\n" + 
                                         "Voting duration of each match: " + durationStr + "\n" + 
                                         "Voting duration of tiebreaker match: " + tiebreakerStr + "\n" +
                                         "Duration of breaks in between match: " + delayStr)
    await ctx.channel.send(embed=embedVar)

    roundCounter = 1
    while numRounds > 2:

        await ctx.channel.send(embed=discord.Embed(title="Round " + str(roundCounter) + " begins now!"))

        winnerList = []

        for match in range(len(fileList)):
        
            winner = None

            await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1), description="Ends in: " + durationStr))

            embedVar = discord.Embed(title="")
            globalValues.getFile(str(ctx.guild.id), fileList[match][0])
            compImage = discord.File(fileList[match][0])
            embedVar.set_image(url="attachment://" + fileList[match][0])
            matchMessage = await ctx.channel.send(file=compImage, embed=embedVar)
            os.remove(fileList[match][0])
            for reaction in reactionList:
                await matchMessage.add_reaction(reaction)

            await asyncio.sleep(durationInSeconds)

            await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1) + " is over!"))

            matchMessage = await ctx.fetch_message(matchMessage.id)

            reactionCount = [0] * backgroundTuple[0]

            reactions = matchMessage.reactions

            for i in range(len(reactions)):
                if reactions[i].emoji in reactionList:
                    reactionIndex = reactionList.index(reactions[i].emoji)
                    reactionCount[reactionIndex] = reactions[i].count - 1

            tie = False

            if fileList[match][2][1] == -1:
                winner = fileList[match][1]
                removeList.append(fileList[match][2][0])
            elif fileList[match][1][1] == -1:
                winner = fileList[match][2]
                removeList.append(fileList[match][1][0])
            elif reactionCount[0] > reactionCount[1]:
                winner = fileList[match][1]
                removeList.append(fileList[match][2][0])
            elif reactionCount[1] > reactionCount[0]:
                winner = fileList[match][2]
                removeList.append(fileList[match][1][0])
            else:
                tie = True

            if tie:

                await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1) + " resulted in a tie!", description="Tiebreaker starts in: " + delayStr))

                await asyncio.sleep(delayInSeconds)

                await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1) + " Tiebreaker starts now!", description="Ends in: " + tiebreakerStr))

                embedVar = discord.Embed(title="")
                globalValues.getFile(str(ctx.guild.id), fileList[match][0])
                compImage = discord.File(fileList[match][0])
                embedVar.set_image(url="attachment://" + fileList[match][0])
                matchMessage = await ctx.channel.send(file=compImage, embed=embedVar)
                os.remove(fileList[match][0])
                for reaction in reactionList:
                    await matchMessage.add_reaction(reaction)

                await asyncio.sleep(durationInSeconds)

                await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1) + " Tiebreaker is over!"))

                matchMessage = await ctx.fetch_message(matchMessage.id)

                reactionCount = [0] * backgroundTuple[0]

                reactions = matchMessage.reactions

                for i in range(len(reactions)):
                    if reactions[i].emoji in reactionList:
                        reactionIndex = reactionList.index(reactions[i].emoji)
                        reactionCount[reactionIndex] = reactions[i].count - 1

                tie = False

                if fileList[match][2][1] == -1:
                    winner = fileList[match][1]
                    removeList.append(fileList[match][2][0])
                elif fileList[match][1][1] == -1:
                    winner = fileList[match][2]
                    removeList.append(fileList[match][1][0])
                elif reactionCount[0] > reactionCount[1]:
                    winner = fileList[match][1]
                    removeList.append(fileList[match][2][0])
                elif reactionCount[1] > reactionCount[0]:
                    winner = fileList[match][2]
                    removeList.append(fileList[match][1][0])
                else:
                    tie = True

                if tie:

                    await ctx.channel.send(embed=discord.Embed(title="Flipping a coin to decide match " + str(match + 1) + "!"))

                    flip = random.randint(0, 1)

                    if flip == 0:
                        winner = fileList[match][1]
                        removeList.append(fileList[match][2][0])
                    else:
                        winner = fileList[match][2]
                        removeList.append(fileList[match][1][0])

            embedVar = discord.Embed(title="Winner of Round " + str(roundCounter) + " Match " + str(match + 1) + "!")
            globalValues.getFile(str(ctx.guild.id), winner[0])
            imageFile = discord.File(winner[0])
            embedVar.set_image(url="attachment://" + winner[0])
            await ctx.channel.send(file=imageFile, embed=embedVar)
            os.remove(winner[0])
            winnerList.append(winner)

            removeList.append(fileList[match][0])

            if match < len(fileList) - 1:
                await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 2) + " starts in " + delayStr + "!"))
                await asyncio.sleep(delayInSeconds)

        numRounds -= 1
        roundCounter += 1

        fileList = generateMatches(ctx, backgroundTuple, winnerList)

        if numRounds > 2:
            await ctx.channel.send(embed=discord.Embed(title="Round " + str(roundCounter) + " starts in " + delayStr + "!"))
        else:
            await ctx.channel.send(embed=discord.Embed(title="The " + name + " Semifinals start in " + delayStr + "!"))

        await asyncio.sleep(delayInSeconds)

    # semi finals
    if len(fileList) > 1:

        finalList = []
        consolationList = []

        await ctx.channel.send(embed=discord.Embed(title="The " + name + " Semifinals start now!"))

        for match in range(len(fileList)):
            
            winner = None

            await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1), description="Ends in: " + durationStr))

            embedVar = discord.Embed(title="")
            globalValues.getFile(str(ctx.guild.id), fileList[match][0])
            compImage = discord.File(fileList[match][0])
            embedVar.set_image(url="attachment://" + fileList[match][0])
            matchMessage = await ctx.channel.send(file=compImage, embed=embedVar)
            os.remove(fileList[match][0])
            for reaction in reactionList:
                await matchMessage.add_reaction(reaction)

            await asyncio.sleep(durationInSeconds)

            await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1) + " is over!"))

            matchMessage = await ctx.fetch_message(matchMessage.id)

            reactionCount = [0] * backgroundTuple[0]

            reactions = matchMessage.reactions

            for i in range(len(reactions)):
                if reactions[i].emoji in reactionList:
                    reactionIndex = reactionList.index(reactions[i].emoji)
                    reactionCount[reactionIndex] = reactions[i].count - 1

            tie = False

            if fileList[match][2][1] == -1:
                winner = fileList[match][1]
                consolationList.append(fileList[match][2])
            elif fileList[match][1][1] == -1:
                winner = fileList[match][2]
                consolationList.append(fileList[match][1])
            elif reactionCount[0] > reactionCount[1]:
                winner = fileList[match][1]
                consolationList.append(fileList[match][2])
            elif reactionCount[1] > reactionCount[0]:
                winner = fileList[match][2]
                consolationList.append(fileList[match][1])
            else:
                tie = True

            if tie:

                await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1) + " resulted in a tie!", description="Tiebreaker starts in: " + delayStr))

                await asyncio.sleep(delayInSeconds)

                await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1) + " Tiebreaker starts now!", description="Ends in: " + tiebreakerStr))

                embedVar = discord.Embed(title="")
                globalValues.getFile(str(ctx.guild.id), fileList[match][0])
                compImage = discord.File(fileList[match][0])
                embedVar.set_image(url="attachment://" + fileList[match][0])
                matchMessage = await ctx.channel.send(file=compImage, embed=embedVar)
                os.remove(fileList[match][0])
                for reaction in reactionList:
                    await matchMessage.add_reaction(reaction)

                await asyncio.sleep(durationInSeconds)

                await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 1) + " Tiebreaker is over!"))

                matchMessage = await ctx.fetch_message(matchMessage.id)

                reactionCount = [0] * backgroundTuple[0]

                reactions = matchMessage.reactions

                for i in range(len(reactions)):
                    if reactions[i].emoji in reactionList:
                        reactionIndex = reactionList.index(reactions[i].emoji)
                        reactionCount[reactionIndex] = reactions[i].count - 1

                tie = False

                if fileList[match][2][1] == -1:
                    winner = fileList[match][1]
                    consolationList.append(fileList[match][2])
                elif fileList[match][1][1] == -1:
                    winner = fileList[match][2]
                    consolationList.append(fileList[match][1])
                elif reactionCount[0] > reactionCount[1]:
                    winner = fileList[match][1]
                    consolationList.append(fileList[match][2])
                elif reactionCount[1] > reactionCount[0]:
                    winner = fileList[match][2]
                    consolationList.append(fileList[match][1])
                else:
                    tie = True

                if tie:

                    await ctx.channel.send(embed=discord.Embed(title="Flipping a coin to determine match " + str(match + 1) + "!"))

                    flip = random.randint(0, 1)

                    if flip == 0:
                        winner = fileList[match][1]
                        consolationList.append(fileList[match][2])
                    else:
                        winner = fileList[match][2]
                        consolationList.append(fileList[match][1])

            embedVar = discord.Embed(title="Winner of the " + name + " Semifinals Match " + str(match + 1) + "!")
            globalValues.getFile(str(ctx.guild.id), winner[0])
            imageFile = discord.File(winner[0])
            embedVar.set_image(url="attachment://" + winner[0])
            await ctx.channel.send(file=imageFile, embed=embedVar)
            os.remove(winner[0])
            finalList.append(winner)

            removeList.append(fileList[match][0])

            if match < len(fileList) - 1:
                await ctx.channel.send(embed=discord.Embed(title="Match " + str(match + 2) + " starts in " + delayStr + "!"))
                await asyncio.sleep(delayInSeconds)

        await ctx.channel.send(embed=discord.Embed(title="The " + name + " Consolation Final starts in " + str(delayStr) + "!"))
        await asyncio.sleep(delayInSeconds)

        # consolation final
        consolationList = generateMatches(ctx, backgroundTuple, consolationList)
        consolationList = consolationList[0]

        thirdPlace = ()

        embedVar = discord.Embed(title="The " + name + " Consolation Final begins now!", description="Consolation final ends in: " + durationStr)
        await ctx.channel.send(embed=embedVar)

        embedVar = discord.Embed(title="")
        globalValues.getFile(str(ctx.guild.id), consolationList[0])
        compImage = discord.File(consolationList[0])
        embedVar.set_image(url="attachment://" + consolationList[0])
        matchMessage = await ctx.channel.send(file=compImage, embed=embedVar)
        os.remove(consolationList[0])
        for reaction in reactionList:
            await matchMessage.add_reaction(reaction)

        await asyncio.sleep(durationInSeconds)

        matchMessage = await ctx.fetch_message(matchMessage.id)

        reactionCount = [0] * backgroundTuple[0]

        reactions = matchMessage.reactions

        for i in range(len(reactions)):
            if reactions[i].emoji in reactionList:
                reactionIndex = reactionList.index(reactions[i].emoji)
                reactionCount[reactionIndex] = reactions[i].count - 1

        tie = False
        if consolationList[2][1] == -1:
            thirdPlace = consolationList[1]
            removeList.append(consolationList[2][0])
        elif consolationList[1][1] == -1:
            thirdPlace = consolationList[2]
            removeList.append(consolationList[1][0])
        elif reactionCount[0] > reactionCount[1]:
            thirdPlace = consolationList[1]
            removeList.append(consolationList[2][0])
        elif reactionCount[1] > reactionCount[0]:
            thirdPlace = consolationList[2]
            removeList.append(consolationList[1][0])
        else:
            tie = True

        if tie:

            await ctx.channel.send(embed=discord.Embed(title="The " + name + " Consolation Final resulted in a tie!", description="Tiebreaker starts in: " + delayStr))

            await asyncio.sleep(delayInSeconds)

            embedVar = discord.Embed(title="The " + name + " Consolation Final Tiebreaker starts now!", description="Tiebreaker ends in: " + getTimeStr(tiebreakerList))
            await ctx.channel.send(embed=embedVar)

            embedVar = discord.Embed(title="")
            globalValues.getFile(str(ctx.guild.id), consolationList[0])
            compImage = discord.File(consolationList[0])
            embedVar.set_image(url="attachment://" + consolationList[0])
            matchMessage = await ctx.channel.send(file=compImage, embed=embedVar)
            os.remove(consolationList[0])
            for reaction in reactionList:
                await matchMessage.add_reaction(reaction)
        
            match = (matchMessage, consolationList)

            await asyncio.sleep(durationInSeconds)

            matchMessage = await ctx.fetch_message(matchMessage.id)

            reactionCount = [0] * backgroundTuple[0]

            reactions = matchMessage.reactions

            for i in range(len(reactions)):
                if reactions[i].emoji in reactionList:
                    reactionIndex = reactionList.index(reactions[i].emoji)
                    reactionCount[reactionIndex] = reactions[i].count - 1

            tie = False
            if consolationList[2][1] == -1:
                thirdPlace = consolationList[1]
                removeList.append(consolationList[2][0])
            elif consolationList[1][1] == -1:
                thirdPlace = consolationList[2]
                removeList.append(consolationList[1][0])
            elif reactionCount[0] > reactionCount[1]:
                thirdPlace = consolationList[1]
                removeList.append(consolationList[2][0])
            elif reactionCount[1] > reactionCount[0]:
                thirdPlace = consolationList[2]
                removeList.append(consolationList[1][0])
            else:
                tie = True

            if tie:

                await asyncio.sleep(delayInSeconds)

                embedVar = discord.Embed(title="Flipping a coin to decide the Consolation Final!")
                await ctx.channel.send(embed=embedVar)

                flip = random.randint(0, 1)

                if flip == 0:
                    thirdPlace = consolationList[1]
                    removeList.append(consolationList[2][0])

                else:
                    thirdPlace = consolationList[2]
                    removeList.append(consolationList[1][0])

        embedVar = discord.Embed(title="Winner of the " + name + " Consolation Final!")
        globalValues.getFile(str(ctx.guild.id), thirdPlace[0])
        imageFile = discord.File(thirdPlace[0])
        embedVar.set_image(url="attachment://" + thirdPlace[0])
        await ctx.channel.send(file=imageFile, embed=embedVar)
        os.remove(thirdPlace[0])

        removeList.append(consolationList[0])

        await ctx.channel.send(embed=discord.Embed(title="The " + name + " Final starts in " + delayStr + "!"))

        await asyncio.sleep(delayInSeconds)

    else:
        finalList = fileList

    # final
    finalList = generateMatches(ctx, backgroundTuple, finalList)
    finalList = finalList[0]

    firstPlace = ()
    secondPlace = ()

    await ctx.channel.send(embed=discord.Embed(title="The " + name + " Final begins now!", description="Final ends in: " + durationStr))

    embedVar = discord.Embed(title="")
    globalValues.getFile(str(ctx.guild.id), finalList[0])
    compImage = discord.File(finalList[0])
    embedVar.set_image(url="attachment://" + finalList[0])
    matchMessage = await ctx.channel.send(file=compImage, embed=embedVar)
    os.remove(finalList[0])
    for reaction in reactionList:
        await matchMessage.add_reaction(reaction)

    await asyncio.sleep(durationInSeconds)

    matchMessage = await ctx.fetch_message(matchMessage.id)

    reactionCount = [0] * backgroundTuple[0]

    reactions = matchMessage.reactions

    for i in range(len(reactions)):
        if reactions[i].emoji in reactionList:
            reactionIndex = reactionList.index(reactions[i].emoji)
            reactionCount[reactionIndex] = reactions[i].count - 1

    tie = False
    if finalList[2][1] == -1:
        firstPlace = finalList[1]
        secondPlace = finalList[2]
    elif finalList[1][1] == -1:
        firstPlace = finalList[2]
        secondPlace = finalList[1]
    elif reactionCount[0] > reactionCount[1]:
        firstPlace = finalList[1]
        secondPlace = finalList[2]
    elif reactionCount[1] > reactionCount[0]:
        firstPlace = finalList[2]
        secondPlace = finalList[1]
    else:
        tie = True

    if tie:

        await ctx.channel.send(embed=discord.Embed(title="The " + name + " Final resulted in a tie!", description="Tiebreaker starts in: " + delayStr))

        await asyncio.sleep(delayInSeconds)

        embedVar = discord.Embed(title="The " + name + " Final Tiebreaker starts now!", description="Tiebreaker ends in: " + tiebreakerStr)
        await ctx.channel.send(embed=embedVar)

        embedVar = discord.Embed(title="")
        globalValues.getFile(str(ctx.guild.id), finalList[0])
        compImage = discord.File(finalList[0])
        embedVar.set_image(url="attachment://" + finalList[0])
        matchMessage = await ctx.channel.send(file=compImage, embed=embedVar)
        os.remove(finalList[0])
        for reaction in reactionList:
            await matchMessage.add_reaction(reaction)

        await asyncio.sleep(durationInSeconds)

        matchMessage = await ctx.fetch_message(matchMessage.id)

        reactionCount = [0] * backgroundTuple[0]

        reactions = matchMessage.reactions

        for i in range(len(reactions)):
            if reactions[i].emoji in reactionList:
                reactionIndex = reactionList.index(reactions[i].emoji)
                reactionCount[reactionIndex] = reactions[i].count - 1

        tie = False
        if finalList[2][1] == -1:
            firstPlace = finalList[1]
            secondPlace = finalList[2]
        elif finalList[1][1] == -1:
            firstPlace = finalList[2]
            secondPlace = finalList[1]
        elif reactionCount[0] > reactionCount[1]:
            firstPlace = finalList[1]
            secondPlace = finalList[2]
        elif reactionCount[1] > reactionCount[0]:
            firstPlace = finalList[2]
            secondPlace = finalList[1]
        else:
            tie = True

        if tie:

            embedVar = discord.Embed(title="Flipping a coin to decide the Final!")
            await ctx.channel.send(embed=embedVar)

            flip = random.randint(0, 1)

            if flip == 0:
                firstPlace = finalList[1]
                secondPlace = finalList[2]

            else:
                firstPlace = finalList[2]
                secondPlace = finalList[1]

    removeList.append(finalList[0])

    await asyncio.sleep(delayInSeconds)

    winnerList = []

    embedVar = discord.Embed(title="1st Place Winner of " + name, description="Congratulations <@" + str(firstPlace[1]) + ">", color=discord.Color.gold())
    globalValues.getFile(str(ctx.guild.id), firstPlace[0])
    imageFile = discord.File(firstPlace[0])
    embedVar.set_image(url="attachment://" + firstPlace[0])
    await ctx.channel.send(file=imageFile, embed=embedVar)
    os.remove(firstPlace[0])

    winnerList.append((embedVar, firstPlace[0]))

    embedVar = discord.Embed(title="2nd Place Winner of " + name, description="Congratulations <@" + str(secondPlace[1]) + ">", color=0xAAA9AD)
    globalValues.getFile(str(ctx.guild.id), secondPlace[0])
    imageFile = discord.File(secondPlace[0])
    embedVar.set_image(url="attachment://" + secondPlace[0])
    await ctx.channel.send(file=imageFile, embed=embedVar)
    os.remove(secondPlace[0])

    winnerList.append((embedVar, secondPlace[0]))

    embedVar = discord.Embed(title="3rd Place Winner of " + name, description="Congratulations <@" + str(thirdPlace[1]) + ">", color=0xCD7F32)
    globalValues.getFile(str(ctx.guild.id), thirdPlace[0])
    imageFile = discord.File(thirdPlace[0])
    embedVar.set_image(url="attachment://" + thirdPlace[0])
    await ctx.channel.send(file=imageFile, embed=embedVar)
    os.remove(thirdPlace[0])

    winnerList.append((embedVar, thirdPlace[0]))
    over = True
    
    if over:
        for file in removeList:
            try:
                globalValues.removeFile(str(ctx.guild.id), file);
            except:
                pass

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 4
        globalValues.savedCompetitions[str(ctx.guild.id)][name][WINNER_INDEX] = winnerList

##############################################################################################################################################

def generateMatches(ctx, backgroundTuple, cardFiles):

    bracket = generateBracket(cardFiles)

    pairs = []
    generatePairs(bracket, pairs)

    matchFiles = generateMatchFiles(ctx, backgroundTuple, pairs)

    return matchFiles    

##############################################################################################################################################

def generateBracket(cardFiles):

    if len(cardFiles) <= 2:
        return cardFiles

    num = int(len(cardFiles) / 2)
    return [generateBracket(cardFiles[:num]), generateBracket(cardFiles[num:])]

##############################################################################################################################################

def generatePairs(bracket, pairs):

    if not isinstance(bracket[0], type([])):
        pairs.append(bracket)

    else:
        generatePairs(bracket[0], pairs)
        generatePairs(bracket[1], pairs)

##############################################################################################################################################

def generateMatchFiles(ctx, backgroundTuple, pairs):

    matchFiles = []

    for pair in pairs:
        
        fileNames = []
        
        req = urllib.request.Request(globalValues.backgrounds.get(backgroundTuple[0])[backgroundTuple[1]][0], headers=globalValues.header)
        backgroundImage = Image.open(urlopen(req))
        backgroundImage.convert('RGBA')
        image = backgroundImage.copy()
        imageFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-0" + ".jpg"

        fileNames.append(imageFileName)
        
        for i in range(len(pair)):
            globalValues.getFile(str(ctx.guild.id), pair[i][0])
            cardImage = Image.open(pair[i][0])
            cardImage.convert('RGBA')
            image.paste(cardImage, (globalValues.cardCoordinates.get(backgroundTuple[0])[i][0], globalValues.cardCoordinates.get(backgroundTuple[0])[i][1]), cardImage)
            fileNames.append((pair[i][0], pair[i][1]))
            os.remove(pair[i][0])

        image.save(imageFileName, quality=95)
        globalValues.addFile(str(ctx.guild.id), imageFileName)
        os.remove(imageFileName)
        matchFiles.append(fileNames)

    return matchFiles

##############################################################################################################################################

async def error(ctx, code, *args):

    # invalid name
    if code == 5:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " does not exist."))

    # currently open
    elif code == 0:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is currently open. Please close " + name + " first in order to start."))

    # currently being edited
    elif code == 1:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is currently being edited and cannot be accessed."))

    # currently live
    elif code == 3:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is already live."))