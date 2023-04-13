import asyncio

import requests
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
import textwrap

from discord.ext.commands import UserInputError

CALENDER_URL = 'https://www.forexfactory.com/calendar'
IMPACT_DICT = {"High Impact Expected": "high", "Low Impact Expected": "low", "Medium Impact Expected": "medium",
               "Non-Economic": "none"}
TOKEN = 'Input discord token'
CHANNEL_ID = "Input channel id"
FILTER_COUNTRIES = None
FILTER_IMPACT = None
COUNTRIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "NZD", "CHF"]
IMPACT_LEVELS = ["high", "low", "medium", "none"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def get_calender_data(countries=None, impacts=None):
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    response = requests.get(CALENDER_URL, headers=headers)

    soup = BeautifulSoup(response.content, "html.parser")

    events = []

    for row in soup.select('tr.calendar_row'):
        event = {}
        event['date'] = row.select_one('td.calendar__date').get_text()
        event['time'] = row.select_one('td.calendar__time').get_text()
        event['currency'] = row.select_one('td.calendar__currency').get_text()
        event['impact'] = row.select_one('td.calendar__impact').find('span').get('title')
        event['event'] = row.select_one('td.calendar__event').get_text()

        if countries and event["currency"].strip().lower() not in [c.lower() for c in countries]:
            continue

        if impacts and not any(i.lower() in IMPACT_DICT[event["impact"]].lower() for i in impacts):
            continue
        events.append(event)

    return events


async def send_calender_alerts(countries, impact):
    channel = bot.get_channel(CHANNEL_ID)
    while True:
        calender_data = get_calender_data(countries, impact)
        if calender_data:
            message = "**Economic Calendar Alert**\n\n"
            for event in calender_data:
                message += f"{event['date']} | {event['time']} | {event['currency']} | {event['impact']} | {event['event']}\n"
            message_chunks = textwrap.wrap(message, width=2000)
            for chunk in message_chunks:
                await channel.send(chunk)
        await asyncio.sleep(60)


@bot.command()
async def get_events(ctx):
    await ctx.send("Economic calender alerts started.")
    bot.loop.create_task(send_calender_alerts(FILTER_COUNTRIES, FILTER_IMPACT))


@bot.command(name='commands')
async def help_command(ctx):
    """Displays a list of available commands and their descriptions."""
    help_message = """
    **Available Commands:**
    `!commands`: Displays a list of available commands and their descriptions.
    `!set_country <country>`: Sets the country for which to receive event alerts.
    `!set_impact <impact>`: Sets the minimum impact level for which to receive event alerts.
    `!get_events`: Displays a list of upcoming events that match the current country and impact level settings.
    """
    await ctx.send(help_message)


@bot.command(name='set_country')
async def set_country_command(ctx, *countries):
    """Sets the country for which to receive event alerts."""
    global FILTER_COUNTRIES
    arguments = ', '.join(countries)
    FILTER_COUNTRIES = arguments.split(',')
    invalid_countries = []
    for idx, country in enumerate(FILTER_COUNTRIES):
        if country.upper() not in COUNTRIES:
            invalid_countries.append(country)
        if invalid_countries:
            raise UserInputError(f"Invalid country/countries: {', '.join(invalid_countries)}")
        else:
            await ctx.send(f"Countries set to {FILTER_COUNTRIES[idx]}")


@set_country_command.error
async def set_country_command_error(ctx, error):
    if isinstance(error, UserInputError):
        await ctx.send(error)


@bot.command(name='set_impact')
async def set_impact_command(ctx, *impact_levels):
    print("got here")
    """Sets the minimum impact level for which to receive event alerts."""
    global FILTER_IMPACT
    invalid_impacts = []
    arguments = ', '.join(impact_levels)
    FILTER_IMPACT = arguments.split(',')
    for idx, impact in enumerate(impact_levels):
        if impact not in IMPACT_LEVELS:
            invalid_impacts.append(impact)
        if invalid_impacts:
            raise UserInputError(f"Invalid impact levels: {', '.join(invalid_impacts)}")
        else:
            await ctx.send(f"Impact levels set to {FILTER_IMPACT[idx]}")


@set_impact_command.error
async def set_impact_command_error(ctx, error):
    if isinstance(error, UserInputError):
        await ctx.send(error)


def main():
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
