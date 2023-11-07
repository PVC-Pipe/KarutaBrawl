# setup.py
# By: PVCPipe01
# contains the setup command

import discord
import os
from discord.ext import commands

import globalValues

async def setup(ctx):

    dm = await ctx.author.create_dm()

    embedVar = discord.Embed(title="Permissions Information", description="In order to use commands besides \"submit\" and \"participants\", the user must have the role \"Brawls\", otherwise this bot will sit and do nothing. Once the role has been assigned, type kb!help to see the commands or just read this.")

    await dm.send(embed=embedVar)

    embedVar = discord.Embed(title="Hosting a Brawl or Tournament", description=
                       "Command: \"kb!host brawl\" or \"kb!host tournament\"\n" +
                       "This will open the host interface.\n" +
                       "\n" +
                       "**Brawls**: brawls are 1 round competitions where ties are accepted.\n" +
                       "**Tournaments**: tournaments are single elimination tournaments with 1st, 2nd, and 3rd place.\n" + 
                       "\n" +
                       "**Hosting options**:\n" +
                       "Set the name.\n" +
                       "Restrict the tournament to specific people or roles.\n" +
                       "Restrict the tournament to specific series.\n" +
                       "Set the maximum number of participants.\n" +
                       "Set duration.\n" +
                       "Choose the background.\n" +
                       "Choose the reactions for voting.\n" +
                       "Confirm selections.\n" +
                       "\n" +
                       "**Differences between brawls and tournaments**:\n" +
                       "Tournaments have a duration for the rounds, tiebreaker rounds, and delays in between rounds, while brawls just have the one round's duration.\n"
                       "\n" +
                       "**Other info**:\n" +
                       "Names of saved brawls and tournaments must all be different. Names are also case sensitive."
                       "Tournaments will auto fill with pass cards to reach a power of 2 number of contestants.")

    await dm.send(embed=embedVar)

    embedVar = discord.Embed(title="Submitting a Card", description=
                       "kb!submit <brawl or tournament name> <card code>\n" +
                       "\n" +
                       "To submit a card, type the above command and then k!v the card. If the user does not own the card, the submission won't go through. The user will recieve confirmation once the submission goes through.\n" +
                       "Users cannot submit cards when the brawl or tournament in question is being edited, is closed, or live.")
    
    await dm.send(embed=embedVar)

    embedVar = discord.Embed(title="Viewing Current Participants", description=
                       "Command: kb!participants <brawl or tournament name>\n" +
                       "\n" +
                       "Returns the current participant list without opening the editor.")

    await dm.send(embed=embedVar)

    embedVar = discord.Embed(title="Closing and Opening a Brawl or Tournament", description=
                       "Closing a brawl or tournament will prevent any more people from entering the brawl or tournament. It will also show the user a preview of what the brawl or tournament will look like when it is started.\n" +
                       "\n" +
                       "Opening a brawl or tournament will reopent the brawl or tournament to entrants.\n" +
                       "Users cannot open or close while the brawl or tournament is being edited or live.")

    await dm.send(embed=embedVar)

    embedVar = discord.Embed(title="Starting a Brawl or Tournament", description=
                       "Command: kb!start <brawl or tournament name>\n" +
                       "\n" +
                       "A brawl or tournament cannot be started until it is closed and not being edited.\n"
                       "Once started, a brawl or tournament cannot be stopped until it has finished.\n" +
                       "Tournaments rounds that tie twice will be decided by a coin flip.")

    await dm.send(embed=embedVar)

    embedVar = discord.Embed(title="Editing a Brawl or Tournament", description=
                       "Editing a brawl or tournament allows you to change anything you want. There are some complex things though. If the brawl or tournament is closed, you will not be able to edit eligibility.\n" +
                       "\n" +
                       "**Participants**:\n" +
                       "The editor allows you to remove participants by id, @, or card code. You can remove individually or with lists separeated by commas. You cannot add participants.\n" +
                       "\n" +
                       "**Eligibility**:\n" +
                       "The editor allows you to change the eligibility of participants.\n" +
                       "You can add and remove participant and card restrictions.\n" +
                       "You can add and remove individual participants to the eligibility list if there's a price to enter the tournament or brawl. You can add people to the eligibility list with kb!eligible <id or @>\n" +
                       "You can add and remove role eligiblity.\n" +
                       "You can add and remove series restrictions.\n" +
                       "If a participant is removed from the eligibility list, but still has an eligible role, they won't be removed from the participant list. The opposite also applies.\n" + 
                       "If a series is removed from the eligible series list, no participants will be removed.")

    await dm.send(embed=embedVar)

    embedVar = discord.Embed(title="Viewing Saved Brawls and Tournaments", description=
                       "Command: kb!mybrawls\n" +
                       "\n" +
                       "Will show the user the currently saved brawls and completed brawls.")

    await dm.send(embed=embedVar)

    embedVar = discord.Embed(title="Deleting Brawls and Tournaments", description=
                       "Command: kb!delete <brawl or tournament name>\n" +
                       "\n" +
                       "Use this command to delete a brawl or tournament, it will give you preview of the brawl or tournament you are about to delete then ask for confirmation.")

    await dm.send(embed=embedVar)


    

