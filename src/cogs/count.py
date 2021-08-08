import asyncio

from discord_components import *
from discord import Embed
from discord.ext import commands

from src.cogs.decorators import connectToDB
from src.cogs.errors import GameAlreadyInPlay
from .errors import MorePlayersNeeded, IncorrectSyntax, UserNotPlayer, NoGameBeingPlayed, IncorrectIncrement


class Count(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="start", alises=['st'])
    @connectToDB
    async def start(self, ctx, *, _=None, cursor=None):
        games = cursor.execute(f"SELECT * FROM COUNT WHERE guild = {ctx.guild.id} AND channel_id = {ctx.channel.id}") \
            .fetchall()
        if len(games) > 0:
            print(games)
            raise GameAlreadyInPlay

        players = [ctx.author]
        respond_msg = str("IDK WHAT HAPPENED WHAT DID U DO MF, SHOULD I KICK U?")
        is_msg_editable = False
        game_not_started = True

        def _check_join(res):
            nonlocal respond_msg, embed, is_msg_editable
            print(str(res.user), "JOINED")
            if res.component.label.startswith("Join") and not res.user.bot:
                if res.user not in players:
                    players.append(res.user)
                    print(players)
                    embed.clear_fields()
                    for player in players:
                        embed.add_field(name=str(players.index(player) + 1), value=player.name)
                    is_msg_editable = True
                    respond_msg = f"You JOINED {ctx.author.name}'s game!"
                    return True
                respond_msg = f"You have already joined the game"
                return True

        def _check_start(res):
            nonlocal game_not_started
            print(str(res.user), "STARTED")
            if res.component.label.startswith("Start") and res.user == ctx.author and not res.user.bot:
                if len(players) > 1:
                    cursor.execute(f"INSERT INTO COUNT (guild, channel_id, players) VALUES (?,?,?)",
                                   (str(ctx.guild.id), str(ctx.channel.id), str([user.id for user in players]),))
                    print("Game Started", (str(ctx.guild.id), str(ctx.channel.id), str([user.id for user in players]),))
                    game_not_started = False
                    return True

        embed = Embed(title="Start Game",
                      description=f"{ctx.author.name} Wants to play `Count` or `Word Chain` or Whatever you call it",
                      color=0xffc800)

        for player in players:
            embed.add_field(name=str(players.index(player) + 1), value=player.name)

        msg = await ctx.send(type=InteractionType.ChannelMessageWithSource, embed=embed,
                             components=[Button(style=ButtonStyle.green, label="Join", custom_id="join"),
                                         Button(style=ButtonStyle.blue, label="Start", custom_id="start",
                                                disabled=True)])
        while game_not_started:
            if is_msg_editable:
                await msg.edit(type=InteractionType.ChannelMessageWithSource, embed=embed,
                               components=[Button(style=ButtonStyle.green, label="Join", custom_id="join"),
                                           Button(style=ButtonStyle.blue, label="Start", custom_id="start",
                                                  disabled=len(players) <= 1)])
                is_msg_editable = False

            if len(players) > 1:
                start_button = await self.bot.wait_for("button_click", check=_check_start)
                await start_button.respond(type=4, content="Game started")
            try:
                join_button = await self.bot.wait_for("button_click", timeout=5, check=_check_join)
            except asyncio.TimeoutError:
                if len(players) <= 1:
                    raise MorePlayersNeeded

            try:
                await join_button.respond(content=respond_msg)
            except Exception as e:
                print(e)

        embed.title = "GAME STARTED! THE FIRST WORD IS `HELLO`"
        await msg.edit(type=InteractionType.ChannelMessageWithSource, embed=embed,
                       components=[Button(style=ButtonStyle.green, label="Join", custom_id="join"),
                                   Button(style=ButtonStyle.blue, label="Start", custom_id="start",
                                          disabled=len(players) <= 1)])

    @commands.Cog.listener()
    @connectToDB
    async def on_message(self, message, cursor=None):
        games = cursor.execute(
                    f"SELECT * FROM COUNT WHERE guild = {message.guild.id} AND channel_id = {message.channel.id}"
                ).fetchall()
        games = cursor.execute(
                    f"SELECT * FROM SERVER_SETTINGS WHERE guild = {message.guild.id} AND channel_id = {message.channel.id}"
                ).fetchall()

        if len(games) > 0:
            players = eval(games[0][2])
            print(message.author.id, players, players[1])
            if message.author.id in players:
                if '.' in message.content:
                    num, word = message.content.split('.')
                elif '-' in message.content:
                    num, word = message.content.split('-')
                elif ' ' in message.content:
                    num, word = message.content.split(' ')
                else:
                    raise IncorrectSyntax

                num = int(str(num).strip())
                word = str(num).strip()

                previous_num = int(games[0][4])
                if num == previous_num+1:
                    print(num, word, message.author.name)
                    previous_words = games[0][3] if games[0][3] else []
                    cursor.execute(f"UPDATE COUNT SET guild = ?, channel_id = ?, said_words = ?, word_count = "
                                   f"word_count+1 WHERE guild = ? AND channel_id = ?",
                                   (str(message.guild.id), str(message.channel.id),
                                    str([*previous_words, word]), num, str(message.guild.id), str(message.channel.id)))
                else:
                    raise IncorrectIncrement
            else:
                raise UserNotPlayer
        else:
            raise NoGameBeingPlayed


def setup(bot):
    bot.add_cog(Count(bot))
