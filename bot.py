import discord
import requests
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_USERNAME = os.getenv("API_USERNAME", "SMSbot")
API_PASSWORD = os.getenv("API_PASSWORD", "SMStavanger4ever")

# Discord setup
intents = discord.Intents.default()
intents.members = True  # Needed to manage roles
bot = commands.Bot(command_prefix="!", intents=intents)

API_BASE = "https://medlem.telamork.net/"
AUTH_ENDPOINT = f"{API_BASE}api-auth/"
ACTIVE_CHECK_ENDPOINT = f"{API_BASE}api1_clubmembernameactive/str:{{nick}}/"


def get_api_token():
    try:
        response = requests.post(AUTH_ENDPOINT, data={
            "username": API_USERNAME,
            "password": API_PASSWORD
        })
        response.raise_for_status()
        return response.json().get("token")
    except Exception as e:
        print(f"[ERROR] Failed to authenticate with API: {e}")
        return None


def check_membership_active(nick, token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = ACTIVE_CHECK_ENDPOINT.replace("{nick}", nick)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()  # True or False
    except Exception as e:
        print(f"[ERROR] Failed to verify {nick}: {e}")
        return None


@bot.event
async def on_ready():
    print(f"[INFO] Logged in as {bot.user.name}")


@bot.command()
async def verify(ctx, *, nickname=None):
    user = ctx.author
    nick_to_check = nickname or user.display_name

    await ctx.send(f"Verifying membership for `{nick_to_check}`...")

    token = get_api_token()
    if not token:
        await ctx.send("Authentication with the membership system failed.")
        return

    is_active = check_membership_active(nick_to_check, token)
    if is_active is True:
        role = discord.utils.get(ctx.guild.roles, name="Verified")
        if role:
            await user.add_roles(role)
            await ctx.send(f"✅ `{nick_to_check}` is verified. Role assigned.")
        else:
            await ctx.send("The 'Verified' role is missing. Please ask an admin to create it.")
    elif is_active is False:
        await ctx.send(f"❌ `{nick_to_check}` is not an active member.")
    else:
        await ctx.send("An error occurred while checking your status. Try again later.")


@bot.command()
@commands.has_permissions(administrator=True)
async def forceverify(ctx, member: discord.Member, *, nickname):
    """Admin command to verify another user."""
    token = get_api_token()
    if not token:
        await ctx.send("API authentication failed.")
        return

    is_active = check_membership_active(nickname, token)
    if is_active is True:
        role = discord.utils.get(ctx.guild.roles, name="Verified")
        if role:
            await member.add_roles(role)
            await ctx.send(f"✅ `{nickname}` verified and role assigned to {member.display_name}.")
        else:
            await ctx.send("The 'Verified' role is missing. Admin must create it.")
    elif is_active is False:
        await ctx.send(f"❌ `{nickname}` is not active.")
    else:
        await ctx.send("Error during verification process.")


bot.run(DISCORD_TOKEN)