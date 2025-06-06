import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Google Sheets auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Google Sheets URL
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1ixALQkOLF-lqjvpXik3Q5AUilsx3F5m_5yNGkb83ccs/edit")

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")

@bot.command()
async def vente(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    nom_joueur = ctx.author.display_name

    try:
        feuille = spreadsheet.worksheet(nom_joueur)
    except gspread.exceptions.WorksheetNotFound:
        await ctx.send(f"❌ Feuille introuvable pour {nom_joueur}. Vérifie que l’onglet existe.")
        return

    await ctx.send("🛠️ Veux-tu faire une :\n1️⃣ Customisation\n2️⃣ Réparation\nRéponds par 1 ou 2")

    try:
        choix = await bot.wait_for("message", timeout=30.0, check=check)
    except:
        await ctx.send("⏰ Temps écoulé.")
        return

    tz = pytz.timezone('Europe/Paris')
    now = datetime.datetime.now(tz)
    date = now.strftime("%d/%m/%Y")
    heure = now.strftime("%H:%M")

    type_action = ""

    if choix.content == "1":
        type_action = "Customisation"
        await ctx.send("🔠 Entre la plaque :")
        plaque = await bot.wait_for("message", timeout=30.0, check=check)

        await ctx.send("💰 Entre le prix :")
        prix = await bot.wait_for("message", timeout=30.0, check=check)

        donnees_custom = feuille.get("B10:B100")
        ligne_vide_relative = next((i for i, val in enumerate(donnees_custom) if not val or val[0].strip() == ""), len(donnees_custom))
        ligne_ecriture = 10 + ligne_vide_relative

        feuille.update_cell(ligne_ecriture, 2, date)           # B
        feuille.update_cell(ligne_ecriture, 3, heure)          # C
        feuille.update_cell(ligne_ecriture, 4, plaque.content) # D
        feuille.update_cell(ligne_ecriture, 5, prix.content)   # E

        await ctx.send("✅ Customisation enregistrée.")
        await ctx.send("📸 Merci d'envoyer un screen de la facture payée.")

    elif choix.content == "2":
        type_action = "Réparation"
        donnees_rep = feuille.get("G10:G100")
        ligne_vide_relative = next((i for i, val in enumerate(donnees_rep) if not val or val[0].strip() == ""), len(donnees_rep))
        ligne_ecriture = 10 + ligne_vide_relative

        # Demande s'il s'est déplacé
        await ctx.send("🚗 Est-ce que tu t'es déplacé ? (oui/non)")
        try:
            deplacement = await bot.wait_for("message", timeout=30.0, check=check)
            reponse = deplacement.content.strip().lower()
            if reponse not in ["oui", "non"]:
                await ctx.send("❌ Réponse invalide. Écris simplement `oui` ou `non`.")
                return
        except:
            await ctx.send("⏰ Temps écoulé pour la réponse au déplacement.")
            return

        feuille.update_cell(ligne_ecriture, 7, date)     # G
        feuille.update_cell(ligne_ecriture, 8, heure)    # H
        feuille.update_cell(ligne_ecriture, 9, reponse)  # I (oui / non)

        await ctx.send("✅ Réparation enregistrée.")
        await ctx.send("📸 Merci d'envoyer un screen de la facture payée.")

    else:
        await ctx.send("❌ Choix invalide. Utilise 1 ou 2.")
        return

    # Attente du screen (image)
    try:
        message = await bot.wait_for(
            "message",
            timeout=60.0,
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.attachments
        )
        pseudo_salon = ctx.author.display_name.lower().replace(" ", "-") + "-screen"
        channel = discord.utils.get(ctx.guild.text_channels, name=pseudo_salon)

        if channel:
            await channel.send(f"{ctx.author.display_name} {type_action} :", file=await message.attachments[0].to_file())
            await ctx.send("✅ Screen transféré dans le salon dédié.")
        else:
            await ctx.send(f"⚠️ Salon '{pseudo_salon}' introuvable pour transférer le screen.")

    except:
        await ctx.send("⏰ Aucune image reçue. Si tu as un screen, merci de l'envoyer rapidement la prochaine fois.")

# Démarre le bot
bot.run("")
