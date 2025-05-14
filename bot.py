import os
import discord
from discord.ext import tasks
from discord import app_commands
import requests
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set your constants
DISCORD_CHANNEL_ID = 1370437377146880044
PIXELGREW_POOL_ID = 'GEeWf7at9sytpVb73MqSj9jn8bD5Jx1BHB21a6T82wQz'
PIXELGREW_TOKEN_ADDRESS = 'HSf4zrNZj7ZbMWiPqC2M9DWZDB1rgZicCGmLJh6mXray'

# Bot state
last_price = None

# Create bot client
class PixelGrewBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        GUILD_ID = 1150040799569002586  # <-- Replace with your actual server ID
        guild = discord.Object(id=GUILD_ID)
        await self.tree.sync(guild=guild)
        print(f"Slash commands synced to guild {GUILD_ID}")

bot = PixelGrewBot()

# --- Price Fetching ---
def get_pixelgrew_price():
    try:
        url = f'https://api.geckoterminal.com/api/v2/networks/solana/pools/{PIXELGREW_POOL_ID}'
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        price_str = data['data']['attributes']['base_token_price_usd']
        return float(price_str)
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

# --- Price Check Task ---
@tasks.loop(seconds=60)
async def check_price():
    global last_price
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print("Discord channel not found.")
        return

    current_price = get_pixelgrew_price()
    if current_price is None:
        return

    if last_price is None:
        last_price = current_price
        return

    percent_change = ((current_price - last_price) / last_price) * 100
    if abs(percent_change) >= 1:
        direction = "up" if percent_change > 0 else "down"
        message = (
            f"📈 **PIXELGREW Price Alert**\n"
            f"Price moved {abs(percent_change):.2f}% {direction}!\n"
            f"Current Price: ${current_price:.6f} USDC\n"
            f"[View on Solana Explorer](https://explorer.solana.com/address/{PIXELGREW_TOKEN_ADDRESS})"
        )
        await channel.send(message)
        last_price = current_price

# --- Slash Command ---
@bot.tree.command(name="price", description="Check the current PIXELGREW token price")
async def slash_price(interaction: discord.Interaction):
    current_price = get_pixelgrew_price()
    if current_price is None:
        await interaction.response.send_message("Error fetching PIXELGREW price. Try again later.", ephemeral=True)
    else:
        await interaction.response.send_message(
            f"**PIXELGREW Price**\n"
            f"Current Price: ${current_price:.6f} USDC\n"
            f"[Token Explorer](https://explorer.solana.com/address/{PIXELGREW_TOKEN_ADDRESS})"
        )

# --- Bot Ready ---
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    if not check_price.is_running():
        check_price.start()

# --- Run ---
bot.run(DISCORD_BOT_TOKEN)
