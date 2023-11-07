# edit.py
# By: PVCPipe01
# contains the edit command

import discord
import os
from discord.ext import commands
import asyncio
import pickle

import globalValues
import host
import close

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX

async def edit(ctx, arg1):

    name = arg1
    typeOfBrawl = ""
    accessState = -1
    info = []

    errorCode = -1

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        if not globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name):
            errorCode = 5
            
        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 1:
            errorCode = 1

        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 3:
            errorCode = 3

        else:
            info = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)
            typeOfBrawl = info[TYPE_INDEX]
            accessState = info[ACCESS_INDEX]
            globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 1

    if errorCode != -1:
        await error(ctx, errorCode, name)
        return

    if accessState == 0 and typeOfBrawl == "brawl":
        info = await editOpenBrawl(ctx, name, info)
    elif accessState == 0 and typeOfBrawl == "tournament":
        info = await editOpenTournament(ctx, name, info)
    elif accessState == 2 and typeOfBrawl == "brawl":
        info = await editOpenBrawl(ctx, name, info)
    else:
        info = await editClosedTournament(ctx, name, info)

    if info == None:
        globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = accessState
        await ctx.channel.send(embed=discord.Embed(description="Editing cancelled", color=discord.Color.red()))
        return

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        if name == info[0]:
            globalValues.savedCompetitions[str(ctx.guild.id)][info[0]] = info[1]

        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(info[0]) == None:
            globalValues.savedCompetitions.get(str(ctx.guild.id)).pop(name)
            globalValues.savedCompetitions[str(ctx.guild.id)][info[0]] = info[1]

        elif globalValues.savedCompetitions.get(str(ctx.guild.id)).get(info[0]) != None:
            globalValues.savedCompetitions[str(ctx.guild.id)][name] = info[1]
            nameTaken = True
        
        await globalValues.store()

    await ctx.channel.send(embed=discord.Embed(description="Editing complete", color=discord.Color.green()))

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

async def editOpenBrawl(ctx, name, info):

    accessState = info[ACCESS_INDEX]
    oldParticipantTuple = info[PARTICIPANT_INDEX]
    participantTuple = list(oldParticipantTuple)
    maxParticipants = info[PARTICIPANT_INDEX][2]
    timeList = info[TIME_INDEX]
    backgroundTuple = info[BACKGROUND_INDEX]
    reactionList = info[REACTION_INDEX]
    fileList = info[FILE_INDEX]

    sampleFileName = ""

    confirmed = False
    while not confirmed:

        timeStr = host.getTimeStr(timeList)

        sampleFileName = host.generateSample(ctx, backgroundTuple)

        restricted = False
        if participantTuple[1] != None:
            restricted = True
                
        embedVar = discord.Embed(title=name, description="Open\nRestricted: " + str(restricted) + "\nMax number of participants: " + str(maxParticipants) + "\nDuration: " + timeStr)
        globalValues.getFile(str(ctx.guild.id), sampleFileName)
        sampleImage = discord.File(sampleFileName)
        embedVar.set_image(url="attachment://" + sampleFileName)
        preview = await ctx.channel.send(file=sampleImage, embed=embedVar)
        os.remove(sampleFileName)
        for i in range(maxParticipants):
            await preview.add_reaction(reactionList[i])

        embedVar = discord.Embed(title="Edit Brawl",
                                 description="Is what you see above correct?\n" +
                                             "React with what you want to change:\n" +
                                             "🇳 : change the name\n" +
                                             "#️⃣ : change the max number of participants\n" +
                                             "⏲️ : change the duration\n" +
                                             "🇧 : change the background\n" +
                                             "🇷 : change the reactions\n" +
                                             "🎴 : edit participants and eligibility\n" +
                                             "✅ : looks good\n" + 
                                             "❌ : cancel edits")

        message = await ctx.channel.send(embed=embedVar)
        await message.add_reaction('🇳')
        await message.add_reaction('#️⃣')
        await message.add_reaction('⏲️')
        await message.add_reaction('🇧')
        await message.add_reaction('🇷')
        await message.add_reaction('🎴')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def check(react, user):
            return react.message == message and user == ctx.message.author and (react.emoji == '🇳' or react.emoji == '#️⃣' or react.emoji == '⏲️' or react.emoji == '🇧' or react.emoji == '🇷' or react.emoji == '🎴' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '✅':
                embedVar = discord.Embed(title="Edit Brawl",
                                         description="Is what you see above correct?\n" +
                                                     "React with what you want to change:\n" +
                                                     "🇳 : change the name\n" +
                                                     "#️⃣ : change the max number of participants\n" +
                                                     "⏲️ : change the duration\n" +
                                                     "🇧 : change the background\n" +
                                                     "🇷 : change the reactions\n" +
                                                     "🎴 : edit participants and eligibility\n" +
                                                     "✅ : looks good\n" + 
                                                     "❌ : cancel edits",
                                         color=discord.Color.green())
                await message.edit(embed=embedVar)
                confirmed = True
            elif reaction == '❌':
                raise asyncio.TimeoutError
            else:
                if reaction == '🇳':
                    name = await host.chooseName(ctx, "brawl")
                    if name == None:
                        raise asyncio.TimeoutError
                elif reaction == '#️⃣':
                    origMax = maxParticipants
                    maxParticipants = await chooseNumParticipants(ctx, "brawl", participantTuple)
                    if not maxParticipants:
                        raise asyncio.TimeoutError
                    if origMax != maxParticipants:
                        await ctx.channel.send(embed=discord.Embed(description="You changed the max number of participants, please choose a different background and reactions."))
                        backgroundTuple = await host.chooseBackground(ctx, maxParticipants)
                        if not backgroundTuple:
                            raise asyncio.TimeoutError
                        reactionList = await host.chooseReactions(ctx, maxParticipants)
                        if not reactionList:
                            raise asyncio.TimeoutError
                elif reaction == '⏲️':
                    timeList = await host.chooseTime(ctx, "brawl")
                    if timeList == None:
                        raise asyncio.TimeoutError
                elif reaction == '🇧':
                    backgroundTuple = await host.chooseBackground(ctx, maxParticipants)
                elif reaction == '🇷':
                    reactionList = await host.chooseReactions(ctx, maxParticipants)
                elif reaction == '🎴':
                    participantTuple = await participantMenu(ctx, "brawl", accessState, name, participantTuple)
                    if participantTuple == None:
                        raise asyncio.TimeoutError
            
            try:
                globalValues.removeFile(str(ctx.guild.id), sampleFileName)
            except:
                pass

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title="Edit Brawl",
                                     description="Is what you see above correct?\n" +
                                                 "React with what you want to change:\n" +
                                                 "🇳 : change the name\n" +
                                                 "#️⃣ : change the max number of participants\n" +
                                                 "⏲️ : change the duration\n" +
                                                 "🇧 : change the background\n" +
                                                 "🇷 : change the reactions\n" +
                                                 "🎴 : edit participants and eligibility\n" +
                                                 "✅ : looks good\n" + 
                                                 "❌ : cancel edits",
                                     color=discord.Color.red())
            await message.edit(embed=embedVar)
            try:
                globalValues.removeFile(str(ctx.guild.id), sampleFileName)
            except:
                pass
            return None

    removeDict = {k:v for k, v in oldParticipantTuple[0].items() if k not in participantTuple[0]}

    for v in removeDict.values():
        try:
            globalValues.removeFile(str(ctx.guild.id), v[0]);
        except:
            pass

    participantTuple[2] = maxParticipants

    return (name, ["brawl", 0, participantTuple, timeList, backgroundTuple, reactionList, fileList])

##############################################################################################################################################

async def editOpenTournament(ctx, name, info):

    accessState = info[ACCESS_INDEX]
    oldParticipantTuple = info[PARTICIPANT_INDEX]
    participantTuple = list(oldParticipantTuple)
    maxParticipants = info[PARTICIPANT_INDEX][2]
    timeList = info[TIME_INDEX]
    backgroundTuple = info[BACKGROUND_INDEX]
    reactionList = info[REACTION_INDEX]
    fileList = info[FILE_INDEX]

    sampleFileName = ""

    confirmed = False
    while not confirmed:

        timeStr = host.getTimeStr(timeList)

        sampleFileName = host.generateSample(ctx, backgroundTuple)

        eligibilityList = participantTuple[1]

        restricted = False
        if eligibilityList != None:
            restricted = True
                
        durationStr = getTimeStr(timeList[0])
        tiebreakerStr = getTimeStr(timeList[1])
        delayStr = getTimeStr(timeList[2])

        embedVar = discord.Embed(title=name, description="Open\nRestricted: " + str(restricted) + "\nMax number of participants: " + str(maxParticipants) + "\nMatch duration: " + durationStr + "\nTiebreaker match duration: " + tiebreakerStr + "\nDelay between matches: " + delayStr)
        globalValues.getFile(str(ctx.guild.id), sampleFileName)
        sampleImage = discord.File(sampleFileName)
        embedVar.set_image(url="attachment://" + sampleFileName)
        preview = await ctx.channel.send(file=sampleImage, embed=embedVar)
        os.remove(sampleFileName)
        for i in range(2):
            await preview.add_reaction(reactionList[i])

        embedVar = discord.Embed(title="Edit Tournament",
                                    description="Is what you see above correct?\n" +
                                                "React with what you want to change:\n" +
                                                "🇳 : change the name\n" +
                                                "#️⃣ : change the max number of participants\n" +
                                                "⏲️ : change the duration\n" +
                                                "🇧 : change the background\n" +
                                                "🇷 : change the reactions\n" +
                                                "🎴 : edit participants and eligibility\n" +
                                                "✅ : looks good\n" + 
                                                "❌ : cancel edits")

        message = await ctx.channel.send(embed=embedVar)
        await message.add_reaction('🇳')
        await message.add_reaction('#️⃣')
        await message.add_reaction('⏲️')
        await message.add_reaction('🇧')
        await message.add_reaction('🇷')
        await message.add_reaction('🎴')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def check(react, user):
            return react.message == message and user == ctx.message.author and (react.emoji == '🇳' or react.emoji == '#️⃣' or react.emoji == '⏲️' or react.emoji == '🇧' or react.emoji == '🇷' or react.emoji == '🎴' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '✅':
                embedVar = discord.Embed(title="Edit Tournament",
                                         description="Is what you see above correct?\n" +
                                                     "React with what you want to change:\n" +
                                                     "🇳 : change the name\n" +
                                                     "#️⃣ : change the max number of participants\n" +
                                                     "⏲️ : change the duration\n" +
                                                     "🇧 : change the background\n" +
                                                     "🇷 : change the reactions\n" +
                                                     "🎴 : edit participants and eligibility\n" +
                                                     "✅ : looks good\n" + 
                                                     "❌ : cancel edits",
                                         color=discord.Color.green())
                await message.edit(embed=embedVar)
                confirmed = True
            elif reaction == '❌':
                raise asyncio.TimeoutError
            else:
                if reaction == '🇳':
                    name = await host.chooseName(ctx, "tournament")
                    if name == None:
                        raise asyncio.TimeoutError
                elif reaction == '#️⃣':
                    maxParticipants = await chooseNumParticipants(ctx, "tournament", participantTuple)
                    if maxParticipants == None:
                        raise asyncio.TimeoutError
                elif reaction == '⏲️':
                    timeList = await host.chooseTime(ctx, "tournament")
                    if timeList == None:
                        raise asyncio.TimeoutError
                elif reaction == '🇧':
                    backgroundTuple = await host.chooseBackground(ctx, 2)
                elif reaction == '🇷':
                    reactionList = await host.chooseReactions(ctx, 2)
                elif reaction == '🎴':
                    participantTuple = await participantMenu(ctx, "tournament", accessState, name, participantTuple)
                    if participantTuple == None:
                        raise asyncio.TimeoutError

            globalValues.removeFile(str(ctx.guild.id), sampleFileName)

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title="Edit Tournament",
                                     description="Is what you see above correct?\n" +
                                                 "React with what you want to change:\n" +
                                                 "🇳 : change the name\n" +
                                                 "#️⃣ : change the max number of participants\n" +
                                                 "⏲️ : change the duration\n" +
                                                 "🇧 : change the background\n" +
                                                 "🇷 : change the reactions\n" +
                                                 "🎴 : edit participants and eligibility\n" +
                                                 "✅ : looks good\n" + 
                                                 "❌ : cancel edits",
                                     color=discord.Color.red())
            await message.edit(embed=embedVar)
            globalValues.removeFile(str(ctx.guild.id), sampleFileName)
            return None

    removeDict = {k:v for k, v in oldParticipantTuple[0].items() if k not in participantTuple[0]}

    for v in removeDict.values():
        try:
            globalValues.removeFile(str(ctx.guild.id), v[0])
        except:
            pass

    participantTuple[2] = maxParticipants

    return (name, ["tournament", 0, participantTuple, timeList, backgroundTuple, reactionList, fileList])

##############################################################################################################################################

async def editClosedBrawl(ctx, name, info):

    accessState = info[ACCESS_INDEX]
    oldParticipantTuple = info[PARTICIPANT_INDEX]
    participantTuple = list(oldParticipantTuple)
    maxParticipants = info[PARTICIPANT_INDEX][2]
    timeList = info[TIME_INDEX]
    backgroundTuple = info[BACKGROUND_INDEX]
    reactionList = info[REACTION_INDEX]
    oldFileList = info[FILE_INDEX]

    sampleFileName = ""

    confirmed = False
    while not confirmed:
        timeStr = host.getTimeStr(timeList)

        fileList = await generateBrawlImage(ctx, backgroundTuple, participantTuple[0])
        if fileList == None:
            return None
                
        embedVar = discord.Embed(title=name, description="Closed\nDuration: " + timeStr)
        globalValues.getFile(str(ctx.guild.id), sampleFileName)
        sampleImage = discord.File(sampleFileName)
        embedVar.set_image(url="attachment://" + sampleFileName)
        preview = await ctx.channel.send(file=sampleImage, embed=embedVar)
        os.remove(sampleFileName)
        for i in range(maxParticipants):
            await preview.add_reaction(reactionList[i])

        embedVar = discord.Embed(title="Edit Brawl",
                                 description="Is what you see above correct?\n" +
                                             "React with what you want to change:\n" +
                                             "🇳 : change the name\n" +
                                             "⏲️ : change the duration\n" +
                                             "🇧 : change the background\n" +
                                             "🇷 : change the reactions\n" +
                                             "🎴 : edit participants and eligibility\n" +
                                             "✅ : looks good\n" + 
                                             "❌ : cancel edits")

        message = await ctx.channel.send(embed=embedVar)
        await message.add_reaction('🇳')
        await message.add_reaction('⏲️')
        await message.add_reaction('🇧')
        await message.add_reaction('🇷')
        await message.add_reaction('🎴')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def check(react, user):
            return react.message == message and user == ctx.message.author and (react.emoji == '🇳' or react.emoji == '⏲️' or react.emoji == '🇧' or react.emoji == '🇷' or react.emoji == '🎴' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '✅':
                embedVar = discord.Embed(title="Edit Brawl",
                                         description="Is what you see above correct?\n" +
                                                     "React with what you want to change:\n" +
                                                     "🇳 : change the name\n" +
                                                     "⏲️ : change the duration\n" +
                                                     "🇧 : change the background\n" +
                                                     "🇷 : change the reactions\n" +
                                                     "🎴 : edit participants and eligibility\n" +
                                                     "✅ : looks good\n" + 
                                                     "❌ : cancel edits",
                                         color=discord.Color.green())
                confirmed = True
            elif reaction == '❌':
                raise asyncio.TimeoutError
            else:
                if reaction == '🇳':
                    name = await host.chooseName(ctx, "brawl")
                    if name == None:
                        raise asyncio.TimeoutError
                elif reaction == '⏲️':
                    timeList = await host.chooseTime(ctx, "brawl")
                    if timeList == None:
                        raise asyncio.TimeoutError
                elif reaction == '🇧':
                    backgroundTuple = await host.chooseBackground(ctx, len(participantTuple[0]))
                    if backgroundTuple == None:
                        raise asyncio.TimeoutError
                elif reaction == '🇷':
                    reactionList = await host.chooseReactions(ctx, len(participantTuple[0]))
                    if reactionList == None:
                        raise asyncio.TimeoutError
                elif reaction == '🎴':
                    origLen = len(participantTuple[0])
                    participantTuple = await participantMenu(ctx, "brawl", accessState, name, participantTuple)
                    if participantTuple == None:
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
                    globalValues.removeFile(str(ctx.guild.id), fileList[0]);
                except:
                    pass
        except asyncio.TimeoutError:
            embedVar = discord.Embed(title="Edit Brawl",
                                     description="Is what you see above correct?\n" +
                                                "React with what you want to change:\n" +
                                                "🇳 : change the name\n" +
                                                "⏲️ : change the duration\n" +
                                                "🇧 : change the background\n" +
                                                "🇷 : change the reactions\n" +
                                                "🎴 : edit participants and eligibility\n" +
                                                "✅ : looks good\n" + 
                                                "❌ : cancel edits",
                                     color=discord.Color.red())
            try:
                globalValues.removeFile(str(ctx.guild.id), fileList[0]);
            except:
                pass
            return None

    try:
        globalValues.removeFile(str(ctx.guild.id), oldFileList[0]);
    except:
        pass

    removeDict = {k:v for k, v in oldParticipantTuple[0] if k not in participantTuple[0]}

    for v in removeDict.values():
        try:
            globalValues.removeFile(str(ctx.guild.id), v[0]);
        except:
            pass

    return (name, ["brawl", 2, participantTuple, timeList, backgroundTuple, reactionList, fileList])

##############################################################################################################################################

async def editClosedTournament(ctx, name, info):

    accessState = info[ACCESS_INDEX]
    oldParticipantTuple = info[PARTICIPANT_INDEX]
    participantTuple = list(oldParticipantTuple)
    timeList = info[TIME_INDEX]
    backgroundTuple = info[BACKGROUND_INDEX]
    reactionList = info[REACTION_INDEX]
    oldFileList = info[FILE_INDEX]

    cardList = []

    for id, card in participantTuple[0].items():
        cardList.append((card[0], id))

    close.shuffleCards(cardList)

    confirmed = False
    while not confirmed:

        fileList = await close.generateTournamentImage(ctx, backgroundTuple, cardList, False)
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
                         "🎴 : edit participants and eligibility\n" +
                         "🎲 : reroll matches\n" +
                         "✅ : looks good\n" +
                         "❌ : cancel close")

        embedVar = discord.Embed(title="Edit Tournament", description=confirmStr)
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
            return react.message == confirm and user == ctx.author and (react.emoji == '🇳' or react.emoji == '🇧' or react.emoji == '🇷' or react.emoji == '⏲️' or react.emoji == '🎴' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '✅':
                embedVar = discord.Embed(title="Edit Tournament", description=confirmStr, color=discord.Color.green())
                await confirm.edit(embed=embedVar)
                confirmed = True
            elif reaction == '❌':
                raise asyncio.TimeoutError
            else:
                embedVar = discord.Embed(title="Edit Tournament", description=confirmStr, color=discord.Color.blue())
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
                    origLen = len(participantTuple[0])
                    participantTuple[0] = await participantMenu(ctx, "tournament", accessState, name, participantTuple)
                    if not participantTuple[0]:
                        raise asyncio.TimeoutError
                    cardList =[]
                    for id, card in participantTuple[0].items():
                        cardList.append(card[0], id)
                    close.shuffleCards(cardList)
                elif reaction == '🎲':
                    close.shuffleCards(cardList)

                for match in fileList:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), match[0]);
                    except OSError:
                        pass
                    if match[1][1] == -1:
                        try:
                            globalValues.removeFile(str(ctx.guild.id), match[1][0]);
                        except OSError:
                            pass
                    if match[2][1] == -1:
                        try:
                            globalValues.removeFile(str(ctx.guild.id), match[2][0]);
                        except OSError:
                            pass

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title="Confirm Close", description=confirmStr, color=discord.Color.red())
            await confirm.edit(embed=embedVar)
            for match in fileList:
                try:
                    globalValues.removeFile(str(ctx.guild.id), match[0]);
                except OSError:
                    pass
                if match[1][1] == -1:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), match[1][0]);
                    except OSError:
                        pass
                if match[2][1] == -1:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), match[2][0]);
                    except OSError:
                        pass
            return

    for match in oldFileList:
        try:
            globalValues.removeFile(str(ctx.guild.id), match[0]);
        except:
            pass

    removeDict = {k:v for k, v in oldParticipantTuple[0] if k not in participantTuple[0]}

    for v in removeDict.values():
        try:
            globalValues.removeFile(str(ctx.guild.id), v[0]);
        except:
            pass

    return (name, ["tournament", 2, participantTuple, timeList, backgroundTuple, reactionList, fileList])

##############################################################################################################################################

async def participantMenu(ctx, typeOfBrawl, accessState, name, participantTuple):

    oldParticipantDict = participantTuple[0]

    oldParticipantList = []

    for key in oldParticipantDict:
        oldParticipantList.append([key, (oldParticipantDict.get(key))])

    participantList = oldParticipantList

    oldEligibilityList = participantTuple[1]

    eligibilityList = oldEligibilityList

    optionStr = str("This is the current participant list for " + name + "\n" +
                    "React with the action you would like to perform:\n" +
                    "⬅️ : show the previous 20 participants\n" +
                    "➡️ : show the next 20 participants\n" +
                    "🔍 : search for a participant\n" +
                    "🆔 : remove participants by ID or @\n" +
                    "🎴 : remove participants by card codes\n" +
                    "🇵 : edit participant eligibility\n" +
                    "🇨 : edit card eligibility\n" +
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

    footerStr = ""
    if len(participantList) == 0:
        footerStr = "Showing participants 0-0 out of 0"
    else:
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
        await message.add_reaction('🇵')
        await message.add_reaction('🇨')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def check(react, user):
            return react.message == message and user == ctx.author and (react.emoji == '⬅️' or react.emoji == '➡️' or react.emoji == '🔍' or react.emoji == '🆔' or react.emoji == '🎴' or react.emoji == '🇵' or react.emoji == '🇨' or react.emoji == '✅' or react.emoji == '❌')

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
                    tartIndex = currentIndex + 20
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
                embedVar = discord.Embed(title=name + " Participant Editor", description=optionStr + "\n\n" + listStr, color=discord.Color.red())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                return participantTuple

            else:
                embedVar = discord.Embed(title=name + " Participant Editor", description=optionStr + "\n\n" + listStr, color=discord.Color.blue())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                if reaction == '🔍':
                    participant = await searchParticipant(ctx, participantList)
                    if participant == None:
                        raise asyncio.TimeoutError
                elif reaction == '🆔':
                    origLen = len(participantList)
                    participantList = await delete(ctx, typeOfBrawl, accessState, 0, participantList)
                    if participantList == None:
                        raise asyncio.TimeoutError
                    if accessState == 2 and typeOfBrawl == "brawl":
                        if len(participantTuple[0]) != origLen:
                            await ctx.channel.send(embed=discord.Embed(description="You've changed the number of participants, please choose a different background and reactions."))
                            backgroundTuple = await host.chooseBackground(ctx, len(participantTuple[0]))
                            if not backgroundTuple:
                                raise asyncio.TimeoutError
                            reactionList = await host.chooseReactions(ctx, len(participantTuple[0]))
                            if not reactionList:
                                raise asyncio.TimeoutError
                elif reaction == '🎴':
                    origLen = len(participantList)
                    participantList = await delete(ctx, typeOfBrawl, accessState, 1, participantList)
                    if participantList == None:
                        raise asyncio.TimeoutError
                    if accessState == 2 and typeOfBrawl == "brawl":
                        if len(participantTuple[0]) != origLen:
                            await ctx.channel.send(embed=discord.Embed(description="You've changed the number of participants, please choose a different background and reactions."))
                            backgroundTuple = await host.chooseBackground(ctx, len(participantTuple[0]))
                            if not backgroundTuple:
                                raise asyncio.TimeoutError
                            reactionList = await host.chooseReactions(ctx, len(participantTuple[0]))
                            if not reactionList:
                                raise asyncio.TimeoutError
                elif reaction == '🇵':
                    infoTuple = await eligible(ctx, typeOfBrawl, accessState, participantList, eligibilityList)
                    participantList = infoTuple[0]
                    eligibilityList = infoTuple[1]
                    if eligibilityList == -1:
                        raise asyncio.TimeoutError
                elif reaction == '🇨':
                    eligibilityList = await editEligibleSeries(ctx, eligibilityList)
                    if eligibilityList == None:
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

                if len(participantList) == 0:
                    footerStr = "Showing participants 0-0 out of 0"
                else:
                    footerStr = "Showing participants " + str(startIndex + 1) + "-" + str(endIndex) + " of " + str(len(participantList))

                embedVar = discord.Embed(title=name + " Participant Editor", description=optionStr + "\n\n" + listStr)
                embedVar.set_footer(text=footerStr)
                message = await ctx.channel.send(embed=embedVar)

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title=name + " Participant Editor", description=optionStr + "\n\n" + listStr, color=discord.Color.red())
            embedVar.set_footer(text=footerStr)
            await message.edit(embed=embedVar)
            return None

    participantDict = {}

    for participant in participantList:
        participantDict[participant[0]] = participant[1]

    participantTuple[0] = participantDict
    participantTuple[1] = eligibilityList

    return participantTuple

##############################################################################################################################################

async def searchParticipant(ctx, participantList):

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

async def delete(ctx, typeOfBrawl, accessState, code, participantList):

    if code == 0:

        await ctx.channel.send(embed=discord.Embed(title="Delete Participants by ID or @", description="Please list the IDs or @'s of the participants you would like to remove separated by commas."))

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            message = await globalValues.bot.wait_for('message', timeout=60, check=check)
            idList = message.content
            idList = idList.replace('<', '')
            idList = idList.replace('@', '')
            idList = idList.replace('!', '')
            idList = idList.replace('>', '')
            idList = idList.split(',')
            for i in range(len(idList)):
                idList[i] = idList[i].strip()
                try:
                    idList[i] = int(idList[i])
                except:
                    pass

            newParticipantList = [participant for participant in participantList if participant[0] not in idList]

            removeCount = len(participantList) - len(newParticipantList)

            totalCount = len(newParticipantList) - len(participantList)
            removeCount = len(participantList) - len(newParticipantList)

            if typeOfBrawl == "brawl" and accessState == 2 and totalCount < 2:
                await ctx.channel.send(embed=discord.Embed(description="Cannot close a brawl with less than 2 participants. Cancelling participant deletion."))
                return participantList
            elif typeOfBrawl == "tournament" and accessState == 2 and totalCount < 3:
                await ctx.channel.send(embed=discord.Embed(description="Cannot close a tournament with less than 3 participants. Cancelling participant deletion."))
                return participantList
            else:
                await ctx.channel.send(embed=discord.Embed(description="Removed " + str(removeCount) + " participants."))
                return newParticipantList
        
        except asyncio.TimeoutError:
            return None

    else:

        await ctx.channel.send(embed=discord.Embed(title="Delete Participants by Card Code", description="Please list the card codes of the participants you would like to remove separated by commas."))

        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        try:
            message = await globalValues.bot.wait_for('message', timeout=60, check=check)
            codeList = message.content
            codeList = codeList.split(',')
            for i in range(len(codeList)):
                codeList[i] = codeList[i].strip()

            newParticipantList = [participant for participant in participantList if participant[1][1] not in codeList]

            totalCount = len(newParticipantList) - len(participantList)
            removeCount = len(participantList) - len(newParticipantList)

            if typeOfBrawl == "brawl" and accessState == 2 and totalCount < 2:
                await ctx.channel.send(embed=discord.Embed(description="Cannot close a brawl with less than 2 participants. Cancelling participant deletion."))
                return participantList
            elif typeOfBrawl == "tournament" and accessState == 2 and totalCount < 3:
                await ctx.channel.send(embed=discord.Embed(description="Cannot close a tournament with less than 3 participants. Cancelling participant deletion."))
                return participantList
            else:
                await ctx.channel.send(embed=discord.Embed(description="Removed " + str(removeCount) + " participants."))
                return newParticipantList
        
        except asyncio.TimeoutError:
            return None

##############################################################################################################################################

async def eligible(ctx, typeOfBrawl, accessState, participantList, eligibilityList):

    oldParticipantList = participantList
    oldEligibilityList = eligibilityList
    
    if accessState == 2:
        await ctx.channel.send(embed=discord.Embed(description="This " + typeOfBrawl + " is closed and the eligibility list cannot be edited."))
        return (participantList, eligibilityList)

    if eligibilityList == None:
        restrictedMessage = await ctx.channel.send(embed=discord.Embed(description="This " + typeOfBrawl + " is currently unrestricted and therefore has no eligibility list. Would you like to restrict the " + typeOfBrawl + "?\nThis will remove all participants from the participant list."))
        await restrictedMessage.add_reaction('✅')
        await restrictedMessage.add_reaction('❌')


        def restrictedCheck(react, user):
            return react.message == restrictedMessage and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=restrictedCheck)
            reaction = reaction[0].emoji

            if reaction == '✅':
                await restrictedMessage.edit(embed=discord.Embed(description="This " + typeOfBrawl + " is currently unrestricted and therefore has no eligibility list. Would you like to restrict the " + typeOfBrawl + "?\nThis will remove all participants from the participant list.", color=discord.Color.green()))
                participantList = []
                eligibilityList = [[[], []], []]
            else:
                await restrictedMessage.edit(embed=discord.Embed(description="This " + typeOfBrawl + " is currently unrestricted and therefore has no eligibility list. Would you like to restrict the " + typeOfBrawl + "?\nThis will remove all participants from the participant list.", color=discord.Color.red()))
                return (participantList, None)
        except asyncio.TimeoutError:
            await restrictedMessage.edit(embed=discord.Embed(description="This " + typeOfBrawl + " is currently unrestricted and therefore has no eligibility list. Would you like to restrict the " + typeOfBrawl + "?\nThis will remove all participants from the participant list.", color=discord.Color.red()))
            return -1
        
    eligibleIDs = eligibilityList[0][0]
    eligibleRoles = eligibilityList[0][1]
    eligibleSeries = eligibilityList[1]

    optionStr = str("React with what you want to change:\n" +
                    "⬅️ : show the previous 20 eligible participants\n" +
                    "➡️ : show the next 20 eligible participants\n" +
                    "🔍 : search for an eligible participant\n" +
                    "➕ : add eligible participant(s)\n" +
                    "➖ : remove eligible participant(s)\n" +
                    "🏷️ : edit eligible roles\n" +
                    "🚫 : remove restriction\n" +
                    "✅ : save changes\n" +
                    "❌ : delete changes")
    
    idStr = ""
    currentIndex = 0
    startIndex = currentIndex
    endIndex = currentIndex + 20
    if endIndex > len(eligibleIDs):
        endIndex = len(eligibleIDs)
    for i in range(startIndex, endIndex):
        idStr = idStr + "<@" + str(eligibleIDs[i]) + ">\n"

    footerStr = ""
    if len(eligibleIDs) == 0:
        footerStr = footerStr + "Showing eligible participants 0-0 out of 0"
    else:
        footerStr = footerStr + "Showing eligible participants " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleIDs))

    embedVar = discord.Embed(title="Eligibility Editor", description=optionStr + "\n\n" + idStr)
    embedVar.set_footer(text=footerStr)
    message = await ctx.channel.send(embed=embedVar)

    confirmed = False
    while not confirmed:
        
        await message.add_reaction('⬅️')
        await message.add_reaction('➡️')
        await message.add_reaction('🔍')
        await message.add_reaction('➕')
        await message.add_reaction('➖')
        await message.add_reaction('🏷️')
        await message.add_reaction('🚫')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def check(react, user):
            return react.message == message and user == ctx.author and (react.emoji == '⬅️' or react.emoji == '➡️' or react.emoji == '🔍' or react.emoji == '➖' or react.emoji == '➕' or react.emoji == '🏷️' or react.emoji == '📺' or react.emoji == '🚫' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '⬅️' or reaction == '➡️':
                if reaction == '⬅️':
                    startIndex = currentIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    endIndex = startIndex + 20
                    if endIndex > len(eligibleIDs):
                        endIndex = len(eligibleIDs)
                    currentIndex = startIndex
                    idStr = ""
                    for i in range(startIndex, endIndex):
                        idStr = idStr + "<@" + str(eligibleIDs[i]) + ">\n"
                    footerStr = ""
                    if len(eligibleIDs) == 0:
                        footerStr = footerStr + "Showing eligible participants 0-0 out of 0"
                    else:
                        footerStr = footerStr + "Showing eligible participants " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleIDs))

                elif reaction == '➡️':
                    startIndex = currentIndex + 20
                    endIndex = startIndex + 20
                    if endIndex > len(eligibleIDs):
                        endIndex = len(eligibleIDs)
                    startIndex = endIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    currentIndex = startIndex
                    idStr = ""
                    for i in range(startIndex, endIndex):
                        idStr = idStr + "<@" + str(eligibleIDs[i]) + ">\n"
                    footerStr = ""
                    if len(eligibleIDs) == 0:
                        footerStr = footerStr + "Showing eligible participants 0-0 out of 0"
                    else:
                        footerStr = footerStr + "Showing eligible participants " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleIDs))
                
                embedVar = discord.Embed(title="Eligibility Editor", description=optionStr)
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)

            elif reaction == '✅':
                embedVar = discord.Embed(title="Eligibility Editor", description=optionStr, color=discord.Color.green())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                confirmed = True
            elif reaction == '❌':
                embedVar = discord.Embed(title="Eligibility Editor", description=optionStr, color=discord.Color.red())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                return (oldParticipantList, oldEligibilityList)
            else:
                embedVar = discord.Embed(title="Eligibility Editor", description=optionStr, color=discord.Color.blue())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)

                if reaction == '🔍':
                    id = await searchEligible(ctx, eligibilityList)
                elif reaction == '➕':
                    eligibilityList = await addEligibleParticipant(ctx, eligibilityList)
                elif reaction == '➖':
                    infoTuple = await deleteEligibleParticipant(ctx, participantList, eligibilityList)
                    participantList = infoTuple[0]
                    eligibilityList = infoTuple[1]
                elif reaction == '🏷️':
                    infoTuple = await editEligibleRoles(ctx, participantList, eligibilityList)
                    participantList = infoTuple[0]
                    eligibilityList = infoTuple[1]
                elif reaction == '🚫':
                    eligibilityList = await removeRestriction(ctx, typeOfBrawl, eligibilityList)
                    if eligibilityList == None:
                        return (participantList, eligibilityList)

                idStr = ""
                currentIndex = 0
                startIndex = currentIndex
                endIndex = currentIndex + 20
                if endIndex > len(eligibleIDs):
                    endIndex = len(eligibleIDs)
                for i in range(startIndex, endIndex):
                    idStr = idStr + str(i + 1) + ". <@" + str(eligibleIDs[i]) + ">\n"

                footerStr = ""
                if len(eligibleIDs) == 0:
                    footerStr = footerStr + "Showing eligible participants 0-0 out of 0"
                else:
                    footerStr = footerStr + "Showing eligible participants " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleIDs))

                embedVar.set_footer(text=footerStr)

                message = await ctx.channel.send(embed=embedVar)

        except asyncio.TimeoutError:
            return (-1, -1)

    return (participantList, eligibilityList)

##############################################################################################################################################

async def searchEligible(ctx, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Eligible Participant Search", description="Please input the id or @ of the participant you would like to search for."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content.replace('<', '').replace('@', '').replace('!', '').replace('>', '')
        try:
            id = int(search)
        except:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + message.content + " could not be found."))
            return 0
        if id in eligibilityList[0][0]:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + message.content + " is eligible."))
    except asyncio.TimeoutError:
        return 0

    return id

##############################################################################################################################################

async def editEligibleRoles(ctx, participantList, eligibilityList):

    oldParticipantList = participantList
    oldEligibilityList = eligibilityList
    eligibleRoles = eligibilityList[0][1]

    optionStr = str("React with what you want to change:\n" +
                    "⬅️ : show the previous 20 eligible roles\n" +
                    "➡️ : show the next 20 eligible roles\n" +
                    "🔍 : search for an eligible roles\n" +
                    "➕ : add eligible role(s)\n" +
                    "➖ : remove eligible role(s)\n" +
                    "✅ : save changes\n" +
                    "❌ : delete changes")

    roleStr = ""
    currentIndex = 0
    startIndex = currentIndex
    endIndex = currentIndex + 20
    if endIndex > len(eligibleRoles):
        endIndex = len(eligibleRoles)
    for i in range(startIndex, endIndex):
        roleStr = roleStr + str(eligibleRoles[i]) + "\n"

    footerStr = ""
    if len(eligibleRoles) == 0:
        footerStr = footerStr + "Showing eligible roles 0-0 out of 0"
    else:
        footerStr = footerStr + "Showing eligible roles " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleRoles))

    embedVar = discord.Embed(title="Eligible Role Editor", description=optionStr + "\n\n" + roleStr)
    embedVar.set_footer(text=footerStr)
    message = await ctx.channel.send(embed=embedVar)

    def check(react, user):
            return react.message == message and user == ctx.author and (react.emoji == '⬅️' or react.emoji == '➡️' or react.emoji == '🔍' or react.emoji == '➖' or react.emoji == '➕' or react.emoji == '✅' or react.emoji == '❌')
        
    confirmed = False
    while not confirmed:

        eligibleRoles = eligibilityList[1]

        await message.add_reaction('⬅️')
        await message.add_reaction('➡️')
        await message.add_reaction('🔍')
        await message.add_reaction('➕')
        await message.add_reaction('➖')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '⬅️' or reaction == '➡️':
                if reaction == '⬅️':
                    startIndex = currentIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    endIndex = startIndex + 20
                    if endIndex > len(eligibleRoles):
                        endIndex = len(eligibleRoles)
                    currentIndex = startIndex
                    roleStr = ""
                    for i in range(startIndex, endIndex):
                        roleStr = roleStr + str(eligibleRoles[i]) + "\n"
                    footerStr = ""
                    if len(eligibleRoles) == 0:
                        footerStr = footerStr + "Showing eligible roles 0-0 out of 0"
                    else:
                        footerStr = footerStr + "Showing eligible roles " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleRoles))
                elif reaction == '➡️':
                    startIndex = currentIndex + 20
                    endIndex = startIndex + 20
                    if endIndex > len(eligibleRoles):
                        endIndex = len(eligibleRoles)
                    startIndex = endIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    currentIndex = startIndex
                    roleStr = ""
                    for i in range(startIndex, endIndex):
                        roleStr = roleStr + str(eligibleRoles[i]) + "\n"
                    footerStr = ""
                    if len(eligibleRoles) == 0:
                        footerStr = footerStr + "Showing eligible roles 0-0 out of 0"
                    else:
                        footerStr = footerStr + "Showing eligible roles " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleRoles))
                
                embedVar = discord.Embed(title="Eligible Role Editor", description=optionStr + "\n\n" + roleStr)
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)

            elif reaction == '✅':
                embedVar = discord.Embed(title="Eligible Role Editor", description=optionStr, color=discord.Color.green())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                confirmed = True
            elif reaction == '❌':
                embedVar = discord.Embed(title="Eligible Role Editor", description=optionStr, color=discord.Color.red())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                return (oldParticipantList, oldEligibilityList)
            else:
                embedVar = discord.Embed(title="Eligible Role Editor", description=optionStr, color=discord.Color.blue())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)

                if reaction == '🔍':
                    await searchEligibleRoles(ctx, eligibilityList)
                elif reaction == '➕':
                    eligibilityList = await addEligibleRole(ctx, eligibilityList)
                elif reaction == '➖':
                    infoTuple = await deleteEligibleRole(ctx, participantList, eligibilityList)
                    participantList = infoTuple[0]
                    eligibilityList = infoTuple[1]

                roleStr = ""
                currentIndex = 0
                startIndex = currentIndex
                endIndex = currentIndex + 20
                if endIndex > len(eligibleRoles):
                    endIndex = len(eligibleRoles)
                for i in range(startIndex, endIndex):
                    roleStr = roleStr + str(eligibleRoles[i]) + "\n"

                footerStr = ""
                if len(eligibleRoles) == 0:
                    footerStr = footerStr + "Showing eligible roles 0-0 out of 0"
                else:
                    footerStr = footerStr + "Showing eligible roles " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleRoles))

                embedVar = discord.Embed(title="Eligible Role Editor", description=optionStr + "\n\n" + roleStr)
                embedVar.set_footer(text=footerStr)
                message = await ctx.channel.send(embed=embedVar)

        except asyncio.TimeoutError:
            return (oldParticipantList, oldEligibilityList)

    return (participantList, eligibilityList)

##############################################################################################################################################

async def searchEligibleRole(ctx, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Eligible Role Search", description="Please input the role you would like to search for."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content

        if search in eligibilityList[0][1]:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + search + " is an eligible role."))
        else:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + search + " is not an eligible role."))
    except asyncio.TimeoutError:
        pass

##############################################################################################################################################

async def addEligibleRole(ctx, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Add New Eligible Role", description="Please input the name of the role you would like to add."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content.strip()

        try:
            if search not in eligibilityList[0][1]:
                eligibilityList[0][1].append(search)
                await ctx.channel.send(embed=discord.Embed(description="Added: " + message.content))
            else:
                await ctx.channel.send(embed=discord.Embed(description=message.content + " is already an eligible role."))
        except:
            await ctx.channel.send(embed=discord.Embed(description="Failed to add: " + message.content))

    except:
        return eligibilityList

    return eligibilityList

##############################################################################################################################################

async def deleteEligibleRole(ctx, participantList, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Remove Eligible Role", description="Please input the name of the role you would like to remove.\nThis will remove the participant from the participant list as well if they are not in the eligible participant list."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content

        try:
            eligibilityList[1].remove(search)
        except:
            await ctx.channel.send(embed=discord.Embed(description="Could not find " + message.content + " in eligible roles."))
            return (participantList, eligibilityList)

        for participant in participantList:
            user = globalValues.bot.get_user(participant[0])
            hasRole = False
            hasRole = False
            for role in eligibilityList[1]:
                for userRole in ctx.author.roles:
                    if role == userRole.name:
                        hasRole = True
                        break
            if participant[0] not in eligibilityList[0][0] and not hasRole:
                participantList.remove(participant)
                break

        await ctx.channel.send(embed=discord.Embed(description="Removed: " + message.content))

    except asyncio.TimeoutError:
        return None

    return (participantList, eligibilityList)

##############################################################################################################################################

async def editEligibleSeries(ctx, eligibilityList):

    oldEligibilityList = eligibilityList
    eligibleSeries = eligibilityList[1]

    optionStr = str("React with what you want to change:\n" +
                    "⬅️ : show the previous 20 eligible series\n" +
                    "➡️ : show the next 20 eligible series\n" +
                    "🔍 : search for an eligible series\n" +
                    "➕ : add eligible series\n" +
                    "➖ : remove eligible series\n" +
                    "✅ : save changes\n" +
                    "❌ : delete changes")

    seriesStr = ""
    currentIndex = 0
    startIndex = currentIndex
    endIndex = currentIndex + 20
    if endIndex > len(eligibleSeries):
        endIndex = len(eligibleSeries)
    for i in range(startIndex, endIndex):
        seriesStr = seriesStr + str(eligibleSeries[i]) + "\n"

    footerStr = ""
    if len(eligibleSeries) == 0:
        footerStr = footerStr + "Showing eligible series 0-0 out of 0"
    else:
        footerStr = footerStr + "Showing eligible series " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleSeries))

    embedVar = discord.Embed(title="Eligible Series Editor", description=optionStr + "\n\n" + seriesStr)
    embedVar.set_footer(text=footerStr)
    message = await ctx.channel.send(embed=embedVar)

    def check(react, user):
            return react.message == message and user == ctx.author and (react.emoji == '⬅️' or react.emoji == '➡️' or react.emoji == '🔍' or react.emoji == '➖' or react.emoji == '➕' or react.emoji == '✅' or react.emoji == '❌')
        
    confirmed = False
    while not confirmed:

        eligibleSeries = eligibilityList[1]

        await message.add_reaction('⬅️')
        await message.add_reaction('➡️')
        await message.add_reaction('🔍')
        await message.add_reaction('➕')
        await message.add_reaction('➖')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
            reaction = reaction[0].emoji

            if reaction == '⬅️' or reaction == '➡️':
                if reaction == '⬅️':
                    startIndex = currentIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    endIndex = startIndex + 20
                    if endIndex > len(eligibleSeries):
                        endIndex = len(eligibleSeries)
                    currentIndex = startIndex
                    seriesStr = ""
                    for i in range(startIndex, endIndex):
                        seriesStr = seriesStr + str(eligibleSeries[i]) + "\n"
                    footerStr = ""
                    if len(eligibleSeries) == 0:
                        footerStr = footerStr + "Showing eligible series 0-0 out of 0"
                    else:
                        footerStr = footerStr + "Showing eligible series " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleSeries))
                elif reaction == '➡️':
                    startIndex = currentIndex + 20
                    endIndex = startIndex + 20
                    if endIndex > len(eligibleSeries):
                        endIndex = len(eligibleSeries)
                    startIndex = endIndex - 20
                    if startIndex < 0:
                        startIndex = 0
                    currentIndex = startIndex
                    seriesStr = ""
                    for i in range(startIndex, endIndex):
                        seriesStr = seriesStr + str(eligibleSeries[i]) + "\n"
                    footerStr = ""
                    if len(eligibleSeries) == 0:
                        footerStr = footerStr + "Showing eligible series 0-0 out of 0"
                    else:
                        footerStr = footerStr + "Showing eligible series " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleSeries))
                
                embedVar = discord.Embed(title="Eligible Series Editor", description=optionStr + "\n\n" + seriesStr)
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)

            elif reaction == '✅':
                embedVar = discord.Embed(title="Eligible Series Editor", description=optionStr, color=discord.Color.green())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                confirmed = True
            elif reaction == '❌':
                embedVar = discord.Embed(title="Eligible Series Editor", description=optionStr, color=discord.Color.red())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)
                return oldEligibilityList
            else:
                embedVar = discord.Embed(title="Eligible Series Editor", description=optionStr, color=discord.Color.blue())
                embedVar.set_footer(text=footerStr)
                await message.edit(embed=embedVar)

                if reaction == '🔍':
                    await searchEligibleSeries(ctx, eligibilityList)
                elif reaction == '➕':
                    eligibilityList = await addEligibleSeries(ctx, eligibilityList)
                elif reaction == '➖':
                    eligibilityList = await deleteEligibleSeries(ctx, eligibilityList)

                seriesStr = ""
                currentIndex = 0
                startIndex = currentIndex
                endIndex = currentIndex + 20
                if endIndex > len(eligibleSeries):
                    endIndex = len(eligibleSeries)
                for i in range(startIndex, endIndex):
                    seriesStr = seriesStr + str(eligibleSeries[i]) + "\n"

                footerStr = ""
                if len(eligibleSeries) == 0:
                    footerStr = footerStr + "Showing eligible series 0-0 out of 0"
                else:
                    footerStr = footerStr + "Showing eligible series " + str(startIndex + 1) + "-" + str(endIndex) + " out of " + str(len(eligibleSeries))

                embedVar = discord.Embed(title="Eligible Series Editor", description=optionStr + "\n\n" + seriesStr)
                embedVar.set_footer(text=footerStr)
                message = await ctx.channel.send(embed=embedVar)

        except asyncio.TimeoutError:
            return oldEligibilityList

    return eligibilityList

##############################################################################################################################################

async def addEligibleParticipant(ctx, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Add New Eligible Participant", description="Please input the id or @ of the participant you would like to add."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content
        search = search.replace('<', '').replace('@', '').replace('!', '').replace('>', '')

        try:
            search = int(search)
            if search not in eligibilityList[0][0]:
                eligibilityList[0][0].append(search)
                await ctx.channel.send(embed=discord.Embed(description="Added: " + message.content))
            else:
                await ctx.channel.send(embed=discord.Embed(description=message.content + " is already in the eligibility list."))
        except:
            await ctx.channel.send(embed=discord.Embed(description="Failed to add: " + message.content))

    except:
        return eligibilityList

    return eligibilityList

##############################################################################################################################################

async def deleteEligibleParticipant(ctx, participantList, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Remove Eligible Participant", description="Please input the id or @ of the participant you would like to remove.\nThis will remove the participant from the participant list as well if they don't have an eligible role."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content.replace('<', '').replace('@', '').replace('!', '').replace('>', '')

        try:
            search = int(search)
        except:
            await ctx.channel.send(embed=discord.Embed(description="Failed to remove " + message.content))
            return (participantList, eligibilityList)
        try:
            eligibilityList[0][0].remove(search)
        except:
            await ctx.channel.send(embed=discord.Embed(description="Could not find " + message.content + " in eligibility list."))
            return (participantList, eligibilityList)

        for participant in participantList:
            user = globalValues.bot.get_user(participant[0])
            hasRole = False
            hasRole = False
            for role in eligibilityList[0][1]:
                for userRole in ctx.author.roles:
                    if role == userRole.name:
                        hasRole = True
                        break
            if participant[0] == search and not hasRole:
                participantList.remove(participant)
                break

        await ctx.channel.send(embed=discord.Embed(description="Removed: " + message.content))

    except asyncio.TimeoutError:
        return None

    return (participantList, eligibilityList)

##############################################################################################################################################

async def removeRestriction(ctx, typeOfBrawl, eligibilityList):

    message = await ctx.channel.send(embed=discord.Embed(title="Confirm Participant Restriction Removal", description="Removing the restriction opens the " + typeOfBrawl + " to anyone and deletes the participant eligibility list."))
    await message.add_reaction('✅')
    await message.add_reaction('❌')

    def restrictedCheck(react, user):
        return react.message == message and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=restrictedCheck)
        reaction = reaction[0].emoji

        if reaction == '✅':
            await message.edit(embed=discord.Embed(title="Confirm Participant Restriction Removal", description="Removing the restriction opens the " + typeOfBrawl + " to anyone and deletes the participant eligibility list.", color=discord.Color.green()))
            eligibilityList[0] = None
            return eligibilityList

        else:
            raise asyncio.TimeoutError

    except asyncio.TimeoutError:
        await message.edit(embed=discord.Embed(title="Confirm Participant Restriction Removal", description="Removing the restriction opens the " + typeOfBrawl + " to anyone and deletes the participant eligibility list.", color=discord.Color.red()))
        return eligibilityList

##############################################################################################################################################

async def searchEligibleSeries(ctx, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Eligible Series Search", description="Please input the series you would like to search for."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content

        if search in eligibilityList[1]:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + search + " is an eligible series."))
        else:
            await ctx.channel.send(embed=discord.Embed(description="<@" + str(ctx.author.id) + ">, " + search + " is not an eligible series."))
    except asyncio.TimeoutError:
        pass

##############################################################################################################################################

async def addEligibleSeries(ctx, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Add New Eligible Series", description="Please input the name of the series you would like to add. Please make sure it is identical to the series in Karuta."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content

        try:
            if search not in eligibilityList[1]:
                eligibilityList[1].append(search)
                await ctx.channel.send(embed=discord.Embed(description="Added: " + search))
            else:
                await ctx.channel.send(embed=discord.Embed(description=search + " is already an eligible series."))
        except:
            await ctx.channel.send(embed=discord.Embed(description="Failed to add: " + search))

    except:
        return eligibilityList

    return eligibilityList

##############################################################################################################################################

async def deleteEligibleSeries(ctx, eligibilityList):

    await ctx.channel.send(embed=discord.Embed(title="Remove Eligible Series", description="Please input the name of the series you would like to remove.\nThis will not remove any participants from the participant list."))

    def check(m):
        return m.channel == ctx.channel and m.author == ctx.author

    try:
        message = await globalValues.bot.wait_for('message', timeout=60, check=check)

        search = message.content

        try:
            eligibilityList[1].remove(search)
        except:
            await ctx.channel.send(embed=discord.Embed(description="Could not find " + search + " in eligible series."))
            return eligibilityList

        await ctx.channel.send(embed=discord.Embed(description="Removed: " + search))

    except asyncio.TimeoutError:
        return None

    return eligibilityList

##############################################################################################################################################

async def removeCardRestriction(ctx, typeOfBrawl, eligibilityList):

    message = await ctx.channel.send(embed=discord.Embed(title="Confirm Card Restriction Removal", description="Removing the restriction opens the " + typeOfBrawl + " to any card and deletes the series eligibility list."))
    await message.add_reaction('✅')
    await message.add_reaction('❌')

    def restrictedCheck(react, user):
        return react.message == message and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=restrictedCheck)
        reaction = reaction[0].emoji

        if reaction == '✅':
            await message.edit(embed=discord.Embed(title="Confirm Card Restriction Removal", description="Removing the restriction opens the " + typeOfBrawl + " to any card and deletes the series eligibility list.", color=discord.Color.green()))
            eligibilityList[1] = None
            return eligibilityList

        else:
            raise asyncio.TimeoutError

    except asyncio.TimeoutError:
        await message.edit(embed=discord.Embed(title="Confirm Card Restriction Removal", description="Removing the restriction opens the " + typeOfBrawl + " to any card and deletes the series eligibility list.", color=discord.Color.red()))
        return eligibilityList

##############################################################################################################################################

def generateBrawlFiles(ctx, backgroundTuple, fileList):

    fileNames = []

    req = urllib.request.Request(globalValues.backgrounds.get(backgroundTuple[0])[backgroundTuple[1]], headers=globalValues.header)
    backgroundImage = Image.open(urlopen(req))
    backgroundImage.convert('RGBA')
    image = backgroundImage.copy()
    imageFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-0" + ".png"

    fileNames.append(imageFileName)

    fileList.pop(0)

    for i in range(len(fileList)):
        cardImage = Image.open(fileList[i][0])
        cardImage.convert('RGBA')
        image.paste(cardImage, (globalValues.cardCoordinates.get(backgroundTuple[0])[i][0], globalValues.cardCoordinates.get(backgroundTuple[0])[i][1]), cardImage)

    image.save(imageFileName, quality=95)
    globalValues.addFile(str(ctx.guild.id), imageFileName);
    os.remove(imimageFileName);

    return fileNames

##############################################################################################################################################

def generateTournamentMatches(ctx, backgroundTuple, fileList):

    newFileList = []

    for match in fileList:

        fileNames = []
        
        req = urllib.request.Request(globalValues.backgrounds.get(backgroundTuple[0])[backgroundTuple[1]], headers=globalValues.header)
        backgroundImage = Image.open(urlopen(req))
        backgroundImage.convert('RGBA')
        image = backgroundImage.copy()
        imageFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-0" + ".png"

        fileNames.append(imageFileName)
        
        for i in range(match[1:]):
            cardImage = Image.open(match[1:][i][0])
            cardImage.convert('RGBA')
            cardFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-" + str(i + 1) + ".png"
            cardImage.save(cardFileName, quality=95)
            image.paste(cardImage, (globalValues.cardCoordinates.get(backgroundTuple[0])[i][0], globalValues.cardCoordinates.get(backgroundTuple[0])[i][1]), cardImage)
            fileNames.append((cardFileName, pair[i][1]))

        image.save(imageFileName, quality=95)
        newFileList.append(fileNames)

    return newFileList

##############################################################################################################################################

def generateShuffledTournamentMatches(ctx, backgroundTuple, fileList):
    
    cardFileList = []
    for match in fileList:
        for i in range(len(match)):
            if i > 0 and match[i][1] != -1:
                cardFileList.append(match[i])

    host.shuffleCards(cardFileList)

    logNum = math.log(len(cardFileList), 2)

    if not int(logNum) == logNum:
        logNum = int(logNum) + 1
    
    totNum = 2 ** logNum

    i = 1
    while len(cardURLs) < totNum:
        cardURLs.insert(i, (globalValues.passCardURL, -1))
        i += 2

    bracket = generateTournamentBracket(cardFileList)

    pairs = []
    generatePairs(bracket, pairs)

    fileList = []

    for pair in pairs:

        fileNames = []
        
        req = urllib.request.Request(globalValues.backgrounds.get(backgroundTuple[0])[backgroundTuple[1]], headers=globalValues.header)
        backgroundImage = Image.open(urlopen(req))
        backgroundImage.convert('RGBA')
        image = backgroundImage.copy()
        imageFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-0" + ".png"

        fileNames.append(imageFileName)
        
        for i in range(len(pair)):
            cardImage = Image.open(pair[i][0])
            cardImage.convert('RGBA')
            cardFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-" + str(i + 1) + ".png"
            cardImage.save(cardFileName, quality=95)
            image.paste(cardImage, (globalValues.cardCoordinates.get(backgroundTuple[0])[i][0], globalValues.cardCoordinates.get(backgroundTuple[0])[i][1]), cardImage)
            fileNames.append((cardFileName, pair[i][1]))

        image.save(imageFileName, quality=95)
        fileList.append(fileNames)

    return fileList

##############################################################################################################################################

async def chooseNumParticipants(ctx, typeOfBrawl, participantTuple):

    numParticipants = 0

    if typeOfBrawl == "brawl":

        confirmed = False
        while not confirmed:
        
            await ctx.channel.send(embed=discord.Embed(title="Input Number of Participants", description="Please input the maximum number of participants that will compete in the brawl."))

            def numCheck(m):
                return m.channel == ctx.channel and m.content.isdigit()

            invalid = True
            while invalid:
                try:
                    message = await globalValues.bot.wait_for('message', timeout=60, check=numCheck)
                    if not message.content.isdigit():
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number."))
                    elif int(message.content) < 2:
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number greater than or equal to 2."))
                    elif int(message.content) > 2:
                        await tooLarge(ctx)
                    elif int(message.content) < len(participantTuple[0]):
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number greater than or equal to the current number of registered participants."))
                    else:
                        numParticipants = int(message.content)
                        invalid = False
                except asyncio.TimeoutError:
                    return None

            confirmMessage = await ctx.channel.send(embed=discord.Embed(title="Confirm Number of Participants", description="Number of participants: " + str(numParticipants)))
            await confirmMessage.add_reaction('✅')
            await confirmMessage.add_reaction('❌')

            def reactionCheck(react, user):
                return react.message == confirmMessage and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

            try:
                reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=reactionCheck)
                reaction = reaction[0].emoji

                if reaction == '✅':
                    await confirmMessage.edit(embed=discord.Embed(title="Confirm Number of Participants", description="Number of participants: " + str(numParticipants), color=discord.Color.green()))
                    confirmed = True
                else:
                    await confirmMessage.edit(embed=discord.Embed(title="Confirm Number of Participants", description="Number of participants: " + str(numParticipants), color=discord.Color.red()))
            except asycnio.TimeoutError:
                return None

        return numParticipants

    else:

        confirmed = False
        while not confirmed:
        
            await ctx.channel.send(embed=discord.Embed(title="Input Number of Participants", description="Please input the maximum number of participants that will compete in the tournament."))

            def numCheck(m):
                return m.channel == ctx.channel and m.content.isdigit()

            invalid = True
            while invalid:
                try:
                    message = await globalValues.bot.wait_for('message', timeout=60, check=numCheck)
                    if not message.content.isdigit():
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number."))
                    elif int(message.content) < 3:
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number greater than or equal to 3."))
                    elif int(message.content) < len(participantTuple[0]):
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number greater than or equal to the current number of registered participants."))
                    else:
                        numParticipants = int(message.content)
                        invalid = False
                except asyncio.TimeoutError:
                    return None

            confirmMessage = await ctx.channel.send(embed=discord.Embed(title="Confirm Number of Participants", description="Number of participants: " + str(numParticipants)))
            await confirmMessage.add_reaction('✅')
            await confirmMessage.add_reaction('❌')

            def reactionCheck(react, user):
                return react.message == confirmMessage and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

            try:
                reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=reactionCheck)
                reaction = reaction[0].emoji

                if reaction == '✅':
                    await confirmMessage.edit(embed=discord.Embed(title="Confirm Number of Participants", description="Number of participants: " + str(numParticipants), color=discord.Color.green()))
                    confirmed = True
                else:
                    await confirmMessage.edit(embed=discord.Embed(title="Confirm Number of Participants", description="Number of participants: " + str(numParticipants), color=discord.Color.red()))
            except asycnio.TimeoutError:
                return None

        return numParticipants

##############################################################################################################################################

async def error(ctx, code, *args):

    # invalid name
    if code == 5:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " does not exist."))

    # currently being edited
    elif code == 1:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is currently being edited and cannot be accessed."))

    # currently live
    elif code == 3:
        name = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + name + " is currently live and cannot be edited."))

    # invalid participant search
    elif code == 4:
        search = args[0]
        await ctx.channel.send(embed=discord.Embed(title="", description="<@" + str(ctx.author.id) + ">, " + search + " could not be found."))