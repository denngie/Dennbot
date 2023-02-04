#!/usr/bin/python3.10
"""WCL Bot."""
from dis_snek import (Snake, Intents, InteractionContext, OptionTypes, SlashCommandChoice, Embed,
                      listen, slash_command, slash_option)
from wclapi import WCL
from settings import BOT_TOKEN

bot = Snake(intents=Intents.DEFAULT)


def zone_option():  # type: ignore
    """Start zone option."""

    def wrapper(func):  # type: ignore
        return slash_option(
            name="zone",
            description="Choose a zone",
            required=True,
            opt_type=OptionTypes.INTEGER,
            choices=[
                SlashCommandChoice(name="Naxx/Sarth/Maly", value=1015),  # type: ignore
                SlashCommandChoice(name="VoA", value=1016),  # type: ignore
                SlashCommandChoice(name="Ulduar", value=1017),  # type: ignore
            ]
        )(func)

    return wrapper


def start_date_option():  # type: ignore
    """Start date option."""

    def wrapper(func):  # type: ignore
        return slash_option(
            name="start_date",
            description="ISO8601 date | Example: 2022-04-01",
            required=False,
            opt_type=OptionTypes.STRING
        )(func)

    return wrapper


def end_date_option():  # type: ignore
    """End date option."""

    def wrapper(func):  # type: ignore
        return slash_option(
            name="end_date",
            description="ISO8601 date | Example: 2022-04-31",
            required=False,
            opt_type=OptionTypes.STRING
        )(func)

    return wrapper


def encounter_option():  # type: ignore
    """End date option."""

    def wrapper(func):  # type: ignore
        return slash_option(
            name="encounter",
            description="Choose a specific raid (Naxx/Sarth/Maly only)",
            required=False,
            opt_type=OptionTypes.INTEGER,
            choices=[
                SlashCommandChoice(name="Naxx", value=101119),  # type: ignore
                SlashCommandChoice(name="Sarth", value=742),  # type: ignore
                SlashCommandChoice(name="Maly", value=734),  # type: ignore
            ]
        )(func)

    return wrapper


@listen()
async def on_ready() -> None:
    """Event called when the bot is ready to respond to commands."""
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


@slash_command(name="attendance", description="Show the attendance statistics based on logs")
@zone_option()
@start_date_option()
@end_date_option()
@encounter_option()
async def attendance_function(ctx: InteractionContext,
                              zone: int,
                              start_date: str = "",
                              end_date: str = "",
                              encounter: int = 0) -> None:
    """Discord embed response with attendance data."""
    await ctx.defer()
    wcl = WCL(zone=zone,
              start_date=start_date,
              end_date=end_date,
              tag=50758,
              encounter=encounter)
    try:
        players_attendance, total_raids = wcl.calculate_attendance()
    except ConnectionError as err:
        await ctx.send(f"Something went wrong. Error message {err}")
        raise Exception from err
    output = Embed()
    output.title = "Attendance"
    text = []

    if encounter:
        if encounter == 101119:
            field_name = "Naxx"
        elif encounter == 742:
            field_name = "Sarth"
        elif encounter == 734:
            field_name = "Maly"
    else:
        if zone == 1015:
            field_name = "Naxx/Sarth/Maly"
        elif zone == 1016:
            field_name = "VoA"
        elif zone == 1017:
            field_name = "Ulduar"
    if start_date or end_date:
        field_name += f" ({start_date}-{end_date})"

    for player, value in sorted(players_attendance.items(), key=lambda item: item[1], reverse=True):
        percentage = value / total_raids * 100
        percentage = min(percentage, 100)
        text.append(f"{player}: {percentage:.0f}%")

    for i in range(0, len(text), 15):
        if i != 0:
            field_name = "\u200b"
        output.add_field(name=field_name, inline=True, value="\n".join(text[i:i + 15]))

    await ctx.send(embed=output)


@slash_command(name="deaths", description="Show the deaths statistics based on logs")
@zone_option()
@slash_option(
    name="tag",
    description="Choose a specific tag",
    required=True,
    opt_type=OptionTypes.INTEGER,
    choices=[
        SlashCommandChoice(name="Main raid", value=50758),  # type: ignore
        SlashCommandChoice(name="Pug", value=50705)  # type: ignore
    ]
)
@start_date_option()
@end_date_option()
@encounter_option()
async def deaths_function(ctx: InteractionContext,
                          zone: int,
                          tag: int,
                          start_date: str = "",
                          end_date: str = "",
                          encounter: int = 0) -> None:
    """Discord embed response with attendance data."""
    await ctx.defer()

    wcl = WCL(zone=zone, start_date=start_date, end_date=end_date,
              tag=tag, encounter=encounter)
    try:
        player_stats = wcl.calculate_deaths()
    except ConnectionError as err:
        await ctx.send(f"Something went wrong. Error message {err}")
        raise Exception(err) from err

    if encounter:
        if encounter == 101119:
            field_name = "Naxx"
        elif encounter == 742:
            field_name = "Sarth"
        elif encounter == 734:
            field_name = "Maly"
    else:
        if zone == 1015:
            field_name = "Naxx/Sarth/Maly"
        elif zone == 1016:
            field_name = "VoA"
        elif zone == 1017:
            field_name = "Ulduar"
        else:
            field_name = ""

    if tag == 50705:
        field_name += " pugs"
    if start_date or end_date:
        field_name += f" ({start_date}-{end_date})"

    output = Embed()
    output.title = "Average deaths per raid (minimum five raids and wipes excluded)"
    text = []
    for player, value in sorted(player_stats.items(), key=lambda item: item[1], reverse=True):
        text.append(f"{player}: {value:.1f}")

    for i in range(0, len(text), 15):
        if i != 0:
            field_name = "\u200b"
        output.add_field(name=field_name, inline=True, value="\n".join(text[i:i + 15]))
    await ctx.send(embed=output)


bot.start(BOT_TOKEN)
