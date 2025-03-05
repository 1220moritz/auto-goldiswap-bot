"""
Notification module for the Goldilocks DeFi bot.
Handles sending notifications to Discord.
"""
from discord_webhook import DiscordWebhook
import config


def send_discord_message(msg: str):
    """
    Send a message to Discord webhook.
    
    Args:
        msg: Message content to send
        
    Returns:
        None
    """
    try:
        webhook = DiscordWebhook(url=config.WEBHOOK_URL, content=msg)
        webhook.execute()
        print(f"Discord message sent: {msg}")
    except Exception as e:
        print(f"Failed to send Discord message: {e}")


class EventMessageCollector:
    """
    Collects event messages for a cycle and formats them for Discord.
    """
    
    def __init__(self):
        """Initialize an empty event message list."""
        self.messages = []
    
    def add_success(self, message):
        """Add a success message."""
        self.messages.append(f"✅ {message}")
    
    def add_warning(self, message):
        """Add a warning message."""
        self.messages.append(f"⚠️ {message}")
    
    def add_error(self, message):
        """Add an error message."""
        self.messages.append(f"❌ {message}")
    
    def add_info(self, message):
        """Add an informational message."""
        self.messages.append(f"ℹ️ {message}")
    
    def send(self):
        """Send all collected messages to Discord."""
        if self.messages:
            send_discord_message("\n".join(self.messages))
            self.messages = []  # Clear messages after sending
