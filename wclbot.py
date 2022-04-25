#!/usr/bin/python3.10
"""WCL Bot."""
from dis_snek import (Snake, Intents, InteractionContext, OptionTypes, SlashCommandChoice, Embed,
                      listen, slash_command, slash_option)
from wclapi import WCL
from settings import BOT_TOKEN

bot = Snake(intents=Intents.DEFAULT)


@listen()
async def on_ready() -> None:
    """Event called when the bot is ready to respond to commands."""
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


@slash_command(name="attendance", description="Show the attendance statistics based on logs")
@slash_option(
    name="zone",
    description="Choose a zone",
    required=True,
    opt_type=OptionTypes.INTEGER,
    choices=[
        SlashCommandChoice(name="BT/MH", value=1011),  # type: ignore
        SlashCommandChoice(name="SSC/TK", value=1010),  # type: ignore
    ]
)
@slash_option(
    name="start_date",
    description="ISO8601 date | Example: 2022-04-01",
    required=False,
    opt_type=OptionTypes.STRING
)
@slash_option(
    name="end_date",
    description="ISO8601 date | Example: 2022-04-31",
    required=False,
    opt_type=OptionTypes.STRING
)
@slash_option(
    name="encounter",
    description="Choose a specific raid",
    required=False,
    opt_type=OptionTypes.INTEGER,
    choices=[
        SlashCommandChoice(name="BT", value=601),  # type: ignore
        SlashCommandChoice(name="MH", value=618)  # type: ignore
    ]
)
async def attendance_function(ctx: InteractionContext, zone: int, start_date: str = "",
                              end_date: str = "", encounter: int = 0) -> None:
    """Discord embed response with attendance data."""
    await ctx.defer()
    wcl = WCL()
    players_attendance, total_raids = wcl.calculated_attendance(zone=zone,
                                                                start_date=start_date,
                                                                end_date=end_date,
                                                                encounter=encounter)
    output = Embed()
    output.title = "Attendance"
    text = []
    for player, value in sorted(players_attendance.items(), key=lambda item: item[1], reverse=True):
        percentage = value / total_raids * 100
        text.append(f"{player}: {percentage:.0f}%")
    if encounter:
        if encounter == 601:
            field_name = "BT"
        elif encounter == 618:
            field_name = "MH"
    else:
        if zone == 1011:
            field_name = "BT/MH"
        elif zone == 1010:
            field_name = "SSC/TK"
    field_name += f" ({start_date}-{end_date})"

    output.add_field(name=field_name, value="\n".join(text))
    await ctx.send(embed=output)


bot.start(BOT_TOKEN)
