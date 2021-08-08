from discord.ext import commands


class GameAlreadyInPlay(commands.CommandError):
    pass


class MorePlayersNeeded(commands.CommandError):
    pass


class IncorrectSyntax(commands.CommandError):
    pass


class UserNotPlayer(commands.CommandError):
    pass


class NoGameBeingPlayed(commands.CommandError):
    pass


class IncorrectIncrement(commands.CommandError):
    pass
