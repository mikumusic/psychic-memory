import aiofiles
import discord
from discord.ext import commands
import random
import keep_alive


intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix= "YOUR_PREFIX_HERE") #your prefix here example ">", "?", "!"
client.warnings = {} # guild_id : {member_id: [count, [(admin_id, reason)]]}
client.remove_command("help")





@client.group(invoke_without_command=True)
async def help(ctx):
  em = discord.Embed(title = "Help <command>", description = "Use {YOUR PREFIX HERE} help for the Command List", color = ctx.author.color) #change your prefix here as your prefix

  em.add_field(name = "Moderation", value = "Kick, Ban, Mute, Unmute, Slowmode, Clear, Warn,  Warnings, Lock, Unlock, Ping")

  await ctx.send(embed = em)

@client.event
async def on_ready():
      for guild in client.guilds:
        client.warnings[guild.id] = {}

        async with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
            pass

        async with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
            lines = await file.readlines()

            for line in lines:
                data = line.split(" ")
                member_id = int(data[0])
                admin_id = int(data[1])
                reason = " ".join(data[2:]).strip("\n")

                try:
                    client.warnings[guild.id][member_id][0] += 1
                    client.warnings[guild.id][member_id][1].append((admin_id, reason))

                except KeyError:
                    client.warnings[guild.id][member_id] = [1, [(admin_id, reason)]] 

        print("Logged Into Bot")

@client.event
async def on_guild_join(guild):
    client.warnings[guild.id] = {}

@client.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member=None, *, reason=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

    if reason is None:
        return await ctx.send("Please provide a reason for warning this user.")

    try:
        first_warning = False
        client.warnings[ctx.guild.id][member.id][0] += 1
        client.warnings[ctx.guild.id][member.id][1].append((ctx.author.id, reason))

    except KeyError:
        first_warning = True
        client.warnings[ctx.guild.id][member.id] = [1, [(ctx.author.id, reason)]]

    count = client.warnings[ctx.guild.id][member.id][0]

    async with aiofiles.open(f"{ctx.guild.id}.txt", mode="a") as file:
        await file.write(f"{member.id} {ctx.author.id} {reason}\n")

    await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")

@client.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: discord.Member=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

    embed = discord.Embed(title=f"Displaying Warnings for {member.name}", description="", colour=discord.Colour.purple())
    try:
        i = 1
        for admin_id, reason in client.warnings[ctx.guild.id][member.id][1]:
            admin = ctx.guild.get_member(admin_id)
            embed.description += f"**Warning {i}** given by: {admin.mention} for: *'{reason}'*.\n"
            i += 1

        await ctx.send(embed=embed)

    except KeyError: # no warnings
        await ctx.send("This user has no warnings.")
 
@client.command(case_insensitive=True)
async def ping(ctx):
    await ctx.send("Pong!")
 
@client.command(case_insensitive=True)
async def slowmode(ctx, time:int):
    if (not ctx.author.guild_permissions.manage_messages):
        await ctx.send('You cannot use this command! Requires: ``Manage Messages``')
        return
    if time == 0:
        await ctx.send('Slowmode is currently set to **0** **seconds**')
        await ctx.channel.edit(slowmode_delay = 0)
    elif time > 21600:
        await ctx.send('You cannot make slowmode higher than 6 hours!')
        return
    else:
        await ctx.channel.edit(slowmode_delay = time)
        await ctx.send(f"Slowmode has been set to **{time}** **seconds!**")

@client.command(aliases=['clear'])
async def purge(ctx, amount=11):
    if(not ctx.author.guild_permissions.manage_messages):
        await ctx.send('You cannot use this command! Requires: ``Manage Messages``')
        return
    amount = amount+1
    if amount > 101:
        await ctx.send('I can\'t delete more than 100 messages at a time!')
    else: 
        await ctx.channel.purge(limit=amount)
        await ctx.send(f'Sucessfully deleted **{amount} messages!**')

@client.command(case_insensitive=True)
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} has been Kicked form {ctx.guild}')

@client.command(case_insensitive=True)
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} has been Banned form {ctx.guild}')

@client.command(case_insensitive=True)
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    if reason == None:
        await ctx.send('Please write a reason!')
        return
    guild = ctx.guild
    muteRole = discord.utils.get(guild.roles, name = "Muted")
 
    if not muteRole:
        await ctx.send("No Mute Role found! Creating one now...")
        muteRole = await guild.create_role(name = "Muted")
 
        for channel in guild.channels:
            await channel.set_permissions(muteRole, speak=False, send_messages=False, read_messages=True, read_message_history=True)
        await member.add_roles(muteRole, reason=reason)
        await ctx.send(f"{member.mention} has been muted in {ctx.guild} | Reason: {reason}")
        await member.send(f"You have been muted in {ctx.guild} | Reason: {reason}")
 
@client.command(case_insensitive=True)
async def unmute(ctx, member: discord.Member, *, reason=None):
 
    guild = ctx.guild
    muteRole = discord.utils.get(guild.roles, name = "Muted")
 
    if not muteRole:
        await ctx.send("The Mute role can\'t be found! Please check if there is a mute role or if the user already has it!")
        return
    await member.remove_roles(muteRole, reason=reason)
    await ctx.send(f"{member.mention} has been unmuted in {ctx.guild}")
    await member.send(f"You have been unmuted in {ctx.guild}")

@client.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role,send_messages=False)
    await ctx.send( ctx.channel.mention + " ***has been locked.***")

@client.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(ctx.channel.mention + " ***has been unlocked.***")

   

keep_alive.keep_alive()
client.run("YOUR_BOT_TOKEN_HERE") #your token here from https://discord.com/developers/applications