# host.py
# By: PVCPipe01
# contains the host command

import discord
import os
from discord.ext import commands

import random
import asyncio
import aiorwlock
import urllib.request
from urllib.request import urlopen
from PIL import Image

import pickle
import time
import math

import globalValues

TYPE_INDEX = globalValues.TYPE_INDEX
ACCESS_INDEX = globalValues.ACCESS_INDEX
PARTICIPANT_INDEX = globalValues.PARTICIPANT_INDEX
TIME_INDEX = globalValues.TIME_INDEX
BACKGROUND_INDEX = globalValues.BACKGROUND_INDEX
REACTION_INDEX = globalValues.REACTION_INDEX
FILE_INDEX = globalValues.FILE_INDEX

# 0 : open
# 1 : editing
# 2 : close
# 3 : live
# 4 : completed

##############################################################################################################################################

async def host(ctx, arg):

    if globalValues.savedCompetitions.get(str(ctx.guild.id)) == None:
        globalValues.savedCompetitions[str(ctx.guild.id)] = {}
        globalValues.guildLocks[str(ctx.guild.id)] = aiorwlock.RWLock()

    # two types, brawl and tournament
    typeOfBrawl = ""

    if arg == "brawl":
        typeOfBrawl = "brawl"
    
    elif arg == "tournament":
        typeOfBrawl = "tournament"

    else:
        await invalidArg(ctx)
        return

    info = None

    #brawl actions
    if typeOfBrawl == "brawl":
        info = await createBrawl(ctx)
        if not info:
            await cancel(ctx)
            return

    # tournament actions
    else:
        info = await createTournament(ctx)
        if not info:
            await cancel(ctx)
            return

    await store(ctx, info)

##############################################################################################################################################

async def createBrawl(ctx):

    # choose the name of the competition
    name = await chooseName(ctx, "brawl")
    if not name:
        return None

    restricted = await chooseRestriction(ctx, "brawl")
    if restricted == None:
        return None

    cardRestriction = await chooseCardRestriction(ctx, "tournament")
    if cardRestriction == None:
        return None

    maxParticipants = await chooseNumParticipants(ctx, "brawl")
    if not maxParticipants:
        return None

    timeList = await chooseTime(ctx, "brawl")
    if not timeList:
        return None

    backgroundTuple = await chooseBackground(ctx, maxParticipants)
    if not backgroundTuple:
        return None

    reactionList = await chooseReactions(ctx, maxParticipants)
    if not reactionList:
        return None

    confirm = await finalConfirm(ctx, "brawl", name, restricted, cardRestriction, maxParticipants, timeList, backgroundTuple, reactionList)
    
    return confirm

##############################################################################################################################################

async def createTournament(ctx):

    name = await chooseName(ctx, "tournament")
    if not name:
        return None

    restricted = await chooseRestriction(ctx, "tournament")
    if restricted == None:
        return None

    cardRestriction = await chooseCardRestriction(ctx, "tournament")
    if cardRestriction == None:
        return None

    maxParticipants = await chooseNumParticipants(ctx, "tournament")
    if not maxParticipants:
        return None

    timeList = await chooseTime(ctx, "tournament")
    if not timeList:
        return None

    backgroundTuple = await chooseBackground(ctx, 2)
    if not backgroundTuple:
        return None

    reactionList = await chooseReactions(ctx, 2)
    if not reactionList:
        return None

    confirm = await finalConfirm(ctx, "tournament", name, restricted, cardRestriction, maxParticipants, timeList, backgroundTuple, reactionList)

    return confirm

##############################################################################################################################################

async def chooseName(ctx, typeOfBrawl):
    name = ""
    nameConfirmed = False
    while not nameConfirmed:
        try:
            nameChosen = False

            def nameCheck(m):
                return m.channel == ctx.channel and m.author == ctx.message.author

            namePrompt = await ctx.channel.send(embed=discord.Embed(title="Choose a Name", description="Please input a name for the " + typeOfBrawl + " within the next 60 seconds."))

            while not nameChosen:
                nameMessage = await globalValues.bot.wait_for('message', timeout=60, check=nameCheck)
                name = nameMessage.content

                if name != "":
                    nameChosen = True
                  
                guildBrawls = {}
                
                async with globalValues.guildLocks.get(str(ctx.guild.id)).reader_lock:
                    brawl = globalValues.savedCompetitions.get(str(ctx.guild.id)).get(name)

                    if brawl != None:
                        if brawl[0] == "brawl":
                            await namePrompt.edit(embed=discord.Embed(title="Invalid Name", description="You already have a brawl with that name."))
                            nameChosen = False
                        else:
                            await namePrompt.edit(embed=discord.Embed(title="Invalid Name", description="You already have a tournament with that name."))
                            nameChosen = False
                
            nameConfirmMessage = await ctx.channel.send(embed=discord.Embed(title="Confirm Name", description=name + "\n\nIs this correct? Please react within the next 60 seconds."))

            def nameConfirm(react, user):
                return react.message == nameConfirmMessage and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

            await nameConfirmMessage.add_reaction('✅')
            await nameConfirmMessage.add_reaction('❌')
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=nameConfirm)
            reaction = reaction[0].emoji
            if reaction == '✅':
                await nameConfirmMessage.edit(embed=discord.Embed(title="Confirm Name", description=name + "\n\nIs this correct? Please react within the next 60 seconds.", color=discord.Color.green()))
                nameConfirmed = True
            else:
                await nameConfirmMessage.edit(embed=discord.Embed(title="Confirm Name", description=name + "\n\nIs this correct? Please react within the next 60 seconds.", color=discord.Color.red()))
        except asyncio.TimeoutError:
            return None

    return name

##############################################################################################################################################

async def chooseRestriction(ctx, typeOfBrawl):
    
    typeOfBrawlCap = ""
    if typeOfBrawl == "brawl":
        typeOfBrawlCap = "Brawl"
    else:
        typeOfBrawlCap = "Tournament"

    roleList = []

    restrictMessage = None

    restrictMessage = await ctx.channel.send(embed=discord.Embed(title="Restrict " + typeOfBrawlCap + " Participants", description="Would you like to restrict this " + typeOfBrawl + "'s participants?"))
    await restrictMessage.add_reaction('✅')
    await restrictMessage.add_reaction('❌')

    def check(react, user):
        return react.message == restrictMessage and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
        reaction = reaction[0].emoji

        if reaction == '✅':
            await restrictMessage.edit(embed=discord.Embed(title="Restrict " + typeOfBrawlCap, description="Would you like to restrict this " + typeOfBrawl + "'s participants?", color=discord.Color.green()))

            confirmed = False
            while not confirmed:
                addRoles = True
                while addRoles:
                    rolesMessage = await ctx.channel.send(embed=discord.Embed(title="Restrict to Roles", description="Would you like to restrict this " + typeOfBrawl + " to a certain role? This prompt will repeat until you select no to allow you to input multiple roles."))
                    await rolesMessage.add_reaction('✅')
                    await rolesMessage.add_reaction('❌')

                    def rolesCheck(react, user):
                        return react.message == rolesMessage and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

                    reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=rolesCheck)
                    reaction = reaction[0].emoji

                    if reaction == '✅':
                        await rolesMessage.edit(embed=discord.Embed(title="Restrict to Roles", description="Would you like to restrict this " + typeOfBrawl + " to a certain role? This prompt will repeat until you select no to allow you to input multiple roles.", color=discord.Color.green()))
                        await ctx.channel.send(embed=discord.Embed(description="Please input the role you would like to restrict this " + typeOfBrawl + " to."))

                        def roleListCheck(m):
                            return m.channel == ctx.channel and m.author == ctx.author

                        roleInputMessage = await globalValues.bot.wait_for('message', timeout=60, check=roleListCheck)
                        role = roleInputMessage.content.strip()
                        
                        if role != "":
                            roleList.append(role)
                    else:
                        await rolesMessage.edit(embed=discord.Embed(title="Restrict to Roles", description="Would you like to restrict this " + typeOfBrawl + " to a certain role? This prompt will repeat until you select no to allow you to input multiple roles.", color=discord.Color.red()))
                        addRoles = False

                roleStr = ""
                for role in roleList:
                    roleStr = roleStr + role + "\n"
                rolesConfirm = await ctx.channel.send(embed=discord.Embed(title="Confirm Roles", description="Selecting no will allow you to reselect roles.\nList of roles allowed to participate in this " + typeOfBrawl + ":\n\n" + roleStr))
                await rolesConfirm.add_reaction('✅')
                await rolesConfirm.add_reaction('❌')

                def roleConfirmCheck(react, user):
                    return react.message == rolesConfirm and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

                reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=roleConfirmCheck)
                reaction = reaction[0].emoji

                if reaction == '✅':
                    await rolesConfirm.edit(embed=discord.Embed(title="Confirm Roles", description="Selecting no will allow you to reselect roles.\nList of roles allowed to participate in this " + typeOfBrawl + ":\n\n" + roleStr, color=discord.Color.green()))
                    confirmed = True

                else:
                    await rolesConfirm.edit(embed=discord.Embed(title="Confirm Roles", description="Selecting no will allow you to reselect roles.\nList of roles allowed to participate in this " + typeOfBrawl + ":\n\n" + roleStr, color=discord.Color.red()))
                    roleList = []

        else:
            await restrictMessage.edit(embed=discord.Embed(title="Restrict " + typeOfBrawlCap + " Participants", description="Would you like to restrict this " + typeOfBrawl + "'s participants?", color=discord.Color.red()))
            return False
                        
    except asyncio.TimeoutError:
        return None

    return roleList

##############################################################################################################################################

async def chooseCardRestriction(ctx, typeOfBrawl):

    typeOfBrawlCap = ""
    if typeOfBrawl == "brawl":
        typeOfBrawlCap = "Brawl"
    else:
        typeOfBrawlCap = "Tournament"

    seriesList = []

    restrictMessage = await ctx.channel.send(embed=discord.Embed(title="Restrict " + typeOfBrawlCap + " Cards", description="Would you like to restrict this " + typeOfBrawl + "'s card submissions?"))
    await restrictMessage.add_reaction('✅')
    await restrictMessage.add_reaction('❌')

    def check(react, user):
        return react.message == restrictMessage and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

    try:
        reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=check)
        reaction = reaction[0].emoji

        if reaction == '✅':
            await restrictMessage.edit(embed=discord.Embed(title="Restrict " + typeOfBrawlCap, description="Would you like to restrict this " + typeOfBrawl + "'s card submissions?", color=discord.Color.green()))

            confirmed = False
            while not confirmed:
                addSeries = True
                while addSeries:
                    seriesMessage = await ctx.channel.send(embed=discord.Embed(title="Restrict to Series", description="Would you like to restrict this " + typeOfBrawl + " to a certain anime series? This prompt will repeat until you select no to allow you to input multiple series."))

                    await seriesMessage.add_reaction('✅')
                    await seriesMessage.add_reaction('❌')

                    def seriesCheck(react, user):
                        return react.message == seriesMessage and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

                    reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=seriesCheck)
                    reaction = reaction[0].emoji

                    if reaction == '✅':
                        await seriesMessage.edit(embed=discord.Embed(title="Restrict to Series", description="Would you like to restrict this " + typeOfBrawl + " to a certain anime series? This prompt will repeat until you select no to allow you to input multiple series.", color=discord.Color.green()))
                        await ctx.channel.send(embed=discord.Embed(description="Please input the series you would like to restrict this " + typeOfBrawl + " to."))

                        def seriesListCheck(m):
                            return m.channel == ctx.channel and m.author == ctx.author

                        seriesInputMessage = await globalValues.bot.wait_for('message', timeout=60, check=seriesListCheck)
                        series = seriesInputMessage.content.strip()
                        
                        if series != "":
                            seriesList.append(series)
                    else:
                        await seriesMessage.edit(embed=discord.Embed(title="Restrict to Series", description="Would you like to restrict this " + typeOfBrawl + " to a certain anime series? This prompt will repeat until you select no to allow you to input multiple series.", color=discord.Color.red()))
                        addSeries = False

                seriesStr = ""
                for series in seriesList:
                    seriesStr = seriesStr + series + "\n"
                seriesConfirm = await ctx.channel.send(embed=discord.Embed(title="Confirm Series", description="Selecting no will allow you to reselect series.\nList of series allowed to participate in this " + typeOfBrawl + ":\n\n" + seriesStr))
                await seriesConfirm.add_reaction('✅')
                await seriesConfirm.add_reaction('❌')

                def seriesConfirmCheck(react, user):
                    return react.message == seriesConfirm and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

                reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=seriesConfirmCheck)
                reaction = reaction[0].emoji

                if reaction == '✅':
                    await seriesConfirm.edit(embed=discord.Embed(title="Confirm Series", description="Selecting no will allow you to reselect series.\nList of series allowed to participate in this " + typeOfBrawl + ":\n\n" + seriesStr, color=discord.Color.green()))
                    confirmed = True

                else:
                    await seriesConfirm.edit(embed=discord.Embed(title="Confirm Series", description="Selecting no will allow you to reselect series.\nList of series allowed to participate in this " + typeOfBrawl + ":\n\n" + seriesStr, color=discord.Color.red()))
                    seriesList = []

        else:
            await restrictMessage.edit(embed=discord.Embed(title="Restrict " + typeOfBrawlCap + " Cards", description="Would you like to restrict this " + typeOfBrawl + "'s card submissions?", color=discord.Color.red()))
            return False

    except asyncio.TimeoutError:
        return None

    return seriesList

##############################################################################################################################################

async def chooseNumParticipants(ctx, typeOfBrawl):

    numParticipants = 0

    if typeOfBrawl == "brawl":

        confirmed = False
        while not confirmed:
        
            await ctx.channel.send(embed=discord.Embed(title="Input Number of Participants", description="Please input the maximum number of participants that will compete in the brawl"))

            def numCheck(m):
                return m.channel == ctx.channel and m.content.isdigit()

            invalid = True
            while invalid:
                try:
                    message = await globalValues.bot.wait_for('message', timeout=60, check=numCheck)
                    if not message.content.isdigit():
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number"))
                    elif int(message.content) < 2:
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number greater than or equal to 2"))
                    elif int(message.content) > 2:
                        await tooLarge(ctx)
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
        
            await ctx.channel.send(embed=discord.Embed(title="Input Number of Participants", description="Please input the maximum number of participants that will compete in the tournament"))

            def numCheck(m):
                return m.channel == ctx.channel and m.content.isdigit()

            invalid = True
            while invalid:
                try:
                    message = await globalValues.bot.wait_for('message', timeout=60, check=numCheck)
                    if not message.content.isdigit():
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number"))
                    elif int(message.content) < 3:
                        await ctx.channel.send(embed=discord.Embed(description="Please input a number greater than or equal to 3"))
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

async def chooseBackground(ctx, numCards):

    backgroundMessage = ctx.message
    
    selectedBackground = 0

    embedVar = discord.Embed(title="Backgrounds", description="Please select a background to use")
    embedVar.set_image(url=globalValues.backgrounds.get(numCards)[selectedBackground][0])
    backgroundMessage = await ctx.channel.send(embed=embedVar)
    await backgroundMessage.add_reaction('⬅️')
    await backgroundMessage.add_reaction('➡')
    await backgroundMessage.add_reaction('🔍')
    await backgroundMessage.add_reaction('✅')
    await backgroundMessage.add_reaction('❌')

    backgroundChosen = False
    while not backgroundChosen:
        try:
            def reactionCheck(react, user):
                return react.message == backgroundMessage and user == ctx.message.author and (react.emoji == '⬅️' or react.emoji == '➡' or react.emoji == '🔍' or react.emoji == '✅' or react.emoji == '❌')

            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=reactionCheck)
            reaction = reaction[0].emoji
            if reaction == '⬅️' or reaction == '➡':
                if reaction == '➡':
                    selectedBackground = (selectedBackground + 1) % len(globalValues.backgrounds.get(numCards))
                    # change embed to next background image
                    embedVar.set_image(url=globalValues.backgrounds.get(numCards)[selectedBackground][0])
                    await backgroundMessage.edit(embed=embedVar)
                else:
                    selectedBackground = (selectedBackground + len(globalValues.backgrounds.get(numCards)) - 1) % len(globalValues.backgrounds.get(numCards))
                    # change embed to previous background image
                    embedVar = discord.Embed(title="Backgrounds", description="Please select a background to use")
                    embedVar.set_image(url=globalValues.backgrounds.get(numCards)[selectedBackground][0])
                    await backgroundMessage.edit(embed=embedVar)
            elif reaction == '🔍':
                searchString = "Input the number of the background you want to see.\n"
                for i in range(len(globalValues.backgrounds.get(numCards))):
                    searchString = searchString + str(i + 1) + ". " + globalValues.backgrounds.get(numCards)[i][1] + "\n"
                embedSearch = discord.Embed(title="Background Search", description=searchString)

                def searchCheck(m):
                    if m.channel == ctx.channel and m.author == ctx.message.author and m.content.isdigit():
                        if int(m.content) >= 1 and int(m.content) <= len(globalValues.backgrounds.get(numCards)):
                            return True
                    return False

                await backgroundMessage.edit(embed=embedSearch)
                searchMessage = await globalValues.bot.wait_for('message', timeout=30, check=searchCheck)
                selectedBackground = int(searchMessage.content)
                try:
                    await searchMessage.delete()
                except:
                    pass
                selectedBackground -= 1
                embedVar.set_image(url=globalValues.backgrounds.get(numCards)[selectedBackground][0])
                await backgroundMessage.edit(embed=embedVar)
            elif reaction == '✅':
                embedVar = discord.Embed(title="Backgrounds", description="Please select a background to use", color=discord.Color.green())
                embedVar.set_image(url=globalValues.backgrounds.get(numCards)[selectedBackground][0])
                await backgroundMessage.edit(embed=embedVar)
                backgroundChosen = True
            elif reaction == '❌':
                embedVar = discord.Embed(title="Backgrounds", description="Please select a background to use", color=discord.Color.red())
                embedVar.set_image(url=globalValues.backgrounds.get(numCards)[selectedBackground][0])
                await backgroundMessage.edit(embed=embedVar)
                raise asyncio.TimeoutError
        except asyncio.TimeoutError:
            return None

    return (numCards, selectedBackground)

##############################################################################################################################################

async def chooseReactions(ctx, numCards):

    confirmed = False
    while not confirmed:
        reactionList = []

        reactionMessage = ctx.message
        for i in range(numCards):
        
            def reactionCheck(react, user):
                chosen = False
                if not isinstance(react.emoji, str):
                    return False
                for reaction in reactionList:
                    if react.emoji == reaction:
                        chosen = True
                return react.message == reactionMessage and user == ctx.author and not chosen
        
            embedVar = discord.Embed(title="Input Reactions", description="React to this message with the reaction that you want to represent card **" + str(i + 1) + "**. They cannot be personal server emotes.")

            if i == 0:
                reactionMessage = await ctx.channel.send(embed=embedVar)
            else:
                await reactionMessage.edit(embed=embedVar)

            try:
                reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=reactionCheck)
                reaction = reaction[0].emoji
                reactionList.append(reaction)
            except asyncio.TimeoutError:
                embedVar = discord.Embed(title="Input Reactions", description="React to this message with the reaction that you want to represent card **" + str(i + 1) + "**. They cannot be personal server emotes.", color=discord.Color.red())
                await reactionMessage.edit(embed=embedVar)
                return None

        embedVar = discord.Embed(title="Input Reactions", description="React to this message with the reaction that you want to represent card **" + str(i + 1) + "**. They cannot be personal server emotes.", color=discord.Color.green())
        await reactionMessage.edit(embed=embedVar)

        reactionStr = ""
        for i in range(len(reactionList)):
            reactionStr = reactionStr + "Card " + str(i + 1) + ": " + reactionList[i] + "\n"

        embedVar = discord.Embed(title="Confirm Reactions", description="Please confirm whether the reactions are correct:\n" + reactionStr)
        confirmMessage = await ctx.channel.send(embed=embedVar)
        await confirmMessage.add_reaction('✅')
        await confirmMessage.add_reaction('❌')

        def confirmCheck(react, user):
            return react.message == confirmMessage and user == ctx.author and (react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=confirmCheck)
            reaction = reaction[0].emoji

            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Reactions", description="Please confirm whether the reactions are correct:\n" + reactionStr, color=discord.Color.green())
                await confirmMessage.edit(embed=embedVar)
                confirmed = True
            else:
                embedVar = discord.Embed(title="Confirm Reactions", description="Please confirm whether the reactions are correct:\n" + reactionStr, color=discord.Color.red())
                await confirmMessage.edit(embed=embedVar)

        except asyncio.TimeoutError:
            return None

    return reactionList

##############################################################################################################################################

async def chooseTime(ctx, typeOfBrawl):

    timeList = []

    if typeOfBrawl == "brawl":
        
        timeList = await brawlDuration(ctx)

    else:

        timeList = await tournamentDuration(ctx)

    return timeList

##############################################################################################################################################

async def brawlDuration(ctx):

    durationList = []
    timeConfirmed = False
    while not timeConfirmed:
        def timeCheck(m):
                return m.channel == ctx.channel and m.author == ctx.author

        try:
            embedVar = discord.Embed(title="Set Voting Duration", description="Please input a voting duration for the brawl within the next 60 seconds (the duration must be greater than 0 seconds and less than or equal to 1 week).\n\nFormat as days:hours:minutes:seconds otherwise it won't work.\neg. 0:2:0:0 = 2 hours")
            await ctx.channel.send(embed=embedVar)
            timeMessage = await globalValues.bot.wait_for('message', timeout=60, check=timeCheck)
            timeSplit = timeMessage.content.split(':', 3)
            days = int(timeSplit[0])
            hours = int(timeSplit[1])
            minutes = int(timeSplit[2])
            seconds = int(timeSplit[3])

            if days < 0 or hours < 0 or minutes < 0 or seconds < 0:
                raise ValueError

            week = 604800
            durationTotal = days * 86400 + hours * 3600 + minutes * 60 + seconds

            if week < durationTotal or durationTotal <= 0:
                raise ValueError

            days = int(durationTotal / 86400)
            durationTotal = durationTotal % 86400
            hours = int(durationTotal / 3600)
            durationTotal = durationTotal % 3600
            minutes = int(durationTotal / 60)
            seconds = durationTotal % 60
            durationList = [days, hours, minutes, seconds]

            timeStr = ""
            for i in range(len(durationList)):
                timeStr = timeStr + str(durationList[i])
                if i == 0:
                    timeStr = timeStr + " day"
                elif i == 1:
                    timeStr = timeStr + " hour"
                elif i == 2:
                    timeStr = timeStr + " minute"
                elif i == 3:
                    timeStr = timeStr + " second"
                if durationList[i] != 1:
                    timeStr = timeStr + "s"
                timeStr = timeStr + "\n"

            embedVar = discord.Embed(title="Confirm Duration", description=timeStr + "\nIs this correct? Please react within the next 60 seconds.")
            timeConfirmMessage = await ctx.channel.send(embed=embedVar)
            await timeConfirmMessage.add_reaction('✅')
            await timeConfirmMessage.add_reaction('❌')

            def timeConfirm(react, user):
                return react.message == timeConfirmMessage and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=timeConfirm)
            reaction = reaction[0].emoji
            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Duration",  description=timeStr + "\nIs this correct? Please react within the next 60 seconds.", color=discord.Color.green())
                await timeConfirmMessage.edit(embed=embedVar)
                timeConfirmed = True
            else:
                embedVar = discord.Embed(title="Confirm Duration", description=timeStr + "Is this correct? Please react within the next 60 seconds.", color=discord.Color.red())
                await timeConfirmMessage.edit(embed=embedVar)
        except ValueError:
            embedVar = discord.Embed(description="There was an error in the format of the time or the time was invalid.")
            await ctx.channel.send(embed=embedVar)
        except IndexError:
            embedVar = discord.Embed(description="There was an error in the format of the time or the time was invalid.")
            await ctx.channel.send(embed=embedVar)
        except asyncio.TimeoutError:
            return None

    return durationList

##############################################################################################################################################

async def tournamentDuration(ctx):

    durationList = []
    timeConfirmed = False
    while not timeConfirmed:
        def timeCheck(m):
                return m.channel == ctx.channel and m.author == ctx.author

        try:
            embedVar = discord.Embed(title="Set Voting Duration", description="Please input a duration for the voting period for each match within the next 60 seconds (the duration must be greater than 0 seconds and less than or equal to 1 week).\n\nFormat as days:hours:minutes:seconds\neg. 0:2:0:0 = 2 hours")
            await ctx.channel.send(embed=embedVar)
            timeMessage = await globalValues.bot.wait_for('message', timeout=60, check=timeCheck)
            timeSplit = timeMessage.content.split(':', 3)
            days = int(timeSplit[0])
            hours = int(timeSplit[1])
            minutes = int(timeSplit[2])
            seconds = int(timeSplit[3])

            if days < 0 or hours < 0 or minutes < 0 or seconds < 0:
                raise ValueError

            week = 604800
            timeTotal = days * 86400 + hours * 3600 + minutes * 60 + seconds

            if week < timeTotal or timeTotal <= 0:
                raise ValueError

            days = int(timeTotal / 86400)
            durationTotal = timeTotal % 86400
            hours = int(timeTotal / 3600)
            durationTotal = timeTotal % 3600
            minutes = int(timeTotal / 60)
            seconds = timeTotal % 60
            durationList = [days, hours, minutes, seconds]

            timeStr = ""
            for i in range(len(durationList)):
                timeStr = timeStr + str(durationList[i])
                if i == 0:
                    timeStr = timeStr + " day"
                elif i == 1:
                    timeStr = timeStr + " hour"
                elif i == 2:
                    timeStr = timeStr + " minute"
                elif i == 3:
                    timeStr = timeStr + " second"
                if durationList[i] != 1:
                    timeStr = timeStr + "s"
                timeStr = timeStr + "\n"

            embedVar = discord.Embed(title="Confirm Duration", description=timeStr + "\nIs this correct? Please react within the next 60 seconds.")
            timeConfirmMessage = await ctx.channel.send(embed=embedVar)
            await timeConfirmMessage.add_reaction('✅')
            await timeConfirmMessage.add_reaction('❌')

            def timeConfirm(react, user):
                return react.message == timeConfirmMessage and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=timeConfirm)
            reaction = reaction[0].emoji
            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Duration",  description=timeStr + "\nIs this correct? Please react within the next 60 seconds.", color=discord.Color.green())
                await timeConfirmMessage.edit(embed=embedVar)
                timeConfirmed = True
            else:
                embedVar = discord.Embed(title="Confirm Duration", description=timeStr + "Is this correct? Please react within the next 60 seconds.", color=discord.Color.red())
                await timeConfirmMessage.edit(embed=embedVar)
        except ValueError:
            embedVar = discord.Embed(description="There was an error in the format of the time or the time was invalid.")
            await ctx.channel.send(embed=embedVar)
        except IndexError:
            embedVar = discord.Embed(description="There was an error in the format of the time or the time was invalid.")
            await ctx.channel.send(embed=embedVar)
        except asyncio.TimeoutError:
            return None

    tieList = []
    timeConfirmed = False
    while not timeConfirmed:
        def timeCheck(m):
                return m.channel == ctx.channel and m.author == ctx.author

        try:
            embedVar = discord.Embed(title="Set Tiebreaker Duration", description="Please input a duration for the tiebreaker matches within the next 60 seconds (the duration must be greater than 0 seconds and less than or equal to 1 week).\n\nFormat as days:hours:minutes:seconds\neg. 0:2:0:0 = 2 hours")
            await ctx.channel.send(embed=embedVar)
            timeMessage = await globalValues.bot.wait_for('message', timeout=60, check=timeCheck)
            timeSplit = timeMessage.content.split(':', 3)
            days = int(timeSplit[0])
            hours = int(timeSplit[1])
            minutes = int(timeSplit[2])
            seconds = int(timeSplit[3])

            if days < 0 or hours < 0 or minutes < 0 or seconds < 0:
                raise ValueError

            week = 604800
            timeTotal = days * 86400 + hours * 3600 + minutes * 60 + seconds

            if week < timeTotal or timeTotal <= 0:
                raise ValueError

            days = int(timeTotal / 86400)
            durationTotal = timeTotal % 86400
            hours = int(timeTotal / 3600)
            durationTotal = timeTotal % 3600
            minutes = int(timeTotal / 60)
            seconds = timeTotal % 60
            tieList = [days, hours, minutes, seconds]

            timeStr = ""
            for i in range(len(tieList)):
                timeStr = timeStr + str(tieList[i])
                if i == 0:
                    timeStr = timeStr + " day"
                elif i == 1:
                    timeStr = timeStr + " hour"
                elif i == 2:
                    timeStr = timeStr + " minute"
                elif i == 3:
                    timeStr = timeStr + " second"
                if durationList[i] != 1:
                    timeStr = timeStr + "s"
                timeStr = timeStr + "\n"

            embedVar = discord.Embed(title="Confirm Tiebreaker Duration", description=timeStr + "\nIs this correct? Please react within the next 60 seconds.")
            timeConfirmMessage = await ctx.channel.send(embed=embedVar)
            await timeConfirmMessage.add_reaction('✅')
            await timeConfirmMessage.add_reaction('❌')

            def timeConfirm(react, user):
                return react.message == timeConfirmMessage and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=timeConfirm)
            reaction = reaction[0].emoji
            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Tiebreaker Duration", description=timeStr + "\nIs this correct? Please react within the next 60 seconds.", color=discord.Color.green())
                await timeConfirmMessage.edit(embed=embedVar)
                timeConfirmed = True
            else:
                embedVar = discord.Embed(title="Confirm Tiebreaker Duration", description=timeStr + "\nIs this correct? Please react within the next 60 seconds.", color=discord.Color.red())
                await timeConfirmMessage.edit(embed=embedVar)
        except ValueError:
            embedVar = discord.Embed(description="There was an error in the format of the time or the time was invalid.")
            await ctx.channel.send(embed=embedVar)
        except IndexError:
            embedVar = discord.Embed(description="There was an error in the format of the time or the time was invalid.")
            await ctx.channel.send(embed=embedVar)
        except asyncio.TimeoutError:
            return None

    delayList = []
    timeConfirmed = False
    while not timeConfirmed:
        def timeCheck(m):
                return m.channel == ctx.channel and m.author == ctx.author

        try:
            embedVar = discord.Embed(title="Set Delay", description="Please input a duration for the delay between each match of the tournament within the next 60 seconds (the delay greater than or equal to 0 seconds and less than or equal to 1 week).\n\nFormat as days:hours:minutes:seconds\neg. 0:2:0:0 = 2 hours")
            await ctx.channel.send(embed=embedVar)
            timeMessage = await globalValues.bot.wait_for('message', timeout=60, check=timeCheck)
            timeSplit = timeMessage.content.split(':', 3)
            days = int(timeSplit[0])
            hours = int(timeSplit[1])
            minutes = int(timeSplit[2])
            seconds = int(timeSplit[3])

            if days < 0 or hours < 0 or minutes < 0 or seconds < 0:
                raise ValueError

            week = 604800
            timeTotal = days * 86400 + hours * 3600 + minutes * 60 + seconds

            if week < timeTotal or timeTotal < 0:
                raise ValueError

            days = int(timeTotal / 86400)
            durationTotal = timeTotal % 86400
            hours = int(timeTotal / 3600)
            durationTotal = timeTotal % 3600
            minutes = int(timeTotal / 60)
            seconds = timeTotal % 60
            delayList = [days, hours, minutes, seconds]

            timeStr = ""
            for i in range(len(delayList)):
                timeStr = timeStr + str(delayList[i])
                if i == 0:
                    timeStr = timeStr + " day"
                elif i == 1:
                    timeStr = timeStr + " hour"
                elif i == 2:
                    timeStr = timeStr + " minute"
                elif i == 3:
                    timeStr = timeStr + " second"
                if durationList[i] != 1:
                    timeStr = timeStr + "s"
                timeStr = timeStr + "\n"

            embedVar = discord.Embed(title="Confirm Delay", description=timeStr + "\nIs this correct? Please react within the next 60 seconds.")
            timeConfirmMessage = await ctx.channel.send(embed=embedVar)
            await timeConfirmMessage.add_reaction('✅')
            await timeConfirmMessage.add_reaction('❌')

            def timeConfirm(react, user):
                return react.message == timeConfirmMessage and user == ctx.message.author and (react.emoji == '✅' or react.emoji == '❌')

            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=timeConfirm)
            reaction = reaction[0].emoji
            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Delay",  description=timeStr + "\nIs this correct? Please react within the next 60 seconds.", color=discord.Color.green())
                await timeConfirmMessage.edit(embed=embedVar)
                timeConfirmed = True
            else:
                embedVar = discord.Embed(title="Confirm Delay", description=timeStr + "Is this correct? Please react within the next 60 seconds.", color=discord.Color.red())
                await timeConfirmMessage.edit(embed=embedVar)
        except ValueError:
            embedVar = discord.Embed(description="There was an error in the format of the time or the time was invalid.")
            await ctx.channel.send(embed=embedVar)
        except IndexError:
            embedVar = discord.Embed(description="There was an error in the format of the time or the time was invalid.")
            await ctx.channel.send(embed=embedVar)
        except asyncio.TimeoutError:
            return None

    return (durationList, tieList, delayList)

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

async def finalConfirm(ctx, typeOfBrawl, name, restricted, cardRestriction, maxParticipants, timeList, backgroundTuple, reactionList):
    
    if typeOfBrawl == "brawl":

        info = await brawlConfirm(ctx, name, restricted, cardRestriction, maxParticipants, timeList, backgroundTuple, reactionList)
        return info

    else:

        info = await tournamentConfirm(ctx, name, restricted, cardRestriction, maxParticipants, timeList, backgroundTuple, reactionList)
        return info

##############################################################################################################################################

async def brawlConfirm(ctx, name, restricted, cardRestriction, maxParticipants, timeList, backgroundTuple, reactionList):

    confirmed = False
    while not confirmed:
        timeStr = getTimeStr(timeList)

        sampleFileName = generateSample(ctx, backgroundTuple)

        if restricted == False:
            restrictedStr = "No participant restrictions"
        else:
            restrictedStr = "List of eligible roles:\n"
            for role in restricted:
                restrictedStr = restrictedStr + role + "\n"
        cardRestrictedStr = ""
        if cardRestriction == False:
            cardRestrictedStr = "No card restrictions"
        else:
            restrictedStr = restrictedStr + "List of eligible series:\n"
            for series in cardRestriction:
                restrictedStr = restrictedStr + series + "\n"
                
        embedVar = discord.Embed(title=name, description=restrictedStr + cardRestrictedStr + "\nMax number of participants: " + str(maxParticipants) + "\nDuration: " + timeStr)
        globalValues.getFile(str(ctx.guild.id), sampleFileName)
        sampleImage = discord.File(sampleFileName)
        embedVar.set_image(url="attachment://" + sampleFileName)
        preview = await ctx.channel.send(file=sampleImage, embed=embedVar)
        os.remove(sampleFileName)
        for i in range(maxParticipants):
            await preview.add_reaction(reactionList[i])

        embedVar = discord.Embed(title="Confirm Brawl",
                                    description="Is what you see above correct?\n" +
                                                "React with what you want to change:\n" +
                                                "🇳 : change the name\n" +
                                                "🚫 : change participant restriction\n" +
                                                "⛔ : change card restriction\n" +
                                                "#️⃣ : change the max number of participants\n" +
                                                "⏲️ : change the duration\n" +
                                                "🇧 : change the background\n" +
                                                "🇷 : change the reactions\n" +
                                                "✅ : looks good\n" + 
                                                "❌ : cancel setup")
        message = await ctx.channel.send(embed=embedVar)
        await message.add_reaction('🇳')
        await message.add_reaction('🚫')
        await message.add_reaction('⛔')
        await message.add_reaction('#️⃣')
        await message.add_reaction('⏲️')
        await message.add_reaction('🇧')
        await message.add_reaction('🇷')
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def competitionCheck(react, user):
            return react.message == message and user == ctx.message.author and (react.emoji == '🇳' or react.emoji == '🚫' or react.emoji == '⛔' or react.emoji == '#️⃣' or react.emoji == '⏲️' or react.emoji == '🇧' or react.emoji == '🇷' or react.emoji == '✅' or react.emoji == '❌')

        try:
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=competitionCheck)
            reaction = reaction[0].emoji
            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Brawl",
                                            description="Is what you see above correct?\n" +
                                                        "React with what you want to change:\n" +
                                                        "🇳 : change the name\n" +
                                                        "🚫 : change restriction\n" +
                                                        "⛔ : change card restriction\n" +
                                                        "#️⃣ : change the max number of participants\n" +
                                                        "⏲️ : change the duration\n" +
                                                        "🇧 : change the background\n" +
                                                        "🇷 : change the reactions\n" +
                                                        "✅ : looks good\n" + 
                                                        "❌ : cancel setup",
                                            color=discord.Color.green())
                await message.edit(embed=embedVar)
                globalValues.removeFile(str(ctx.guild.id), sampleFileName)
                confirmed = True
            elif reaction == '❌':
                embedVar = discord.Embed(title="Confirm Brawl",
                                            description="Is what you see above correct?\n" +
                                                        "React with what you want to change:\n" +
                                                        "🇳 : change the name\n" +
                                                        "🚫 : change restriction\n" +
                                                        "⛔ : change card restriction\n" +
                                                        "#️⃣ : change the max number of participants\n" +
                                                        "⏲️ : change the duration\n" +
                                                        "🇧 : change the background\n" +
                                                        "🇷 : change the reactions\n" +
                                                        "✅ : looks good\n" + 
                                                        "❌ : cancel setup",
                                            color=discord.Color.red())
                await message.edit(embed=embedVar)
                raise asyncio.TimeoutError
            else:
                embedVar = discord.Embed(title="Confirm Brawl",
                                            description="Is what you see above correct?\n" +
                                                        "React with what you want to change:\n" +
                                                        "🇳 : change the name\n" +
                                                        "🚫 : change restriction\n" +
                                                        "⛔ : change card restriction\n" +
                                                        "#️⃣ : change the max number of participants\n" +
                                                        "⏲️ : change the duration\n" +
                                                        "🇧 : change the background\n" +
                                                        "🇷 : change the reactions\n" +
                                                        "✅ : looks good\n" + 
                                                        "❌ : cancel setup",
                                            color=discord.Color.blue())
                await message.edit(embed=embedVar)
                if reaction == '🇳':
                    name = await chooseName(ctx, "brawl")
                    if not name:
                        raise asyncio.TimeoutError
                elif reaction == '🚫':
                    restricted = await chooseRestriction(ctx, "brawl")
                    if restricted == None:
                        raise asyncio.TimeoutError
                elif reaction == '⛔':
                    cardRestriction = await chooseCardRestriction(ctx, "brawl")
                    if cardRestriction == None:
                        raise asyncio.TimeoutError
                elif reaction == '#️⃣':
                    origMax = maxParticipants
                    maxParticipants = await chooseNumParticipants(ctx, "brawl")
                    if not maxParticipants:
                        raise asyncio.TimeoutError
                    if origMax != maxParticipants:
                        await ctx.channel.send(embed=discord.Embed(description="You changed the max number of participants, please choose a different background and reactions."))
                        backgroundTuple = await chooseBackground(ctx, maxParticipants)
                        if not backgroundTuple:
                            raise asyncio.TimeoutError
                        reactionList = await chooseReactions(ctx, maxParticipants)
                        if not reactionList:
                            raise asyncio.TimeoutError
                elif reaction == '⏲️':
                    timeList = await chooseTime(ctx, "brawl")
                    if not timeList:
                        raise asyncio.TimeoutError
                elif reaction == '🇧':
                    backgroundTuple = await chooseBackground(ctx, maxParticipants)
                    if not backgroundTuple:
                        raise asyncio.TimeoutError
                elif reaction == '🇷':
                    reactionList = await chooseReactions(ctx, maxParticipants)
                    if not reactionList:
                        raise asyncio.TimeoutError

                globalValues.removeFile(str(ctx.guild.id), sampleFileName)

        except asyncio.TimeoutError:
            globalValues.removeFile(str(ctx.guild.id), sampleFileName)
            return None

    participantDict = {}
    eligibilityList = [[], []]
    if restricted == False:
        eligibilityList[0] = None
    else:
        eligibilityList[0] = [[], restricted]
    if cardRestriction == False:
        eligibilityList[1] = None
    else:
        eligibilityList[1] = cardRestriction
    fileList = []

    return (name, ["brawl", 0, [participantDict, eligibilityList, maxParticipants], timeList, backgroundTuple, reactionList, fileList])

##############################################################################################################################################

async def tournamentConfirm(ctx, name, restricted, cardRestriction, maxParticipants, timeList, backgroundTuple, reactionList):

    confirmed = False
    while not confirmed:
        durationStr = getTimeStr(timeList[0])
        tiebreakerStr = getTimeStr(timeList[1])
        delayStr = getTimeStr(timeList[2])

        sampleFileName = generateSample(ctx, backgroundTuple)

        restrictedStr = ""
        if restricted == False:
            restrictedStr = "No participant restrictions\n"
        else:
            restrictedStr = "List of eligible roles:\n"
            for role in restricted:
                restrictedStr = restrictedStr + role + "\n"
        cardRestrictedStr = ""
        if cardRestriction == False:
            cardRestrictedStr = "No card restrictions"
        else:
            restrictedStr = restrictedStr + "List of eligible series:\n"
            for series in cardRestriction:
                restrictedStr = restrictedStr + series + "\n"
                
        embedVar = discord.Embed(title=name, description=restrictedStr + cardRestrictedStr + "\nMatch duration: " + durationStr + "\nTiebreaker match duration: " + tiebreakerStr + "\nDelay between matches: " + delayStr)
        globalValues.getFile(str(ctx.guild.id), sampleFileName)
        sampleImage = discord.File(sampleFileName)
        embedVar.set_image(url="attachment://" + sampleFileName)
        preview = await ctx.channel.send(file=sampleImage, embed=embedVar)
        os.remove(sampleFileName)
        for i in range(2):
            await preview.add_reaction(reactionList[i])
        embedVar = discord.Embed(title="Confirm Tournament",
                                    description="Is what you see above correct?\n" +
                                                "React with what you want to change:\n" +
                                                "🇳 : change the name\n" +
                                                "🚫 : change the participant restriction\n" +
                                                "⛔ : change card restriction\n" +
                                                "#️⃣ : change the max number of participants\n" +
                                                "⏲️ : change the duration\n" +
                                                "🇧 : change the background\n" +
                                                "🇷 : change the reactions\n" +
                                                "✅ : looks good\n" + 
                                                "❌ : cancel setup")
        message = await ctx.channel.send(embed=embedVar)

        def competitionCheck(react, user):
            return react.message == message and user == ctx.message.author and (react.emoji == '🇳' or react.emoji == '🚫' or react.emoji == '#️⃣' or react.emoji == '⏲️' or react.emoji == '🇧' or react.emoji == '🇷' or react.emoji == '✅' or react.emoji == '❌')

        try:
            await message.add_reaction('🇳')
            await message.add_reaction('🚫')
            await message.add_reaction('⛔')
            await message.add_reaction('#️⃣')
            await message.add_reaction('⏲️')
            await message.add_reaction('🇧')
            await message.add_reaction('🇷')
            await message.add_reaction('✅')
            await message.add_reaction('❌')
            reaction = await globalValues.bot.wait_for('reaction_add', timeout=60, check=competitionCheck)
            reaction = reaction[0].emoji
            if reaction == '✅':
                embedVar = discord.Embed(title="Confirm Tournament",
                                            description="Is what you see above correct?\n" +
                                                        "React with what you want to change:\n" +
                                                        "🇳 : change the name\n" +
                                                        "🚫 : change restriction\n" +
                                                        "⛔ : change card restriction\n" +
                                                        "#️⃣ : change the max number of participants\n" +
                                                        "⏲️ : change the duration\n" +
                                                        "🇧 : change the background\n" +
                                                        "🇷 : change the reactions\n" +
                                                        "✅ : looks good\n" + 
                                                        "❌ : cancel setup",
                                            color=discord.Color.green())
                await message.edit(embed=embedVar)
                globalValues.removeFile(str(ctx.guild.id), sampleFileName)
                confirmed = True
            elif reaction == '❌':
                embedVar = discord.Embed(title="Confirm Tournament",
                                            description="Is what you see above correct?\n" +
                                                        "React with what you want to change:\n" +
                                                        "🇳 : change the name\n" +
                                                        "🚫 : change restriction\n" +
                                                        "⛔ : change card restriction\n" +
                                                        "#️⃣ : change the max number of participants\n" +
                                                        "⏲️ : change the duration\n" +
                                                        "🇧 : change the background\n" +
                                                        "🇷 : change the reactions\n" +
                                                        "✅ : looks good\n" + 
                                                        "❌ : cancel setup",
                                            color=discord.Color.red())
                await message.edit(embed=embedVar)
                raise asyncio.TimeoutError
            else:
                embedVar = discord.Embed(title="Confirm Tournament",
                                            description="Is what you see above correct?\n" +
                                                        "React with what you want to change:\n" +
                                                        "🇳 : change the name\n" +
                                                        "🚫 : change restriction\n" +
                                                        "⛔ : change card restriction\n" +
                                                        "#️⃣ : change the max number of participants\n" +
                                                        "⏲️ : change the duration\n" +
                                                        "🇧 : change the background\n" +
                                                        "🇷 : change the reactions\n" +
                                                        "✅ : looks good\n" + 
                                                        "❌ : cancel setup",
                                            color=discord.Color.blue())
                await message.edit(embed=embedVar)
                if reaction == '🇳':
                    name = await chooseName(ctx, "tournament")
                    if not name:
                        raise asyncio.TimeoutError
                elif reaction == '🚫':
                    restricted = await chooseRestriction(ctx, "tournament")
                    if restricted == None:
                        raise asyncio.TimeoutError
                elif reaction == '⛔':
                    cardRestriction = await chooseCardRestriction(ctx, "tournament")
                    if cardRestriction == None:
                        raise asyncio.TimeoutError
                elif reaction == '#️⃣':
                    maxParticipants = await chooseNumParticipants(ctx, "tournament")
                    if not maxParticipants:
                        raise asyncio.TimeoutError
                elif reaction == '⏲️':
                    timeList = await chooseTime(ctx, "tournament")
                    if not timeList:
                        raise asyncio.TimeoutError
                elif reaction == '🇧':
                    backgroundTuple = await chooseBackground(ctx, 2)
                    if not backgroundTuple:
                        raise asyncio.TimeoutError
                elif reaction == '🇷':
                    reactionList = await chooseReactions(ctx, 2)
                    if not reactionList:
                        raise asyncio.TimeoutError

                globalValues.removeFile(str(ctx.guild.id), sampleFileName)

        except asyncio.TimeoutError:
            globalValues.removeFile(str(ctx.guild.id), sampleFileName)
            return None

    participantDict = {}
    eligibilityList = [[], []]
    if restricted == False:
        eligibilityList[0] = None
    else:
        eligibilityList[0] = [[], restricted]
    if cardRestriction == False:
        eligibilityList[1] = None
    else:
        eligibilityList[1] = cardRestriction
    fileList = []

    return (name, ["tournament", 0, [participantDict, eligibilityList, maxParticipants], timeList, backgroundTuple, reactionList, fileList])

##############################################################################################################################################

def generateSample(ctx, backgroundTuple):
    
    req = urllib.request.Request(globalValues.backgrounds.get(backgroundTuple[0])[backgroundTuple[1]][0], headers=globalValues.header)
    backgroundImage = Image.open(urlopen(req))
    backgroundImage.convert('RGBA')
    image = backgroundImage.copy()
    imageFileName = str(ctx.guild.id) + "-" + str(time.time()) + "-sample" + ".png"

    for i in range(backgroundTuple[0]):
        req = urllib.request.Request(globalValues.sampleCards[i], headers=globalValues.header)
        cardImage = Image.open(urlopen(req))
        cardImage.convert('RGBA')
        image.paste(cardImage, (globalValues.cardCoordinates.get(backgroundTuple[0])[i][0], globalValues.cardCoordinates.get(backgroundTuple[0])[i][1]), cardImage)

    image.save(imageFileName, quality=95)
    globalValues.addFile(str(ctx.guild.id), imageFileName);
    os.remove(imageFileName);

    return imageFileName

##############################################################################################################################################

async def store(ctx, info):

    async with globalValues.guildLocks.get(str(ctx.guild.id)).writer_lock:
        if not globalValues.savedCompetitions.get(str(ctx.guild.id)).get(info[0]):
            globalValues.savedCompetitions[str(ctx.guild.id)][info[0]] = info[1]
            globalValues.brawlLocks[str(ctx.guild.id)][info[0]] = aiorwlock.RWLock()
        else:
            await brawlExists(ctx)
            return
    
    typeOfBrawl = info[1][0]

    if typeOfBrawl == "brawl":
        await ctx.channel.send(embed=discord.Embed(tile="", description="Brawl setup complete", color=discord.Color.green()))
    else:
        await ctx.channel.send(embed=discord.Embed(tile="", description="Tournament setup complete", color=discord.Color.green()))

    await globalValues.store()

##############################################################################################################################################

async def invalidArg(ctx):
    await ctx.channel.send(embed=discord.Embed(description="Please input either brawl or tournament"))

##############################################################################################################################################

async def tooLarge(ctx):
    await ctx.channel.send(embed=discord.Embed(description="Sadly, brawls with more than 2 competitors are not supported yet. If you make a background for brawls of more than 2 cards and give it to me, then it'll happen."))

##############################################################################################################################################

async def brawlExists(ctx):
    await ctx.channel.send(embed=discord.Embed(description="There already exists a brawl or tournament of that name. Cancelling setup", color=discord.Color.red()))

##############################################################################################################################################

async def cancel(ctx):
    await ctx.channel.send(embed=discord.Embed(description="Host setup cancelled", color=discord.Color.red()))