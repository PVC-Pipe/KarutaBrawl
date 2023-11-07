# close.py
# By: PVCPipe01
# holds the close command

import discord
import os
from discord.ext import commands

import asyncio
import urllib.request
from urllib.request import urlopen
from PIL import Image
import pickle
import random
import math
import time

import globalValues
import host

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX


##############################################################################################################################################

async def close(ctx, name):

    errorCode = -1

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        if not globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name):
            errorCode = 5
            
        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX] == 1:
            errorCode = 1
        
        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX] == 2:
            errorCode = 2

        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[ACCESS_INDEX] == 3:
            errorCode = 3

        else:
            globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 1

    if errorCode != -1:
        if errorCode == 5:
            await ctx.channel.send(embed=discord.Embed(description=name + " does not exist"))
        elif errorCode == 1:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + name + " is currently being edited and cannot be closed."))
        elif errorCode == 2:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + name + " is already closed."))
        elif errorCode == 3:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + name + " is already live and cannot be closed."))
        return
    
    confirm = await closeSub(ctx, name)
    if not confirm:
        globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 0
        await ctx.channel.send(embed=discord.Embed(description="Close cancelled.", color=discord.Color.red()))
        return

    nameTaken = False

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        if name == confirm[0]:
            globalValues.savedCompetitions[str(ctx.guild.id)][confirm[0]] = confirm[1]

        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(confirm[0]) == None:
            globalValues.savedCompetitions.get(str(ctx.guild.id)).pop(name)
            globalValues.savedCompetitions[str(ctx.guild.id)][confirm[0]] = confirm[1]

        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(confirm[0]) != None:
            globalValues.savedCompetitions[str(ctx.guild.id)][name] = confirm[1]
            nameTaken = True
        
    await globalValues.store()

    if nameTaken:
        await ctx.channel.send(embed=discord.Embed(description=confirm[0] + " was already taken, the name is still " + name))
        await ctx.channel.send(embed=discord.Embed(description=name + " successfully closed.", color=discord.Color.green()))
    else:
        await ctx.channel.send(embed=discord.Embed(description=confirm[0] + " successfully closed.", color=discord.Color.green()))
    

##############################################################################################################################################

async def closeSub(ctx, name):

    brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)
    
    confirm = None

    if brawl[TYPE_INDEX] == "brawl":
        backgroundTuple = None
        if len(brawl[PARTICIPANT_INDEX][0]) != brawl[PARTICIPANT_INDEX][2]:
            await ctx.channel.send(embed=discord.Embed(description="The current number of participants is less than the max number of participants. Please choose a different background."))
            backgroundTuple = await host.chooseBackground(ctx, len(brawl[PARTICIPANT_INDEX][0]))
        else:
            backgroundTuple = brawl[BACKGROUND_INDEX]

        confirm = await confirmBrawl(ctx, backgroundTuple, name)

    else:
        confirm = await confirmTournament(ctx, name)

    return confirm

##############################################################################################################################################

async def generateBrawlImage(ctx, backgroundTuple, participantDict):

    if len(participantDict) < 2:
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, you cannot close a brawl with less than 2 participants."))
        return None

    cardList = []

    for id, card in participantDict.items():
        cardList.append((card[0], id))

    fileList = []

    req = urllib.request.Request(globalValues.backgrounds.get(backgroundTuple[0])[backgroundTuple[1]][0], headers=globalValues.header)
    backgroundImage = Image.open(urlopen(req))
    backgroundImage.convert('RGBA')
    image = backgroundImage.copy()
    imageFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-0" + ".jpg"

    fileList.append(imageFileName)

    for i in range(len(cardList)):
        globalValues.getFile(str(ctx.guild.id), cardList[i][0])
        cardImage = Image.open(cardList[i][0])
        cardImage.convert('RGBA')
        image.paste(cardImage, (globalValues.cardCoordinates.get(backgroundTuple[0])[i][0], globalValues.cardCoordinates.get(backgroundTuple[0])[i][1]), cardImage)
        fileList.append(cardList[i])
        os.remove(cardList[i][0])

    image.save(imageFileName, quality=95)
    globalValues.addFile(str(ctx.guild.id), imageFileName);
    os.remove(imageFileName);

    return fileList

##############################################################################################################################################

async def generateTournamentImage(ctx, backgroundTuple, participantList, shuffle):

    if len(participantList) < 3:
        await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, you cannot close a tournament with less than 3 participants."))
        return None

    cardList = []

    for card in participantList:
        cardList.append((card[0], card[1]))

    if shuffle:
        shuffleCards(cardList)

    fileList = generateTournamentMatches(ctx, backgroundTuple, cardList)

    return fileList

##############################################################################################################################################

def generateTournamentMatches(ctx, backgroundTuple, cardList):

    logNum = math.log(len(cardList), 2)

    if not int(logNum) == logNum:
        logNum = int(logNum) + 1
    
    totNum = 2 ** logNum

    i = 1
    while len(cardList) < totNum:
        cardList.insert(i, (globalValues.passCards, -1))
        i += 2

    bracket = generateTournamentBracket(cardList)

    pairs = []
    generatePairs(bracket, pairs)

    return generateMatchFiles(ctx, backgroundTuple, pairs)

##############################################################################################################################################
 
def generateTournamentBracket(cardList):

    if len(cardList) <= 2:
        return cardList

    num = int(len(cardList) / 2)
    return [generateTournamentBracket(cardList[:num]), generateTournamentBracket(cardList[num:])]

##############################################################################################################################################

def generatePairs(bracket, pairs):

    if not isinstance(bracket[0], type([])):
        pairs.append(bracket)

    else:
        generatePairs(bracket[0], pairs)
        generatePairs(bracket[1], pairs)

##############################################################################################################################################

def generateMatchFiles(ctx, backgroundTuple, pairs):

    fileList = []

    for pair in pairs:
        
        fileNames =[]
        
        req = urllib.request.Request(globalValues.backgrounds.get(backgroundTuple[0])[backgroundTuple[1]][0], headers=globalValues.header)
        backgroundImage = Image.open(urlopen(req))
        backgroundImage.convert('RGBA')
        image = backgroundImage.copy()
        imageFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-0" + ".png"

        fileNames.append(imageFileName)
        
        for i in range(len(pair)):
            if pair[i][1] == -1:
                req = urllib.request.Request(pair[i][0], headers=globalValues.header)
                cardImage = Image.open(urlopen(req))
                cardImage.convert('RGBA')
                cardFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-" + "pass" + ".png"
                cardImage.save(cardFileName, quality=95)
                globalValues.addFile(str(ctx.guild.id), cardFileName);
                os.remove(cardFileName);
                image.paste(cardImage, (globalValues.cardCoordinates.get(backgroundTuple[0])[i][0], globalValues.cardCoordinates.get(backgroundTuple[0])[i][1]), cardImage)
                fileNames.append((cardFileName, pair[i][1]))
            else:
                globalValues.getFile(str(ctx.guild.id), pair[i][0])
                cardImage = Image.open(pair[i][0])
                image.paste(cardImage, (globalValues.cardCoordinates.get(backgroundTuple[0])[i][0], globalValues.cardCoordinates.get(backgroundTuple[0])[i][1]), cardImage)
                fileNames.append(pair[i])
                os.remove(pair[i][0])

        image.save(imageFileName, quality=95)
        globalValues.addFile(str(ctx.guild.id), imageFileName);
        os.remove(imageFileName);
        fileList.append(fileNames)

    return fileList

##############################################################################################################################################

async def confirmBrawl(ctx, backgroundTuple, name):

    brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)

    participantTuple = brawl[PARTICIPANT_INDEX]
    timeList = brawl[TIME_INDEX]
    reactionList = brawl[REACTION_INDEX]

    oldParticipantDict = dict(participantTuple[0])

    confirmed = False
    while not confirmed:

        fileList = await generateBrawlImage(ctx, backgroundTuple, participantTuple[0])
        if fileList == None:
            return None

        durationStr = getTimeStr(timeList)

        embedVar = discord.Embed(title=name, description="Duration: " + durationStr)
        globalValues.getFile(str(ctx.guild.id), fileList[0])
        imageFile = discord.File(fileList[0])
        embedVar.set_image(url="attachment://" + fileList[0])
        preview = await ctx.channel.send(file=imageFile, embed=embedVar)
        os.remove(fileList[0])
        for i in range(len(participantTuple[0])):
            await preview.add_reaction(reactionList[i])

        confirmStr = str("Is what you see above correct?\n" +
                         "React with what you want to change:\n" + 
                         "🇳 : change the name\n" +
                         "🇧 : change the background\n" +
                         "🇷 : change the card reactions\n" +
                         "⏲️ : change the duration\n" +
                         "🎴 : edit the participant list\n" +
                         "✅ : looks good\n" + 
                         "❌ : cancel close")

        embedVar = discord.Embed(title="Confirm Close", description=confirmStr)
        confirm = await ctx.channel.send(embed=embedVar)
        await confirm.add_reaction('🇳')
        await confirm.add_reaction('🇧')
        await confirm.add_reaction('🇷')
        await confirm.add_reaction('⏲️')
        await confirm.add_reaction('🎴')
        await confirm.add_reaction('✅')
        await confirm.add_reaction('❌')

        def check(react, user):
            return react.message == confirm and user == ctx.author and (react.emoji == '🇳' or react.emoji == '🇧' or react.emoji == '🇷' or react.emoji == '⏲️' or react.emoji == '🎴' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Close", description=confirmStr, color=discord.Color.green())
                await confirm.edit(embed=embedVar)
                confirmed = True
            elif reaction == '❌':
                raise asyncio.TimeoutError
            else:
                embedVar = discord.Embed(title="Confirm Close", description=confirmStr, color=discord.Color.blue())
                await confirm.edit(embed=embedVar)

                if reaction == '🇳':
                    name = await host.chooseName(ctx, "brawl")
                    if not name:
                        raise asyncio.TimeoutError
                elif reaction == '🇧':
                    backgroundTuple = await host.chooseBackground(ctx, len(participantTuple[0]))
                    if not backgroundTuple:
                        raise asyncio.TimeoutError    
                elif reaction == '🇷':
                    reactionList = await host.chooseReactions(ctx, len(participantTuple[0]))
                    if not reactionList:
                        raise asyncio.TimeoutError
                elif reaction == '⏲️':
                    timeList = await host.chooseTime(ctx, "brawl")
                    if not timeList:
                        raise asyncio.TimeoutError
                elif reaction == '🎴':
                    origLen = len(participantTuple[0])
                    participantDict = await chooseParticipant(ctx, "brawl", participantTuple[0])
                    if not participantDict:
                        raise asyncio.TimeoutError
                    participantTuple[0] = participantDict
                    if not participantTuple[0]:
                        raise asyncio.TimeoutError
                    if len(participantTuple[0]) != origLen:
                        await ctx.channel.send(embed=discord.Embed(description="You've changed the number of participants, please choose a different background and reactions."))
                        backgroundTuple = await host.chooseBackground(ctx, len(participantTuple[0]))
                        if not backgroundTuple:
                            raise asyncio.TimeoutError
                        reactionList = await host.chooseReactions(ctx, len(participantTuple[0]))
                        if not reactionList:
                            raise asyncio.TimeoutError
                try:
                    globalValues.removeFile(str(ctx.guild.id), fileList[0])
                except:
                    pass

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title="Confirm Close", description=confirmStr, color=discord.Color.red())
            await confirm.edit(embed=embedVar)
            try:
                globalValues.removeFile(str(ctx.guild.id), fileList[0])
            except:
                pass
            return None

    removeCards = {k:v for k, v in oldParticipantDict.items() if k not in participantTuple[0]}

    for card in removeCards.values():
        try:
            globalValues.removeFile(str(ctx.guild.id), card[0])
        except:
            pass

    return (name, ["brawl", 2, participantTuple, timeList, backgroundTuple, reactionList, fileList])

##############################################################################################################################################

async def confirmTournament(ctx, name):

    brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)

    oldParticipantTuple = brawl[PARTICIPANT_INDEX]
    timeList = brawl[TIME_INDEX]
    backgroundTuple = brawl[BACKGROUND_INDEX]
    reactionList = brawl[REACTION_INDEX]

    participantTuple = list(oldParticipantTuple)

    cardList = []

    for id, card in participantTuple[0].items():
        cardList.append((card[0], id))

    shuffleCards(cardList)

    shuffle = True
    confirmed = False
    while not confirmed:

        fileList = await generateTournamentImage(ctx, backgroundTuple, cardList, shuffle)
        shuffle = False
        if fileList == None:
            return

        durationStr = getTimeStr(timeList[0])
        tiebreakerStr = getTimeStr(timeList[1])
        delayStr = getTimeStr(timeList[2])

        embedVar = discord.Embed(title=name, description="Match duration: " + durationStr + "\nTiebreaker match duration: " + tiebreakerStr + "\nDelay between matches: " + delayStr)
        await ctx.channel.send(embed=embedVar)
        await ctx.channel.send(embed=discord.Embed(title="Preview of round 1 matches"))
        for i in range(len(fileList)):
            embedVar = discord.Embed(title="Match " + str(i + 1))
            globalValues.getFile(str(ctx.guild.id), fileList[i][0])
            imageFile = discord.File(fileList[i][0])
            embedVar.set_image(url="attachment://" + fileList[i][0])
            preview = await ctx.channel.send(file=imageFile, embed=embedVar)
            os.remove(fileList[i][0])
            for reaction in reactionList:
                await preview.add_reaction(reaction)

        confirmStr = str("Is what you see above correct?\n" +
                         "React with what you want to change:\n" + 
                         "🇳 : change the name\n" +
                         "🇧 : change the background\n" +
                         "🇷 : change the card reactions\n" +
                         "⏲️ : change the duration\n" +
                         "🎴 : edit the participant list\n" +
                         "🎲 : reroll matches\n" +
                         "✅ : looks good\n" +
                         "❌ : cancel close")

        embedVar = discord.Embed(title="Confirm Close", description=confirmStr)
        confirm = await ctx.channel.send(embed=embedVar)
        await confirm.add_reaction('🇳')
        await confirm.add_reaction('🇧')
        await confirm.add_reaction('🇷')
        await confirm.add_reaction('⏲️')
        await confirm.add_reaction('🎴')
        await confirm.add_reaction('🎲')
        await confirm.add_reaction('✅')
        await confirm.add_reaction('❌')

        def check(react, user):
            return react.message == confirm and user == ctx.author and (react.emoji == '🇳' or react.emoji == '🇧' or react.emoji == '🇷' or react.emoji == '⏲️' or react.emoji == '🎴' or react.emoji == '🎲' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Close", description=confirmStr, color=discord.Color.green())
                await confirm.edit(embed=embedVar)
                confirmed = True
            elif reaction == '❌':
                raise asyncio.TimeoutError
            else:
                embedVar = discord.Embed(title="Confirm Close", description=confirmStr, color=discord.Color.blue())
                await confirm.edit(embed=embedVar)

                if reaction == '🇳':
                    name = await host.chooseName(ctx, "tournament")
                    if not name:
                        raise asyncio.TimeoutError
                elif reaction == '🇧':
                    backgroundTuple = await host.chooseBackground(ctx, 2)
                    if not backgroundTuple:
                        raise asyncio.TimeoutError    
                elif reaction == '🇷':
                    reactionList = await host.chooseReactions(ctx, 2)
                    if not reactionList:
                        raise asyncio.TimeoutError
                elif reaction == '⏲️':
                    timeList = await host.chooseTime(ctx, "tournament")
                    if not timeList:
                        raise asyncio.TimeoutError
                elif reaction == '🎴':
                    participantDict = await chooseParticipants(ctx, "tournament", name, participantTuple[0])
                    if not participantDict:
                        raise asyncio.TimeoutError
                    participantTuple[0] = participantDict
                    cardList =[]
                    for id, card in participantTuple[0].items():
                        cardList.append((card[0], id))
                    shuffleCards(cardList)
                elif reaction == '🎲':
                    shuffleCards(cardList)
                    shuffle = True

                for match in fileList:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), match[0])
                    except OSError:
                        pass
                    if match[1][1] == -1:
                        try:
                            globalValues.removeFile(str(ctx.guild.id), match[1][0])
                        except OSError:
                            pass
                    if match[2][1] == -1:
                        try:
                            globalValues.removeFile(str(ctx.guild.id), match[2][0])
                        except OSError:
                            pass

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title="Confirm Close", description=confirmStr, color=discord.Color.red())
            await confirm.edit(embed=embedVar)
            for match in fileList:
                try:
                    globalValues.removeFile(str(ctx.guild.id), match[0])
                except OSError:
                    pass
                if match[1][1] == -1:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), match[1][0])
                    except OSError:
                        pass
                if match[2][1] == -1:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), match[2][0])
                    except OSError:
                        pass
            return None

    removeDict = {k:v for k, v in oldParticipantTuple[0].items() if k not in participantTuple[0]}

    for id, card in removeDict.items():
        globalValues.removeFile(str(ctx.guild.id), card[0])

    return (name, ["tournament", 2, participantTuple, timeList, backgroundTuple, reactionList, fileList])

##############################################################################################################################################

async def chooseParticipants(ctx, typeOfBrawl, name, participantDict):

    oldParticipantDict = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)[PARTICIPANT_INDEX][0]

    oldParticipantList = []

    for key, value in oldParticipantDict.items():
        oldParticipantList.append([key, oldParticipantDict.get(key)])

    participantList = list(oldParticipantList)

    optionStr = str("This is the current participant list for " + name + "\n" +
                    "React with the action you would like to perform:\n" +
                    "⬅️ : show the previous 20 participants\n" +
                    "➡️ : show the next 20 participant\n" +
                    "🔍 : search for a participant\n" +
                    "🆔 : remove participants by ID or @\n" +
                    "🎴 : remove participants by card codes\n"
                    "✅ : save changes\n" +
                    "❌ : delete changes")
    
    currentIndex = 0
    startIndex = currentIndex
    endIndex = startIndex + 20
    if endIndex > len(participantList):
        endIndex = len(participantList)
    listStr = ""
    for i in range(startIndex, endIndex):
        listStr += "<@" + str(participantList[i][0]) + ">, " +  "**`" + participantList[i][1][1] + "`**\n"
    currentIndex = endIndex

    footerStr = "Showing participants " + str(startIndex + 1) + "-" + str(endIndex) + " of " + str(len(participantList))

    embedVar = discord.Embed(title=name + " Participant Editor", description=optionStr + "\n\n" + listStr)
    embedVar.set_footer(text=footerStr)
    message = await ctx.channel.send(embed=embedVar)

    confirmed = False
    while not confirmed:

        await message.add_reaction('⬅️')
        await message.add_reaction('➡️')
        await message.add_reaction('🔍')
        await message.add_reaction('🆔')
        await message.add_reaction('🎴')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def check(react, user):
            return react.message == message and user == ctx.author and (react.emoji == '⬅️' or react.emoji == '➡️' or react.emoji == '🔍' or react.emoji == '✏️' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '⬅️' or reaction == '➡️':
                if reaction == '⬅️':
                    startIndex = currentIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    endIndex = startIndex + 20
                    if endIndex > len(participantList):
                        endIndex = len(participantList)
                    currentIndex = startIndex
                    listStr = ""
                    for i in range(startIndex, endIndex):
                        listStr += "<@" + str(participantList[i][0]) + ">, " +  "**`" + participantList[i][1][1] + "`**\n"
                    footerStr = "Showing participants " + str(startIndex + 1) + "-" + str(endIndex) + " of " + str(len(participantList))
                else:
                    startIndex = currentIndex + 20
                    endIndex = startIndex + 20
                    if endIndex > len(participantList):
                        endIndex = len(participantList)
                    startIndex = endIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    currentIndex = startIndex
                    listStr = ""
                    for i in range(startIndex, endIndex):
                        listStr += "<@" + str(participantList[i][0]) + ">, " +  "**`" + participantList[i][1][1] + "`**\n"
                    footerStr = "Showing participants " + str(startIndex + 1) + "-" + str(endIndex) + " of " + str(len(participantList))

                embedVar = discord.Embed(title=name + " Participant Editor", description=optionStr + "\n\n" + listStr)
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)

            elif reaction == '✅':
                embedVar = discord.Embed(title=name + " Participant Editor", description=optionStr + "\n\n" + listStr, color=discord.Color.green())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                confirmed = True

            elif reaction == '❌':
                raise asyncio.TimeoutError

            else:
                embedVar = discord.Embed(title=name + "Participant Editor", description=optionStr + "\n\n" + listStr, color=discord.Color.blue())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                if reaction == '🔍':
                    participant = await search(ctx, participantList)
                    if participant == None:
                        raise asyncio.TimeoutError
                elif reaction == '🆔':
                    participantList = await delete(ctx, typeOfBrawl, 0, participantList)
                    if participantList == None:
                        raise asyncio.TimeoutError
                elif reaction == '🎴':
                    participantList = await delete(ctx, typeOfBrawl, 1, participantList)
                    if participantList == None:
                        raise asyncio.TimeoutError

                currentIndex = 0
                startIndex = currentIndex
                endIndex = startIndex + 20
                if endIndex > len(participantList):
                    endIndex = len(participantList)
                listStr = ""
                for i in range(startIndex, endIndex):
                    listStr += "<@" + str(participantList[i][0]) + ">, " +  "**`" + participantList[i][1][1] + "`**\n"
                currentIndex = endIndex

                footerStr = "Showing participants " + str(startIndex + 1) + "-" + str(endIndex) + " of " + str(len(participantList))

                embedVar = discord.Embed(title=name + "Participant Editor", description=optionStr + "\n\n" + listStr)
                embedVar.set_footer(text=footerStr)
                message = await ctx.channel.send(embed=embedVar)

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title=name + "Participant Editor", description=optionStr + "\n\n" + listStr, color=discord.Color.red())
            embedVar.set_footer(text=footerStr)
            await message.edit(embed=embedVar)
            return None

    participantDict = {}

    for participant in participantList:
        participantDict[participant[0]] = participant[1]

    return participantDict

##############################################################################################################################################

async def search(ctx, participantList):

    await ctx.channel.send(embed=discord.Embed(title="Participant Search", description="Please input the participant you would like to search for. Please enter your search in one of the given formats (do not type < or >).\n\nAccepted inputs:\nid: <participant ID or @>\ncode: <card code>"))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author and (m.content.startswith("id:") or m.content.startswith("code:"))

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        if message.content.startswith("id:"):
            search = message.content[3:].strip()
            search = search.replace('<', '')
            search = search.replace('@', '')
            search = search.replace('!', '')
            search = search.replace('>', '')
            try:
                search = int(search)
            except:
                await error(ctx, 4, "id:" + str(search))
                return ()

            for participant in participantList:
                if participant[0] == search:
                    embedVar = discord.Embed(description="<@" + str(participant[0])  + ">")
                    globalValues.getFile(str(ctx.guild.id), participant[1][0])
                    imageFile = discord.File(participant[1][0])
                    embedVar.set_image(url="attachment://" + participant[1][0])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(participant[1][0])
                    return participant
            await error(ctx, 4, "id:" + str(search))
            return ()
        elif message.content.startswith("code:"):
            search = message.content[5:].strip()
            for participant in participantList:
                if participant[1][1] == search:
                    embedVar = discord.Embed(description="<@" + str(participant[0])  + ">")
                    globalValues.getFile(str(ctx.guild.id), participant[1][0])
                    imageFile = discord.File(participant[1][0])
                    embedVar.set_image(url="attachment://" + participant[1][0])
                    await ctx.channel.send(file=imageFile, embed=embedVar)
                    os.remove(participant[1][0])
                    return participant
            await error(ctx, 4, "code:" + str(search))
            return ()
        else:
            await ctx.channel.send(embed=discord.Embed(description="Please begin your search with either \"id:\" or \"code\"."))
    except asyncio.TimeoutError:
        return None



##############################################################################################################################################

async def deleteParticipants(ctx, typeOfBrawl, code, participantDict):

    if code == 0:

        await ctx.channel.send(embed=discord.Embed(title="Delete Participants by ID or @", description="Please list the IDs or @'s of the participants you would like to remove separated by commas."))

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            message = globalValues.bot.wait_for('message', timeout=60, check=check)
            idList = message.content
            idList.replace('<', '')
            idList.replace('@', '')
            idList.replace('>', '')
            idList = idList.split(',')
            for id in idList:
                id = id.strip()

            newParticipantList = [participant for participant in participantList if participant[0] not in idList]

            totalCount = len(newParticipantList) - len(participantList)
            removeCount = len(participantList) - len(newParticipantList)

            if typeOfBrawl == "brawl" and totalCount < 2:
                await ctx.channel.send(embed=discord.Embed(description="Cannot close a brawl with less than 2 participants. Cancelling participant deletion."))
                return participantList
            elif typeOfBrawl == "tournament" and totalCount < 3:
                await ctx.channel.send(embed=discord.Embed(description="Cannot close a tournament with less than 3 participants. Cancelling participant deletion."))
                return participantList
            else:
                await ctx.channel.send(embed=discord.Embed(description="Removed " + removeCount + " participants."))
                return newParticipantList
        
        except asyncio.TimeoutError:
            return None

    else:

        await ctx.channel.send(embed=discord.Embed(title="Delete Participants by Card Code", description="Please list the card codes of the participants you would like to remove separated by commas."))

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            message = globalValues.bot.wait_for('message', timeout=60, check=check)
            codeList = message.content
            codeList = codeList.split(',')
            for code in codeList:
                code = code.strip()

            newParticipantList = [participant for participant in participantList if participant[1][1] not in codeList]


            removeCount = len(participantList) - len(newParticipantList)

            if typeOfBrawl == "brawl" and totalCount < 2:
                await ctx.channel.send(embed=discord.Embed(description="Cannot close a brawl with less than 2 participants. Cancelling participant deletion."))
                return participantList
            elif typeOfBrawl == "tournament" and totalCount < 3:
                await ctx.channel.send(embed=discord.Embed(description="Cannot close a tournament with less than 3 participants. Cancelling participant deletion."))
                return participantList
            else:
                await ctx.channel.send(embed=discord.Embed(description="Removed " + removeCount + " participants."))
                return newParticipantList
        
        except asyncio.TimeoutError:
            return None

##############################################################################################################################################

def shuffleCards(cardList):

    random.shuffle(cardList)

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
    return timeStr

##############################################################################################################################################