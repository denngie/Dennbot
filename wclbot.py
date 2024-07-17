#!/usr/bin/python3.10
"""WCL Bot."""
from interactions import (
    Client,
    Intents,
    listen,
    slash_command,
    SlashContext,
    OptionType,
    slash_option,
    SlashCommandChoice,
    Embed,
)
from wclapi import WCL
from settings import BOT_TOKEN, ENCOUNTERS, ZONES

bot = Client(intents=Intents.DEFAULT)


def zone_option():  # type: ignore
    """Start zone option."""

    def wrapper(func):  # type: ignore
        return slash_option(
            name="zone",
            description="Choose a zone",
            required=True,
            opt_type=OptionType.INTEGER,
            choices=[SlashCommandChoice(name=v, value=k) for k, v in ZONES.items()],
        )(func)

    return wrapper


def start_date_option():  # type: ignore
    """Start date option."""

    def wrapper(func):  # type: ignore
        return slash_option(
            name="start_date",
            description="ISO8601 date | Example: 2022-04-01",
            required=False,
            opt_type=OptionType.STRING,
        )(func)

    return wrapper


def end_date_option():  # type: ignore
    """End date option."""

    def wrapper(func):  # type: ignore
        return slash_option(
            name="end_date",
            description="ISO8601 date | Example: 2022-04-31",
            required=False,
            opt_type=OptionType.STRING,
        )(func)

    return wrapper


def encounter_option():  # type: ignore
    """End date option."""

    def wrapper(func):  # type: ignore
        return slash_option(
            name="encounter",
            description="Choose a specific raid (Naxx/Sarth/Maly only)",
            required=False,
            opt_type=OptionType.INTEGER,
            choices=[
                SlashCommandChoice(name=v, value=k) for k, v in ENCOUNTERS.items()
            ],
        )(func)

    return wrapper


@listen()
async def on_ready() -> None:
    """Event called when the bot is ready to respond to commands."""
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


@slash_command(
    name="attendance", description="Show the attendance statistics based on logs"
)
@zone_option()
@start_date_option()
@end_date_option()
# @encounter_option()
async def attendance_function(
    ctx: SlashContext,
    zone: int,
    start_date: str = "",
    end_date: str = "",
    encounter: int = 0,
) -> None:
    """Discord embed response with attendance data."""
    await ctx.defer()
    wcl = WCL(zone=zone, start_date=start_date, end_date=end_date, encounter=encounter)
    try:
        players_attendance = wcl.calculate_attendance()
    except ConnectionError as err:
        await ctx.send(f"Something went wrong. Error message {err}")
        return

    output = Embed()
    output.title = "Attendance"
    text = []

    if encounter:
        field_name = ENCOUNTERS[encounter]
    else:
        field_name = ZONES[zone]
    if start_date or end_date:
        field_name += f" ({start_date}-{end_date})"

    for player in players_attendance:
        text.append(player)

    for i in range(0, len(text), 15):
        if i != 0:
            field_name = "\u200b"
        output.add_field(
            name=field_name, inline=True, value="\n".join(text[i : i + 15])
        )

    await ctx.send(embed=output)


@slash_command(name="deaths", description="Show the deaths statistics based on logs")
@zone_option()
@start_date_option()
@end_date_option()
# @encounter_option()
async def deaths_function(
    ctx: SlashContext,
    zone: int,
    start_date: str = "",
    end_date: str = "",
    encounter: int = 0,
) -> None:
    """Discord embed response with attendance data."""
    await ctx.defer()

    wcl = WCL(zone=zone, start_date=start_date, end_date=end_date, encounter=encounter)
    try:
        player_stats = wcl.calculate_deaths()
    except ConnectionError as err:
        await ctx.send(f"Something went wrong. Error message {err}")
        return

    if encounter:
        field_name = ENCOUNTERS[encounter]
    else:
        try:
            field_name = ZONES[zone]
        except KeyError:
            field_name = ""

    if start_date or end_date:
        field_name += f" ({start_date}-{end_date})"

    output = Embed()
    output.title = "Average deaths per raid (minimum five raids and wipes excluded)"
    text = []
    for player, value in sorted(
        player_stats.items(), key=lambda item: item[1], reverse=True
    ):
        text.append(f"{player}: {value:.1f}")

    for i in range(0, len(text), 15):
        if i != 0:
            field_name = "\u200b"
        output.add_field(
            name=field_name, inline=True, value="\n".join(text[i : i + 15])
        )
    await ctx.send(embed=output)


bot.start(BOT_TOKEN)
