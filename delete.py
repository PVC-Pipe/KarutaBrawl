# delete.py
# By: PVCPipe01
# contains the delete command

import discord
import os
from discord.ext import commands
import asyncio
import pickle

import globalValues
import host

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX
WINNER_INDEX = globalValues.WINNER_INDEX

async def delete(ctx, arg):

    name = arg
    typeOfBrawl = ""
    accessState = -1
    errorCode = -1

    info = None

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        if not globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name):
            errorCode = 5
            
        elif globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] == 1:
            errorCode = 1

        else:
            info = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)
            typeOfBrawl = info[TYPE_INDEX]
            accessState = info[ACCESS_INDEX]
            globalValues.savedCompetitions[str(ctx.guild.id)][name][ACCESS_INDEX] = 1

    if errorCode != -1:
        await error(ctx, errorCode, name)
        return

    if accessState != 4:
        participantTuple = info[PARTICIPANT_INDEX]
        timeList = info[TIME_INDEX]
        backgroundTuple = info[BACKGROUND_INDEX]
        reactionList = info[REACTION_INDEX]
        fileList = info[FILE_INDEX]

        if typeOfBrawl == "brawl" and accessState == 0:
            await deleteOpenBrawl(ctx, name, participantTuple, timeList, backgroundTuple, reactionList)
        
        elif typeOfBrawl == "brawl" and accessState == 2:
            await deleteClosedBrawl(ctx, name, timeList, reactionList, fileList)
       
        elif typeOfBrawl == "tournament" and accessState == 0:
            await deleteOpenTournament(ctx, name, participantTuple, timeList, backgroundTuple, reactionList)
        
        elif typeOfBrawl == "tournament" and accessState == 2:
            await deleteClosedTournament(ctx, name, timeList, reactionList, fileList)

    else:
        winnerList = info[WINNER_INDEX]

        if typeOfBrawl == "brawl":
            await deleteCompletedBrawl(ctx, name, winnerList)

        elif typeOfBrawl == "tournament":
            await deleteCompletedTournament(ctx, name, winnerList)

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

async def deleteOpenBrawl(ctx, name, participantTuple, timeList, backgroundTuple, reactionList):

    restricted = participantTuple[1]
    if restricted != None:
        restricted = restricted[1]

    restrictedStr = ""
    if restricted == None:
        restrictedStr = "Not Restricted"
    elif restricted == []:
        restrictedStr = "No eligible roles"
    else:
        restrictedStr = "List of eligible roles:\n"
        for role in restricted:
            restrictedStr = restrictedStr + role + "\n"
    
    timeStr = getTimeStr(timeList)
    embedVar = discord.Embed(title=name, description=restrictedStr + "\nMax number of participants: " + str(participantTuple[2]) + "\nDuration: " + timeStr)
    imageFileName = host.generateSample(ctx, backgroundTuple)
    globalValues.getFile(str(ctx.guild.id), imageFileName)
    imageFile = discord.File(imageFileName)
    embedVar.set_image(url="attachment://" + imageFileName)
    preview = await ctx.channel.send(file=imageFile, embed=embedVar)
    os.remove(imageFileName)
    for reaction in reactionList:
        await preview.add_reaction(reaction)
    
    deleteMessage = await ctx.channel.send(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?"))
    await deleteMessage.add_reaction('✅')
    await deleteMessage.add_reaction('❌')

    def deleteCheck(react, user):
        return react.message.channel == ctx.channel and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=deleteCheck)
        reaction = reaction[0].emoji
        if reaction == '✅':
            await deleteMessage.edit(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?", color=discord.Color.green()))

            async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
                globalValues.savedCompetitions.get(str(ctx.guild.id)).pop(name)
                await globalValues.store()

            for id, card in participantTuple[0].items():
                globalValues.removeFile(str(ctx.guild.id), card[0])

            await ctx.channel.send(embed=discord.Embed(title="", description="Brawl successfully deleted.", color=discord.Color.green()))
        else:
            raise asyncio.TimeoutError
    except asyncio.TimeoutError:
        await deleteMessage.edit(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?", color=discord.Color.red()))

        await ctx.channel.send(embed=discord.Embed(title="", description="Deletion cancelled.", color=discord.Color.red()))

    globalValues.removeFile(str(ctx.guild.id), imageFileName)

##############################################################################################################################################

async def deleteOpenTournament(ctx, name, participantTuple, timeList, backgroundTuple, reactionList):

    restricted = participantTuple[1]
    if restricted != None:
        restricted = restricted[1]

    restrictedStr = ""
    if restricted == None:
        restrictedStr = "Not Restricted"
    elif restricted == []:
        restrictedStr = "No eligible roles"
    else:
        restrictedStr = "List of eligible roles:\n"
        for role in restricted:
            restrictedStr = restrictedStr + role + "\n"

    durationStr = getTimeStr(timeList[0])
    tiebreakerStr = getTimeStr(timeList[1])
    delayStr = getTimeStr(timeList[2])
                
    embedVar = discord.Embed(title=name, description=restrictedStr + "\nMax number of participants: " + str(participantTuple[2]) + "\nMatch duration: " + durationStr + "\nTiebreaker match duration: " + tiebreakerStr + "\nDelay between matches: " + delayStr)
    imageFileName = host.generateSample(ctx, backgroundTuple)
    globalValues.getFile(str(ctx.guild.id), imageFileName)
    imageFile = discord.File(imageFileName)
    embedVar.set_image(url="attachment://" + imageFileName)
    preview = await ctx.channel.send(file=imageFile, embed=embedVar)
    os.remove(imageFileName)
    for reaction in reactionList:
        await preview.add_reaction(reaction)
    
    deleteMessage = await ctx.channel.send(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?"))
    await deleteMessage.add_reaction('✅')
    await deleteMessage.add_reaction('❌')

    def deleteCheck(react, user):
        return react.message.channel == ctx.channel and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=deleteCheck)
        reaction = reaction[0].emoji
        if reaction == '✅':
            await deleteMessage.edit(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?", color=discord.Color.green()))

            async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
                globalValues.savedCompetitions.get(str(ctx.guild.id)).pop(name)
                await globalValues.store()

            for id, card in participantTuple[0].items():
                globalValues.removeFile(str(ctx.guild.id), card[0])

            await ctx.channel.send(embed=discord.Embed(title="", description="Tournament successfully deleted.", color=discord.Color.green()))
        else:
            raise asyncio.TimeoutError
    except asyncio.TimeoutError:
        await deleteMessage.edit(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?", color=discord.Color.red()))

        await ctx.channel.send(embed=discord.Embed(title="", description="Deletion cancelled.", color=discord.Color.red()))

    globalValues.removeFile(str(ctx.guild.id), imageFileName)

##############################################################################################################################################

async def deleteClosedBrawl(ctx, name, timeList, reactionList, fileList):

    timeStr = getTimeStr(timeList)
    embedVar = discord.Embed(title=name, description="Duration: " + timeStr)
    globalValues.getFile(str(ctx.guild.id), fileList[0])
    imageFile = discord.File(fileList[0])
    embedVar.set_image(url="attachment://" + fileList[0])
    preview = await ctx.channel.send(file=imageFile, embed=embedVar)
    os.remove(fileList[0])
    for reaction in reactionList:
        await preview.add_reaction(reaction)
    
    deleteMessage = await ctx.channel.send(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?"))
    await deleteMessage.add_reaction('✅')
    await deleteMessage.add_reaction('❌')

    def deleteCheck(react, user):
        return react.message.channel == ctx.channel and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=deleteCheck)
        reaction = reaction[0].emoji
        if reaction == '✅':
            await deleteMessage.edit(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?", color=discord.Color.green()))

            async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
                globalValues.savedCompetitions.get(str(ctx.guild.id)).pop(name)
                await globalValues.store()

            for i in range(len(fileList)):
                if i == 0:
                    globalValues.removeFile(str(ctx.guild.id), fileList[i])
                else:
                    globalValues.removeFile(str(ctx.guild.id), fileList[i][0])

            await ctx.channel.send(embed=discord.Embed(title="", description="Brawl successfully deleted.", color=discord.Color.green()))
        else:
            raise asyncio.TimeoutError
    except asyncio.TimeoutError:
        await deleteMessage.edit(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?", color=discord.Color.red()))

        await ctx.channel.send(embed=discord.Embed(title="", description="Deletion cancelled.", color=discord.Color.red()))

##############################################################################################################################################

async def deleteClosedTournament(ctx, name, timeList, reactionList, fileList):

    durationStr = getTimeStr(timeList[0])
    tiebreakerStr = getTimeStr(timeList[1])
    delayStr = getTimeStr(timeList[2])
                
    embedVar = discord.Embed(title=name, description="Round duration: " + durationStr + "\n" +
                                                     "Tiebreaker duration: " + tiebreakerStr + "\n" +
                                                     "Delay duration: " + delayStr)

    await ctx.channel.send(embed=embedVar)

    await ctx.channel.send(embed=discord.Embed(title="Preview of First Round Matches"))

    for match in fileList:
        embedVar = discord.Embed(title="", description="")
        globalValues.getFile(str(ctx.guild.id), match[0])
        compImage = discord.File(match[0])
        embedVar.set_image(url="attachment://" + match[0])
        message = await ctx.channel.send(file=compImage, embed=embedVar)
        os.remove(match[0])
        for reaction in reactionList:
            await message.add_reaction(reaction)

    deleteMessage = await ctx.channel.send(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?"))
    await deleteMessage.add_reaction('✅')
    await deleteMessage.add_reaction('❌')

    def deleteCheck(react, user):
        return react.message.channel == ctx.channel and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=deleteCheck)
        reaction = reaction[0].emoji
        if reaction == '✅':
            await deleteMessage.edit(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?", color=discord.Color.green()))

            async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
                globalValues.savedCompetitions.get(str(ctx.guild.id)).pop(name)
                await globalValues.store()

            for i in range(len(fileList)):
                if i == 0:
                    globalValues.removeFile(str(ctx.guild.id), fileList[i])
                else:
                    globalValues.removeFile(str(ctx.guild.id), fileList[i][0])

            await ctx.channel.send(embed=discord.Embed(title="", description="Tournament successfully deleted.", color=discord.Color.green()))
        else:
            raise asyncio.TimeoutError
    except asyncio.TimeoutError:
        await deleteMessage.edit(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?", color=discord.Color.red()))

        await ctx.channel.send(embed=discord.Embed(title="", description="Deletion cancelled.", color=discord.Color.red()))

##############################################################################################################################################

async def deleteCompletedBrawl(ctx, name, winnerList):

    firstPlaceList = winnerList[0]
    secondPlaceList = winnerList[1]
    thirdPlaceList = winnerList[2]

    firstPlaceList = winnerList[0]
    secondPlaceList = winnerList[1]
    thirdPlaceList = winnerList[2]

    if len(secondPlaceList) == 0 and len(thirdPlaceList) == 0:
        if len(firstPlaceList) == 1:
            embedVar = firstPlaceList[0][0]
            globalValues.getFile(str(ctx.guild.id), firstPlaceList[0][1])
            imageFile = discord.File(firstPlaceList[0][1])
            embedVar.set_image(url="attachment://" + firstPlaceList[0][1])
            await ctx.channel.send(file=imageFile, embed=embedVar)
            os.remove(firstPlaceList[0][1])
        else:
            await ctx.channel.send(embed=discord.Embed(title="Winners of " + name + "!", color=discord.Color.gold()))
            for card in firstPlaceList:
                embedVar = card[0]
                globalValues.getFile(str(ctx.guild.id), card[1])
                imageFile = discord.File(card[1])
                embedVar.set_image(url="attachment://" + card[1])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(card[1])

    else:
        if len(firstPlaceList) == 1:
            embedVar = firstPlaceList[0][0]
            globalValues.get(firstPlaceList[0][1])
            imageFile = discord.File(firstPlaceList[0][1])
            embedVar.set_image(url="attachment://" + firstPlaceList[0][1])
            await ctx.channel.send(file=imageFile, embed=embedVar)
            os.remove(firstPlaceList[0][1])
        else:
            await ctx.channel.send(embed=discord.Embed(title="1st Place Winners of " + name + "!", color=discord.Color.gold()))
            for card in firstPlaceList:
                embedVar = card[0]
                globalValues.getFile(str(ctx.guild.id), card[1])
                imageFile = discord.File(card[1])
                embedVar.set_image(url="attachment://" + card[1])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(card[1])

        if len(secondPlaceList) == 1:
            embedVar = secondPlaceList[0][0]
            globalValues.getFile(str(ctx.guild.id), secondPlaceList[0][1])
            imageFile = discord.File(secondPlaceList[0][1])
            embedVar.set_image(url="attachment://" + secondPlaceList[0][1])
            await ctx.channel.send(file=imageFile, embed=embedVar)
            os.remove(secondPlaceList[0][1])
        elif len(secondPlaceList) > 0:
            await ctx.channel.send(embed=discord.Embed(title="2nd Place Winners of " + name + "!", color=0xAAA9AD))
            for card in secondPlaceList:
                embedVar = card[0]
                globalValues.getFile(str(ctx.guild.id), card[1])
                imageFile = discord.File(card[1])
                embedVar.set_image(url="attachment://" + card[1])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(card[1])

        if len(thirdPlaceList) == 1:
            embedVar = thirdPlaceList[0][0]
            globalValues.getFile(str(ctx.guild.id), thirdPlaceList[0][1])
            imageFile = discord.File(thirdPlaceList[0][1])
            embedVar.set_image(url="attachment://" + thirdPlaceList[0][1])
            await ctx.channel.send(file=imageFile, embed=embedVar)
            os.remove(thirdPlaceList[0][1])
        elif len(thirdPlaceList) > 0:
            await ctx.channel.send(embed=discord.Embed(title="3rd Place Winners of " + name + "!", color=0xCD7F32))
            for card in thirdPlaceList:
                embedVar = card[0]
                globalValues.get(card[1])
                imageFile = discord.File(card[1])
                embedVar.set_image(url="attachment://" + card[1])
                await ctx.channel.send(file=imageFile, embed=embedVar)
                os.remove(card[1])

    deleteMessage = await ctx.channel.send(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?"))
    await deleteMessage.add_reaction('✅')
    await deleteMessage.add_reaction('❌')

    def deleteCheck(react, user):
        return react.message.channel == ctx.channel and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=deleteCheck)
        reaction = reaction[0].emoji
        if reaction == '✅':
            await deleteMessage.edit(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?", color=discord.Color.green()))

            async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
                globalValues.savedCompetitions.get(str(ctx.guild.id)).pop(name)
                await globalValues.store()

            for cardList in winnerList:
                for card in cardList:
                    try:
                        globalValues.removeFile(str(ctx.guild.id), card[1])
                    except:
                        pass

            await ctx.channel.send(embed=discord.Embed(title="", description="Brawl successfully deleted.", color=discord.Color.green()))
        else:
            raise asyncio.TimeoutError
    except asyncio.TimeoutError:
        await deleteMessage.edit(embed=discord.Embed(title="Delete Brawl", description="Delete the above brawl?", color=discord.Color.red()))

        await ctx.channel.send(embed=discord.Embed(title="", description="Deletion cancelled.", color=discord.Color.red()))


##############################################################################################################################################

async def deleteCompletedTournament(ctx, name, winnerList):

    for card in winnerList:
        embed = card[0]
        globalValues.getFile(str(ctx.guild.id), card[1])
        imageFile = discord.File(card[1])
        embed.set_image(url="attachment://" + card[1])
        await ctx.channel.send(file=imageFile, embed=embed)
        os.remove(card[1])

    deleteMessage = await ctx.channel.send(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?"))
    await deleteMessage.add_reaction('✅')
    await deleteMessage.add_reaction('❌')

    def deleteCheck(react, user):
        return react.message.channel == ctx.channel and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=deleteCheck)
        reaction = reaction[0].emoji
        if reaction == '✅':
            await deleteMessage.edit(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?", color=discord.Color.green()))

            async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
                globalValues.savedCompetitions.get(str(ctx.guild.id)).pop(name)
                await globalValues.store()

            for card in winnerList:
                try:
                    globalValues.removeFile(str(ctx.guild.id), card[1])
                except:
                    pass

            await ctx.channel.send(embed=discord.Embed(title="", description="Tournament successfully deleted.", color=discord.Color.green()))
        else:
            raise asyncio.TimeoutError
    except asyncio.TimeoutError:
        await deleteMessage.edit(embed=discord.Embed(title="Delete Tournament", description="Delete the above tournament?", color=discord.Color.red()))

        await ctx.channel.send(embed=discord.Embed(title="", description="Deletion cancelled.", color=discord.Color.red()))

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