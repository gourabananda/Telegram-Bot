import os
import json
import csv
import io
from datetime import datetime
from bs4 import BeautifulSoup
from paddleocr import PPStructureV3
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio
from dotenv import load_dotenv
load_dotenv()
tokens = os.getenv("TOKEN")
# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize PPStructureV3 pipeline
pipeline = PPStructureV3()

# Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def html_table_to_json(html: str, header_row_index: int = 0):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    if not table:
        return {"error": "No table found in HTML"}

    rows = table.find_all("tr")

    table_data = []
    num_cols = 0

    # Detect number of columns from first row with data
    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) > 0:
            num_cols = len(cells)
            break

    # Build headers (use first row or generate default headers)
    headers = []
    raw_header_cells = rows[header_row_index].find_all(["td", "th"])
    if len(raw_header_cells) == num_cols:
        headers = [cell.get_text(strip=True) or f"Column{i+1}" for i, cell in enumerate(raw_header_cells)]
        data_rows = rows[header_row_index + 1:]
    else:
        headers = [f"Column{i+1}" for i in range(num_cols)]
        data_rows = rows  # treat all rows as data

    # Parse rows
    for row in data_rows:
        cells = row.find_all(["td", "th"])
        row_data = [cell.get_text(strip=True) for cell in cells]
        if len(row_data) < num_cols:
            row_data += [""] * (num_cols - len(row_data))  # pad if cells missing
        elif len(row_data) > num_cols:
            row_data = row_data[:num_cols]  # truncate extras

        table_data.append(dict(zip(headers, row_data)))

    return table_data

async def process_image(image_path):
    if not os.path.exists(image_path):
        return {"error": "Image file does not exist"}

    output = pipeline.predict(input=image_path)
    if not output or 'table_res_list' not in output[0]:
        return {"error": "No table found in image"}

    html_content = output[0]['table_res_list'][0]['pred_html']
    json_data = html_table_to_json(html_content)

    return json_data

def generate_csv_bytes(data):
    """Generate CSV file in memory and return as bytes"""
    if not data or not isinstance(data, list):
        return None
        
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys() if len(data) > 0 else [])
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue().encode('utf-8')

def generate_json_bytes(data):
    """Generate JSON file in memory and return as bytes"""
    return json.dumps(data, indent=2).encode('utf-8')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! I'm a bot that can extract tables from images. "
        "Just send me an image (PNG/JPG) containing a table, "
        "and I'll extract the data for you in both JSON and CSV formats."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Send me an image containing a table (PNG or JPG format), "
        "and I'll extract the table data and send it back to you "
        "in both JSON and CSV formats.\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/help - This help message"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming images and process them."""
    # Check if the message contains a photo
    if not update.message.photo:
        await update.message.reply_text("Please send an image file (PNG/JPG).")
        return

    # Get the highest resolution photo
    photo_file = await update.message.photo[-1].get_file()
    file_ext = "jpg"  # Telegram photos are always JPG
    filename = f"{update.message.message_id}.{file_ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Download the photo
    await photo_file.download_to_drive(filepath)

    # Process the image
    await update.message.reply_text("Processing your image...")
    await update.message.reply_text("Please wait, this may take a minute...")
    
    try:
        parsed_data = await process_image(filepath)
        
        if "error" in parsed_data:
            await update.message.reply_text(f"Error: {parsed_data['error']}")
        else:
            # Format the response
            response = "Here's the data I extracted:\n\n"
            if isinstance(parsed_data, list) and len(parsed_data) > 0:
                # Show first few rows as example
                for i, row in enumerate(parsed_data[:3]):
                    response += f"Row {i+1}:\n"
                    for key, value in row.items():
                        response += f"  {key}: {value}\n"
                    response += "\n"
                
                if len(parsed_data) > 3:
                    response += f"\n...and {len(parsed_data) - 3} more rows.\n"
                
                await update.message.reply_text(response)
                
                # Generate files in memory
                json_bytes = generate_json_bytes(parsed_data)
                csv_bytes = generate_csv_bytes(parsed_data)
                
                if json_bytes and csv_bytes:
                    # Send JSON file
                    await update.message.reply_document(
                        document=InputFile(io.BytesIO(json_bytes), filename="table_data.json"),
                        caption="Extracted data in JSON format"
                    )
                    # Send CSV file
                    await update.message.reply_document(
                        document=InputFile(io.BytesIO(csv_bytes), filename="table_data.csv"),
                        caption="Extracted data in CSV format"
                    )
                else:
                    await update.message.reply_text("Failed to generate output files.")
            else:
                await update.message.reply_text("I found a table but couldn't extract any data from it.")
            
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("Sorry, I encountered an error processing your image.")
    
    finally:
        # Clean up original image
        if os.path.exists(filepath):
            os.remove(filepath)

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(tokens).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e. message - handle images
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main()