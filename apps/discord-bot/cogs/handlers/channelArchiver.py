import discord
from discord.ext import commands, bridge
from discord import File
from datetime import datetime
import io
from .DatabaseHandler import testingservers


class channelArchiver(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bridge.bridge_command(guild_ids=testingservers, name="exportchat", description="Export messages from a channel to an HTML file.")
    @commands.has_permissions(administrator=True)  # Restrict to admins
    async def export_chat(self, ctx, channel_or_thread_id: str = None, limit: int = 100):
        """
        Export messages from a channel or thread to an HTML file.
        Usage: !exportchat #channel-name [limit]
        Usage: !exportchat <thread_id> [limit]
        Usage: !exportchat [limit] (exports current channel/thread)
        Default limit is 100 messages.
        """
        target = None

        # If no argument provided, use current channel/thread
        if channel_or_thread_id is None:
            target = ctx.channel
        else:
            # Try to parse as a channel mention or ID
            try:
                # Remove <# and > if it's a mention
                clean_id = channel_or_thread_id.strip('<#>').strip()
                channel_id = int(clean_id)

                # Try to get as a channel first
                target = ctx.guild.get_channel(channel_id)

                # If not found as channel, try as thread
                if target is None:
                    target = ctx.guild.get_thread(channel_id)

                # If still not found, try fetching it
                if target is None:
                    try:
                        target = await ctx.guild.fetch_channel(channel_id)
                    except:
                        pass

                if target is None:
                    await ctx.send(f"❌ Could not find channel or thread with ID: {channel_id}")
                    return

            except ValueError:
                await ctx.send(f"❌ Invalid channel/thread ID: {channel_or_thread_id}")
                return

        # Cap the limit to prevent abuse
        limit = min(limit, 1000)

        # Determine type for status message
        target_type = "thread" if isinstance(target, discord.Thread) else "channel"
        target_mention = f"<#{target.id}>"

        # Send a status message
        status_msg = await ctx.send(f"📥 Fetching up to {limit} messages from {target_type} {target_mention}...")

        try:
            # Fetch messages from the channel/thread
            messages = []
            async for message in target.history(limit=limit, oldest_first=True):
                messages.append(message)

            if not messages:
                await status_msg.edit(content=f"❌ No messages found in that {target_type}!")
                return

            # Generate HTML
            html_content = self.generate_html(messages, target)

            # Create file-like object
            html_file = io.BytesIO(html_content.encode('utf-8'))

            # Create Discord file object with channel name and date
            date_str = datetime.now().strftime('%Y-%m-%d')
            # Clean the channel/thread name for filename (remove special characters)
            clean_name = ''.join(c if c.isalnum() or c in ('-', '_') else '_' for c in target.name)
            filename = f"{clean_name}_{date_str}.html"
            discord_file = File(html_file, filename=filename)

            # Send to the channel where the command was used
            await status_msg.delete()
            await ctx.send(
                f"✅ Exported {len(messages)} messages from {target_type} {target_mention}",
                file=discord_file
            )

        except discord.Forbidden:
            await status_msg.edit(content=f"❌ I don't have permission to read messages in that {target_type}!")
        except Exception as e:
            await status_msg.edit(content=f"❌ An error occurred: {str(e)}")

    def generate_html(self, messages, target):
        """Generate HTML from messages"""

        # Get target info (works for both channels and threads)
        target_name = target.name
        guild_name = target.guild.name
        export_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        # Determine if it's a thread
        is_thread = isinstance(target, discord.Thread)
        target_type = "Thread" if is_thread else "Channel"

        # Get parent channel name if it's a thread
        parent_info = ""
        if is_thread and target.parent:
            parent_info = f" (in #{target.parent.name})"

        # Get guild icon
        guild_icon = target.guild.icon.url if target.guild.icon else ""

        # Start building HTML
        html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{target_name} - {guild_name}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: 'gg sans', 'Noto Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                background-color: #313338;
                color: #dbdee1;
                padding: 0;
                margin: 0;
            }}

            .container {{
                max-width: 100%;
                margin: 0 auto;
                background-color: #313338;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }}

            .header {{
                background-color: #313338;
                padding: 16px 20px;
                border-bottom: 1px solid #26282c;
                box-shadow: 0 1px 0 rgba(0,0,0,.2), 0 1.5px 0 rgba(0,0,0,.05), 0 2px 0 rgba(0,0,0,.05);
            }}

            .header h1 {{
                color: #f2f3f5;
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 4px;
                display: flex;
                align-items: center;
            }}

            .header .guild-icon {{
                width: 24px;
                height: 24px;
                border-radius: 50%;
                margin-right: 8px;
            }}

            .header .thread-badge {{
                display: inline-flex;
                align-items: center;
                background-color: #5865f2;
                color: #ffffff;
                font-size: 10px;
                font-weight: 600;
                padding: 2px 6px;
                border-radius: 3px;
                margin-left: 8px;
                text-transform: uppercase;
            }}

            .header .info {{
                color: #949ba4;
                font-size: 13px;
            }}

            .messages {{
                flex: 1;
                overflow-y: auto;
                padding: 16px 0;
            }}

            .message {{
                padding: 2px 16px 2px 72px;
                margin-top: 17px;
                position: relative;
                word-wrap: break-word;
            }}

            .message:hover {{
                background-color: #2e3035;
            }}

            .message.grouped {{
                margin-top: 0;
                padding-top: 0.125rem;
                padding-bottom: 0.125rem;
            }}

            .message.grouped:hover .timestamp-hover {{
                display: block;
            }}

            .timestamp-hover {{
                display: none;
                position: absolute;
                left: 0;
                width: 56px;
                text-align: center;
                font-size: 10px;
                color: #949ba4;
                line-height: 22px;
            }}

            .message-header {{
                display: flex;
                align-items: center;
                margin-bottom: 2px;
                line-height: 22px;
            }}

            .avatar {{
                position: absolute;
                left: 16px;
                margin-top: 2px;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background-color: #5865f2;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 500;
                flex-shrink: 0;
                overflow: hidden;
                cursor: pointer;
            }}

            .avatar img {{
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}

            .username {{
                color: #f2f3f5;
                font-weight: 500;
                font-size: 15px;
                margin-right: 6px;
                cursor: pointer;
                line-height: 22px;
            }}

            .username:hover {{
                text-decoration: underline;
            }}

            .bot-tag {{
                background-color: #5865f2;
                color: #ffffff;
                font-size: 10px;
                font-weight: 500;
                padding: 2px 4px;
                border-radius: 3px;
                margin-right: 6px;
                text-transform: uppercase;
                vertical-align: top;
                line-height: 15px;
                margin-top: 3.5px;
                display: inline-block;
            }}

            .timestamp {{
                color: #949ba4;
                font-size: 12px;
                font-weight: 500;
                line-height: 22px;
            }}

            .message-content {{
                color: #dbdee1;
                line-height: 20px;
                font-size: 15px;
                word-wrap: break-word;
                white-space: pre-wrap;
            }}

            .message-content img.emoji {{
                width: 22px;
                height: 22px;
                vertical-align: bottom;
                object-fit: contain;
            }}

            .message-content a {{
                color: #00a8fc;
                text-decoration: none;
            }}

            .message-content a:hover {{
                text-decoration: underline;
            }}

            .message-content code {{
                background-color: #1e1f22;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
            }}

            .message-content pre {{
                background-color: #1e1f22;
                border: 1px solid #1e1f22;
                border-radius: 4px;
                padding: 8px;
                margin: 4px 0;
                overflow-x: auto;
            }}

            .message-content pre code {{
                background: none;
                padding: 0;
            }}

            .message-content strong {{
                font-weight: 700;
            }}

            .message-content em {{
                font-style: italic;
            }}

            .message-content blockquote {{
                border-left: 4px solid #4e5058;
                padding-left: 12px;
                margin: 4px 0;
            }}

            .attachment {{
                margin-top: 8px;
            }}

            .attachment img {{
                max-width: 400px;
                max-height: 300px;
                border-radius: 4px;
                cursor: pointer;
            }}

            .attachment video {{
                max-width: 400px;
                max-height: 300px;
                border-radius: 4px;
            }}

            .attachment a {{
                color: #00a8fc;
                text-decoration: none;
            }}

            .attachment a:hover {{
                text-decoration: underline;
            }}

            .attachment-file {{
                background-color: #2b2d31;
                border: 1px solid #1e1f22;
                border-radius: 4px;
                padding: 12px;
                display: inline-flex;
                align-items: center;
                max-width: 400px;
            }}

            .attachment-file-icon {{
                width: 32px;
                height: 40px;
                margin-right: 12px;
                background-color: #5865f2;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 11px;
                color: white;
            }}

            .attachment-file-info {{
                flex: 1;
                min-width: 0;
            }}

            .attachment-file-name {{
                color: #00a8fc;
                font-weight: 500;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}

            .attachment-file-size {{
                color: #949ba4;
                font-size: 12px;
                margin-top: 2px;
            }}

            .embed {{
                margin-top: 8px;
                background-color: #2b2d31;
                border-left: 4px solid #5865f2;
                border-radius: 4px;
                padding: 12px 16px;
                max-width: 520px;
            }}

            .embed-author {{
                display: flex;
                align-items: center;
                margin-bottom: 8px;
            }}

            .embed-author-icon {{
                width: 24px;
                height: 24px;
                border-radius: 50%;
                margin-right: 8px;
            }}

            .embed-author-name {{
                color: #f2f3f5;
                font-weight: 600;
                font-size: 14px;
            }}

            .embed-title {{
                color: #00a8fc;
                font-weight: 600;
                margin-bottom: 8px;
                font-size: 15px;
            }}

            .embed-title a {{
                color: #00a8fc;
                text-decoration: none;
            }}

            .embed-title a:hover {{
                text-decoration: underline;
            }}

            .embed-description {{
                color: #dbdee1;
                font-size: 14px;
                line-height: 18px;
                white-space: pre-wrap;
            }}

            .embed-fields {{
                margin-top: 8px;
            }}

            .embed-field {{
                margin-bottom: 8px;
            }}

            .embed-field-name {{
                color: #f2f3f5;
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 2px;
            }}

            .embed-field-value {{
                color: #dbdee1;
                font-size: 14px;
                line-height: 18px;
            }}

            .embed-footer {{
                display: flex;
                align-items: center;
                margin-top: 8px;
            }}

            .embed-footer-icon {{
                width: 20px;
                height: 20px;
                border-radius: 50%;
                margin-right: 8px;
            }}

            .embed-footer-text {{
                color: #949ba4;
                font-size: 12px;
            }}

            .embed-image {{
                margin-top: 12px;
                border-radius: 4px;
                max-width: 400px;
            }}

            .embed-thumbnail {{
                float: right;
                margin-left: 16px;
                margin-top: 8px;
                border-radius: 4px;
                max-width: 80px;
                max-height: 80px;
            }}

            .reactions {{
                margin-top: 8px;
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
            }}

            .reaction {{
                background-color: #2b2d31;
                border: 1px solid #1e1f22;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 6px;
                cursor: pointer;
                transition: background-color 0.17s ease, border-color 0.17s ease;
            }}

            .reaction:hover {{
                background-color: #35373c;
                border-color: #4e5058;
            }}

            .reaction img.emoji {{
                width: 16px;
                height: 16px;
            }}

            .reaction-count {{
                color: #949ba4;
                font-size: 13px;
                font-weight: 500;
            }}

            .sticker {{
                margin-top: 8px;
            }}

            .sticker img {{
                max-width: 160px;
                max-height: 160px;
            }}

            .footer {{
                background-color: #2b2d31;
                padding: 16px 20px;
                border-top: 1px solid #26282c;
                text-align: center;
                color: #949ba4;
                font-size: 12px;
            }}

            .divider {{
                height: 1px;
                margin: 24px 16px 8px 16px;
                background-color: #3f4147;
                position: relative;
            }}

            .divider-content {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                padding: 2px 8px;
                background-color: #313338;
                color: #949ba4;
                font-size: 12px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>
                    {'<img src="' + guild_icon + '" class="guild-icon" alt="">' if guild_icon else ''}
                    {target_name}{'<span class="thread-badge">🧵 THREAD</span>' if is_thread else ''}
                </h1>
                <div class="info">
                    {guild_name}{parent_info} • Exported on {export_time} • {len(messages)} messages
                </div>
            </div>

            <div class="messages">
    """

        # Add messages with proper grouping
        last_author = None
        last_timestamp = None
        current_date = None

        for message in messages:
            # Check if we need a date divider
            message_date = message.created_at.strftime("%B %d, %Y")
            if message_date != current_date:
                current_date = message_date
                html += f"""
                <div class="divider">
                    <span class="divider-content">{message_date}</span>
                </div>
    """

            # Get user avatar URL
            avatar_url = message.author.display_avatar.url

            # Get user initials for fallback
            initials = ''.join([word[0].upper() for word in message.author.display_name.split()[:2]])

            # Format timestamp
            timestamp = message.created_at.strftime("%I:%M %p").lstrip('0')
            full_timestamp = message.created_at.strftime("%B %d, %Y %I:%M %p")

            # Check if this message should be grouped with the previous one
            is_grouped = False
            if (last_author == message.author.id and
                    last_timestamp and
                    (message.created_at - last_timestamp).total_seconds() < 420):  # 7 minutes
                is_grouped = True

            last_author = message.author.id
            last_timestamp = message.created_at

            # Bot tag
            bot_tag = '<span class="bot-tag">BOT</span>' if message.author.bot else ''

            # Get user's role color
            role_color = self.get_member_color(message.author)
            username_style = f'color: {role_color};' if role_color else ''

            # Parse message content with Discord markdown and emotes
            content = self.parse_discord_content(message.content, message) if message.content else ''

            if is_grouped:
                # Grouped message (no avatar/username shown)
                html += f"""
                <div class="message grouped">
                    <span class="timestamp-hover">{timestamp}</span>
                    <div class="message-content">{content}</div>
    """
            else:
                # New message block with avatar and username
                html += f"""
                <div class="message">
                    <div class="avatar">
                        <img src="{avatar_url}" alt="{self.escape_html(message.author.display_name)}" onerror="this.style.display='none'; this.parentElement.textContent='{initials}';">
                    </div>
                    <div class="message-header">
                        <span class="username" style="{username_style}">{self.escape_html(message.author.display_name)}</span>
                        {bot_tag}
                        <span class="timestamp" title="{full_timestamp}">{timestamp}</span>
                    </div>
                    <div class="message-content">{content}</div>
    """

            # Add stickers
            if message.stickers:
                for sticker in message.stickers:
                    html += f"""
                    <div class="sticker">
                        <img src="{sticker.url}" alt="{self.escape_html(sticker.name)}">
                    </div>
    """

            # Add attachments
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        html += f"""
                    <div class="attachment">
                        <a href="{attachment.url}" target="_blank">
                            <img src="{attachment.url}" alt="{self.escape_html(attachment.filename)}" loading="lazy">
                        </a>
                    </div>
    """
                    elif attachment.content_type and attachment.content_type.startswith('video/'):
                        html += f"""
                    <div class="attachment">
                        <video controls>
                            <source src="{attachment.url}" type="{attachment.content_type}">
                        </video>
                    </div>
    """
                    else:
                        # Get file extension
                        ext = attachment.filename.split('.')[-1].upper() if '.' in attachment.filename else 'FILE'
                        size = self.format_file_size(attachment.size)
                        html += f"""
                    <div class="attachment">
                        <a href="{attachment.url}" target="_blank" style="text-decoration: none;">
                            <div class="attachment-file">
                                <div class="attachment-file-icon">{ext[:4]}</div>
                                <div class="attachment-file-info">
                                    <div class="attachment-file-name">{self.escape_html(attachment.filename)}</div>
                                    <div class="attachment-file-size">{size}</div>
                                </div>
                            </div>
                        </a>
                    </div>
    """

            # Add embeds
            if message.embeds:
                for embed in message.embeds:
                    border_color = f"#{embed.color.value:06x}" if embed.color else "#5865f2"

                    html += f"""
                    <div class="embed" style="border-left-color: {border_color};">
    """

                    # Embed author
                    if embed.author:
                        author_icon = f'<img src="{embed.author.icon_url}" class="embed-author-icon">' if embed.author.icon_url else ''
                        html += f"""
                        <div class="embed-author">
                            {author_icon}
                            <span class="embed-author-name">{self.escape_html(str(embed.author.name))}</span>
                        </div>
    """

                    # Embed title
                    if embed.title:
                        title_text = self.escape_html(str(embed.title))
                        if embed.url:
                            html += f'<div class="embed-title"><a href="{embed.url}" target="_blank">{title_text}</a></div>'
                        else:
                            html += f'<div class="embed-title">{title_text}</div>'

                    # Embed thumbnail
                    if embed.thumbnail:
                        html += f'<img src="{embed.thumbnail.url}" class="embed-thumbnail">'

                    # Embed description
                    if embed.description:
                        html += f'<div class="embed-description">{self.escape_html(str(embed.description))}</div>'

                    # Embed fields
                    if embed.fields:
                        html += '<div class="embed-fields">'
                        for field in embed.fields:
                            html += f"""
                            <div class="embed-field">
                                <div class="embed-field-name">{self.escape_html(str(field.name))}</div>
                                <div class="embed-field-value">{self.escape_html(str(field.value))}</div>
                            </div>
    """
                        html += '</div>'

                    # Embed image
                    if embed.image:
                        html += f'<img src="{embed.image.url}" class="embed-image">'

                    # Embed footer
                    if embed.footer:
                        footer_icon = f'<img src="{embed.footer.icon_url}" class="embed-footer-icon">' if embed.footer.icon_url else ''
                        footer_text = self.escape_html(str(embed.footer.text))
                        if embed.timestamp:
                            footer_text += f" • {embed.timestamp.strftime('%B %d, %Y at %I:%M %p')}"
                        html += f"""
                        <div class="embed-footer">
                            {footer_icon}
                            <span class="embed-footer-text">{footer_text}</span>
                        </div>
    """

                    html += """
                    </div>
    """

            # Add reactions
            if message.reactions:
                html += """
                    <div class="reactions">
    """
                for reaction in message.reactions:
                    # Check if it's a custom emoji
                    if hasattr(reaction.emoji, 'url'):
                        emoji_html = f'<img src="{reaction.emoji.url}" class="emoji" alt="{reaction.emoji.name}">'
                    else:
                        emoji_html = str(reaction.emoji)

                    html += f"""
                        <div class="reaction">
                            {emoji_html}
                            <span class="reaction-count">{reaction.count}</span>
                        </div>
    """
                html += """
                    </div>
    """

            html += """
                </div>
    """

        # Close HTML
        html += f"""
            </div>

            <div class="footer">
                Exported from Discord • {len(messages)} messages
            </div>
        </div>
    </body>
    </html>
    """

        return html

    def get_member_color(self, member):
        """Get the display color for a member based on their highest role"""
        try:
            if hasattr(member, 'color') and member.color and member.color.value != 0:
                return f"#{member.color.value:06x}"
        except:
            pass
        return None

    def parse_discord_content(self, text, message):
        """Parse Discord markdown and emotes in message content"""
        if not text:
            return ''

        import re

        # Parse Discord custom emotes BEFORE escaping HTML
        # Animated emotes
        text = re.sub(
            r'<a:(\w+):(\d+)>',
            r'<EMOJI_ANIMATED:\1:\2>',
            text
        )

        # Static custom emotes
        text = re.sub(
            r'<:(\w+):(\d+)>',
            r'<EMOJI_STATIC:\1:\2>',
            text
        )

        # Now escape HTML
        text = self.escape_html(text)

        # Replace emoji placeholders with actual HTML
        text = re.sub(
            r'&lt;EMOJI_ANIMATED:(\w+):(\d+)&gt;',
            r'<img src="https://cdn.discordapp.com/emojis/\2.gif" class="emoji" alt="\1" title="\1">',
            text
        )

        text = re.sub(
            r'&lt;EMOJI_STATIC:(\w+):(\d+)&gt;',
            r'<img src="https://cdn.discordapp.com/emojis/\2.png" class="emoji" alt="\1" title="\1">',
            text
        )

        # Parse mentions
        # User mentions
        text = re.sub(
            r'&lt;@!?(\d+)&gt;',
            lambda m: self.format_mention(m.group(1), message),
            text
        )

        # Channel mentions
        text = re.sub(
            r'&lt;#(\d+)&gt;',
            lambda m: f'<span style="color: #00a8fc;">#{self.get_channel_name(m.group(1), message)}</span>',
            text
        )

        # Role mentions
        text = re.sub(
            r'&lt;@&amp;(\d+)&gt;',
            lambda m: f'<span style="color: #00a8fc;">@{self.get_role_name(m.group(1), message)}</span>',
            text
        )

        # Parse Discord markdown
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # Italic (single * or _)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)

        # Underline
        text = re.sub(r'__(.+?)__', r'<u>\1</u>', text)

        # Strikethrough
        text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)

        # Spoiler
        text = re.sub(r'\|\|(.+?)\|\|',
                      r'<span style="background-color: #1e1f22; color: #1e1f22; border-radius: 3px; padding: 0 2px;" title="Spoiler">\1</span>',
                      text)

        # Code blocks with language
        text = re.sub(r'```(\w+)?\n(.+?)```', r'<pre><code>\2</code></pre>', text, flags=re.DOTALL)

        # Inline code
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

        # Block quotes
        text = re.sub(r'^&gt; (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)

        # Links (but not if already in an <a> tag)
        text = re.sub(
            r'(?<!href=")(https?://[^\s<]+)',
            r'<a href="\1" target="_blank">\1</a>',
            text
        )

        return text

    def format_mention(self, user_id, message):
        """Format a user mention"""
        try:
            member = message.guild.get_member(int(user_id))
            if member:
                return f'<span style="color: #00a8fc; background-color: rgba(88, 101, 242, 0.3); border-radius: 3px; padding: 0 2px;">@{self.escape_html(member.display_name)}</span>'
        except:
            pass
        return f'<span style="color: #00a8fc;">@Unknown</span>'

    def get_channel_name(self, channel_id, message):
        """Get channel name from ID"""
        try:
            channel = message.guild.get_channel(int(channel_id))
            if channel:
                return self.escape_html(channel.name)
        except:
            pass
        return 'unknown-channel'

    def get_role_name(self, role_id, message):
        """Get role name from ID"""
        try:
            role = message.guild.get_role(int(role_id))
            if role:
                return self.escape_html(role.name)
        except:
            pass
        return 'unknown-role'

    def format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def escape_html(self, text):
        """Escape HTML characters"""
        if not text:
            return ""
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))


def setup(bot):
    bot.add_cog(channelArchiver(bot))