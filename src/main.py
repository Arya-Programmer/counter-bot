import os
import sqlite3
from datetime import datetime

import discord
from discord.ext import commands

from pathlib import Path

from discord.ext.commands import NoEntryPointError, ExtensionNotLoaded, ExtensionAlreadyLoaded
from discord_components import DiscordComponents

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "info.db")
COGS_PATH = os.path.join(BASE_DIR, 'cogs')


class CountBot(commands.Bot):
    def __init__(self):
        self.conn = sqlite3.connect(DB_DIR, timeout=5)
        self.cursor = self.conn.cursor()
        self._cogs = [p.stem for p in Path(COGS_PATH).glob("*")]

        super().__init__(command_prefix=self.prefix, case_insensitive=True, intents=discord.Intents.all())

    def setup(self):
        print("Running Setup")

        for cog in self._cogs:
            try:
                print(cog)
                self.load_extension(f'cogs.{cog}')
                print(f"Loaded '{cog}' cog.")
            except NoEntryPointError:
                continue

        print("Setup Complete")

    def run(self):
        self.setup()

        print(os.environ.keys())
        # TOKEN = os.environ['BOT_TOKEN']
        TOKEN = "ODcyOTMxMTA5OTcxODM3MDg5.YQxCcg.BNUrsOWQIouMKvNCXshjycyGDJY"

        print("Running bot...")
        super().run(TOKEN, reconnect=True)

    async def add_data_if_not_exist(self, ctx):
        settingsHasRows = self.cursor.execute("SELECT * FROM SERVER_SETTINGS WHERE guild = ?", (ctx.guild.id, )).fetchall()
        if ctx.guild.id not in settingsHasRows:
            self.cursor.execute("INSERT INTO SERVER_SETTINGS VALUES (?,?,?,?,?,?,?)",
                                (ctx.guild.id, str(ctx.guild.channels), "ct.", "all", "100", 60, True))

    async def on_connect(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS HISTORY(
                     guild           TEXT    NOT NULL,
                     channels        TEXT    NOT NULL,
                     user            TEXT    NOT NULL,
                     command         TEXT    NOT NULL,
                     date          timestamp NOT NULL
                 );''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS SERVER_SETTINGS(
                     guild           TEXT    NOT NULL,
                     count_channels  TEXT    NOT NULL,
                     prefix          TEXT    NOT NULL,
                     allowed_roles   TEXT    NOT NULL,
                     restart_count   TEXT    NOT NULL,
                     restart_timer   INT     NOT NULL,
                     check_player_turn BOOL  NOT NULL
                 );''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS USER_SETTINGS(
                     user            TEXT    NOT NULL,
                     turn_announcement BOOL  DEFAULT true             
                 );''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS COUNT(
                     guild           TEXT    NOT NULL,
                     channel_id      TEXT    NOT NULL,
                     players         TEXT    NOT NULL,
                     said_words      TEXT,
                     word_count      INT     DEFAULT 0
                 );''')
        print(f"Connected to Discord (latency: {self.latency * 1000}ms )")

    async def shutdown(self):
        print("Closing connection to Discord/SQL...")
        self.cursor.close()
        await super().close()

    async def on_ready(self):
        DiscordComponents(self, change_discord_methods=True)
        self.client_id = (await self.application_info()).id
        print(self.client_id)

    async def prefix(self, bot, msg):
        await self.add_data_if_not_exist(msg)
        prefix = self.cursor.execute("SELECT prefix FROM SERVER_SETTINGS WHERE guild = ?",
            (msg.guild.id, )).fetchone()[0]
        print(f"Current {prefix=}")
        return commands.when_mentioned_or(prefix)(bot, msg)

    async def process_commands(self, msg):
        ctx = await self.get_context(msg, cls=commands.Context)

        if ctx.command is not None:
            self.cursor.execute("INSERT INTO HISTORY VALUES (?, ?, ?, ?, ?)",
                                (ctx.guild.id, ctx.channel.id, str(ctx.author), msg.content, str(datetime.now())))
            self.conn.commit()
            await self.invoke(ctx)

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_commands(msg)


if __name__ == '__main__':
    client = CountBot()


    @client.command()
    async def reload(ctx):
        for cog in [p.stem for p in Path("").glob("cogs/*.py")]:
            print(cog)
            print(COGS_PATH)
            print(DB_DIR)
            try:
                client.unload_extension(f'cogs.{cog}')
                client.load_extension(f'cogs.{cog}')
            except (ExtensionAlreadyLoaded, ExtensionNotLoaded):
                try:
                    client.load_extension(f'cogs.{cog}')
                except NoEntryPointError:
                    continue
        await ctx.send("Reloaded")


    client.run()
