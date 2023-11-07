# submit.py
# By: PVCPipe01
# Holds the code for the submit command

import discord
import os
import asyncio
import aiorwlock
import urllib.request
from urllib.request import urlopen
from PIL import Image
import random
import time

import globalValues

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX

async def submit(ctx, arg1, arg2):
    async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
        brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(arg1)
        if not brawl:
            await error(ctx, 0, arg1)
            return
        if brawl[ACCESS_INDEX] != 0:
            await error(ctx, 1, arg1)
            return

    name = arg1
    code = arg2.lower()
    participantDict = brawl[PARTICIPANT_INDEX][0]
    eligibilityList = brawl[PARTICIPANT_INDEX][1]
    maxParticipants = brawl[PARTICIPANT_INDEX][2]

    errorCode = False

    if len(participantDict) >= maxParticipants:
        await error(ctx, 5, name)
        return

    hasRole = False
    if eligibilityList[0] != None:
        for role in eligibilityList[0][1]:
            for userRole in ctx.author.roles:
                if role == userRole.name:
                    hasRole = True
                    break

    if eligibilityList[0] == None or ctx.author.id in eligibilityList[0][0] or hasRole:

        cardInfo = await getCard(ctx, code)
        if cardInfo == None:
            return
        cardTuple = cardInfo[0]
        series = cardInfo[1]

        if eligibilityList[1] != None and series not in eligibilityList[1]:
            globalValues.removeFile(str(ctx.guild.id), cardTuple[0])
            await error(ctx, 6, name, series)
            return

        typeOfBrawl = brawl[0]

        if typeOfBrawl == "brawl":
            errorCode = await submitBrawl(ctx, name, cardTuple, series)

        else:
            errorCode = await submitTournament(ctx, name, cardTuple, series)

    else:
        await error(ctx, 4, name)
        return

    if not errorCode:
        async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
            await globalValues.store()

##############################################################################################################################################

async def getCard(ctx, code):

    def cardCheck(m):
        if m.channel == ctx.channel and m.author.id == globalValues.KARUTA_ID and m.embeds and m.embeds[0].title == "Card Details" and "<@" + str(ctx.author.id) + ">" in m.embeds[0].description:
            codeStr = m.embeds[0].description.split("**`")[1]
            codeStr = codeStr.split("`**")[0]
            codeStr = codeStr.strip()
            if codeStr == code:
                return True
        return False

    await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, please type **`k!v " + code + "`**\nYou must own the card to submit it."))

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=cardCheck)

        series = message.embeds[0].description.split('·')[4]
        series = series.strip()
        series = series.strip('~~')

        url = message.embeds[0].image.url
        req = urllib.request.Request(url, headers=globalValues.header)
        cardImage = Image.open(urlopen(req))
        cardImage.convert('RGBA')
        cardFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-" + str(random.randint(1, 1000)) + ".png"
        cardImage.save(cardFileName, quality=95)
        globalValues.addFile(str(ctx.guild.id), cardFileName);
        os.remove(cardFileName);

        return ((cardFileName, code), series)

    except asyncio.TimeoutError:
        return None

##############################################################################################################################################

async def submitBrawl(ctx, name, cardTuple, series):

    brawl = None
    hasError = False

    async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
        brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)

    participantDict = brawl[PARTICIPANT_INDEX][0]
    eligibilityList = brawl[PARTICIPANT_INDEX][1]
    maxParticipants = brawl[PARTICIPANT_INDEX][2]
        
    newCode = cardTuple[1]
    oldCode = ""

    previousEntry = False
    if participantDict.get(ctx.author.id):
        oldCode = participantDict.get(ctx.author.id)[1]
        previousEntry = True

    message = None
    if previousEntry:
        message = await ctx.channel.send(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to switch **`" + oldCode + "`** with **`" + newCode + "`**?"))

    elif len(participantDict) < maxParticipants:
        message = await ctx.channel.send(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to submit **`" + newCode + "`**?"))

    else:
        await error(ctx, 5, name)
        return

    await message.add_reaction('✅')
    await message.add_reaction('❌')

    def brawlCheck(react, user):
        return react.message == message and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=brawlCheck)
        reaction = reaction[0].emoji

        if reaction == '✅':
            if previousEntry:
                await message.edit(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to switch **`" + oldCode + "`** with **`" + newCode + "`**?", color=discord.Color.green()))

                errorCode = -1
                async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
                    async with globalValues.brawlLocks.get(str(ctx.guild.id)).get(name).writer_lock:
                        brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)
                        eligibilityList = brawl[PARTICIPANT_INDEX][1]
                        maxParticipants = brawl[PARTICIPANT_INDEX][2]

                        hasRole = False
                        if eligibilityList[0] != None:
                            for role in eligibilityList[0][1]:
                                for userRole in ctx.author.roles:
                                    if role == userRole.name:
                                        hasRole = True
                                        break
                        if not brawl:
                            errorCode = 0
                        elif brawl[ACCESS_INDEX] == 1:
                            errorCode = 1
                        elif brawl[ACCESS_INDEX] == 2:
                            errorCode = 2
                        elif brawl[ACCESS_INDEX] == 3:
                            errorCode = 3
                        elif eligibilityList[0] != None and ctx.author.id not in eligibilityList[0][0] and not hasRole:
                            errorCode = 4
                        elif len(brawl[PARTICIPANT_INDEX][0]) >= maxParticipants:
                            errorCode = 5
                        elif eligibilityList[1] != None and series not in eligibilityList[1]:
                            errorCode = 6
                        else:
                            oldCard = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0].get(ctx.author.id)
                            try:
                                globalValues.removeFile(str(ctx.guild.id), oldCard[0])
                            except:
                                pass
                            globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0][ctx.author.id] = cardTuple
                if errorCode != -1:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), cardTuple[0])
                    except:
                        pass
                    await error(ctx, errorCode, name, series)
                    hasError = True
                else:
                    await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, **`" + newCode + "`** has been submitted.", color=discord.Color.green()))

            else:
                await message.edit(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to submit **`" + newCode + "`**?", color=discord.Color.green()))

                errorCode = -1
                async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
                    async with globalValues.brawlLocks.get(str(ctx.guild.id)).get(name).writer_lock:
                        brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)
                        eligibilityList = brawl[PARTICIPANT_INDEX][1]
                        maxParticipants = brawl[PARTICIPANT_INDEX][2]

                        hasRole = False
                        if eligibilityList[0] != None:
                            for role in eligibilityList[1]:
                                for userRole in ctx.author.roles:
                                    if role == userRole.name:
                                        hasRole = True
                                        break
                        if not brawl:
                            errorCode = 0
                        elif brawl[ACCESS_INDEX] == 1:
                            errorCode = 1
                        elif brawl[ACCESS_INDEX] == 2:
                            errorCode = 2
                        elif brawl[ACCESS_INDEX] == 3:
                            errorCode = 3
                        elif eligibilityList[0] != None and ctx.author.id not in eligibilityList[0][0] and not hasRole:
                            errorCode = 4
                        elif len(brawl[PARTICIPANT_INDEX][0]) >= maxParticipants:
                            errorCode = 5
                        elif eligibilityList[1] != None and series not in eligibilityList[1]:
                            errorCode = 6
                        else:
                            oldCard = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0].get(ctx.author.id)
                            try:
                                globalValues.removeFile(str(ctx.guild.id), oldCard[0])
                            except:
                                pass
                            globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0][ctx.author.id] = cardTuple
                if errorCode != -1:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), cardTuple[0])
                    except:
                        pass
                    await error(ctx, errorCode, name, series)
                    hasError = True
                else:
                    await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, **`" + newCode + "`** has been submitted.", color=discord.Color.green()))
        else:
            if previousEntry:
                await message.edit(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to switch " + oldCode + " with " + newCode + "?", color=discord.Color.red()))
            else:
                await message.edit(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to submit " + newCode + "?", color=discord.Color.red()))
            try:
                globalValues.removeFile(str(ctx.guild.id), cardTuple[0])
            except:
                pass
            hasError = True

    except asyncio.TimeoutError:
        hasError = True

    return hasError

##############################################################################################################################################

async def submitTournament(ctx, name, cardTuple, series):

    brawl = None
    hasError = False

    async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
        brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)

    participantDict = brawl[PARTICIPANT_INDEX][0]
    eligibilityList = brawl[PARTICIPANT_INDEX][1]
    maxParticipants = brawl[PARTICIPANT_INDEX][2]
        
    newCode = cardTuple[1]
    oldCode = ""

    previousEntry = False
    if participantDict.get(ctx.author.id):
        oldCode = participantDict.get(ctx.author.id)[1]
        previousEntry = True

    message = None
    if previousEntry:
        message = await ctx.channel.send(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to switch **`" + oldCode + "`** with **`" + newCode + "`**?"))

    elif len(participantDict) < maxParticipants:
        message = await ctx.channel.send(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to submit **`" + newCode + "`**?"))

    else:
        await error(ctx, 5, name)
        return

    await message.add_reaction('✅')
    await message.add_reaction('❌')

    def brawlCheck(react, user):
        return react.message == message and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=brawlCheck)
        reaction = reaction[0].emoji

        if reaction == '✅':
            if previousEntry:
                await message.edit(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to switch **`" + oldCode + "`** with **`" + newCode + "`**?", color=discord.Color.green()))

                errorCode = -1
                async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
                    async with globalValues.brawlLocks.get(str(ctx.guild.id)).get(name).writer_lock:
                        brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)
                        eligibilityList = brawl[PARTICIPANT_INDEX][1]
                        maxParticipants = brawl[PARTICIPANT_INDEX][2]

                        hasRole = False
                        if eligibilityList[0] != None:
                            for role in eligibilityList[0][1]:
                                for userRole in ctx.author.roles:
                                    if role == userRole.name:
                                        hasRole = True
                                        break
                        if not brawl:
                            errorCode = 0
                        elif brawl[ACCESS_INDEX] == 1:
                            errorCode = 1
                        elif brawl[ACCESS_INDEX] == 2:
                            errorCode = 2
                        elif brawl[ACCESS_INDEX] == 3:
                            errorCode = 3
                        elif eligibilityList[0] != None and ctx.author.id not in eligibilityList[0][0] and not hasRole:
                            errorCode = 4
                        elif len(brawl[PARTICIPANT_INDEX][0]) >= maxParticipants:
                            errorCode = 5
                        elif eligibilityList[1] != None and series not in eligibilityList[1]:
                            errorCode = 6
                        else:
                            oldCard = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0].get(ctx.author.id)
                            try:
                                globalValues.removeFile(str(ctx.guild.id), oldCard[0])
                            except:
                                pass
                            globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0][ctx.author.id] = cardTuple
                if errorCode != -1:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), cardTuple[0])
                    except:
                        pass
                    await error(ctx, errorCode, name, series)
                    hasError = True
                else:
                    await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, **`" + newCode + "`** has been submitted.", color=discord.Color.green()))

            else:
                await message.edit(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to submit **`" + newCode + "`**?", color=discord.Color.green()))

                errorCode = -1
                async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
                    async with globalValues.brawlLocks.get(str(ctx.guild.id)).get(name).writer_lock:
                        brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)
                        eligibilityList = brawl[PARTICIPANT_INDEX][1]
                        maxParticipants = brawl[PARTICIPANT_INDEX][2]

                        hasRole = False
                        if eligibilityList[0] != None:
                            for role in eligibilityList[1]:
                                for userRole in ctx.author.roles:
                                    if role == userRole.name:
                                        hasRole = True
                                        break
                        if not brawl:
                            errorCode = 0
                        elif brawl[ACCESS_INDEX] == 1:
                            errorCode = 1
                        elif brawl[ACCESS_INDEX] == 2:
                            errorCode = 2
                        elif brawl[ACCESS_INDEX] == 3:
                            errorCode = 3
                        elif eligibilityList[0] != None and ctx.author.id not in eligibilityList[0][0] and not hasRole:
                            errorCode = 4
                        elif len(brawl[PARTICIPANT_INDEX][0]) >= maxParticipants:
                            errorCode = 5
                        elif eligibilityList[1] != None and series not in eligibilityList[1]:
                            errorCode = 6
                        else:
                            oldCard = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0].get(ctx.author.id)
                            try:
                                globalValues.removeFile(str(ctx.guild.id), oldCard[0])
                            except:
                                pass
                            globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0][ctx.author.id] = cardTuple
                if errorCode != -1:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), cardTuple[0])
                    except:
                        pass
                    await error(ctx, errorCode, name, series)
                    hasError = True
                else:
                    await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, **`" + newCode + "`** has been submitted.", color=discord.Color.green()))
        else:
            if previousEntry:
                await message.edit(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to switch " + oldCode + " with " + newCode + "?", color=discord.Color.red()))
            else:
                await message.edit(embed=discord.Embed(title=name + " Submission Ticket", description="<@" + str(ctx.author.id) + ">, would you like to submit " + newCode + "?", color=discord.Color.red()))
            try:
                globalValues.removeFile(str(ctx.guild.id), cardTuple[0])
            except:
                pass
            hasError = True

    except asyncio.TimeoutError:
        hasError = True

    return hasError
                           
##############################################################################################################################################

async def error(ctx, code, *args):

    # invalid name
    if code == 0:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + name + " does not exist."))

    # edit
    elif code == 1:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + name + " is currently being edited and is closed to submissions."))

    # closed
    elif code == 2:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + name + " is closed to submissions."))

    # live
    elif code == 3:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + name + " is currently live and is closed to submissions."))

    # ineligible
    elif code == 4:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, you are ineligible to participate in " + name + "."))

    # max participants
    elif code == 5:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + name + " has reached its max number of participants."))

    elif code == 6:
        name = args[0]
        series = args[1]
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + series + " is not an eligible series for " + name + "."))