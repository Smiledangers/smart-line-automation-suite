"""
Discord Bot API endpoints with Discord Gateway webhooks.
"""
import logging
import hashlib
import hmac
import time
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discord", tags=["discord"])


class DiscordMessageRequest(BaseModel):
    """Discord incoming message."""
    channel_id: str
    guild_id: Optional[str] = None
    author_id: str
    author_name: str
    content: str
    message_id: str
    timestamp: Optional[str] = None


class DiscordSendRequest(BaseModel):
    """Request to send Discord message."""
    channel_id: str
    content: str
    embeds: Optional[List[Dict]] = None


class DiscordInteractionRequest(BaseModel):
    """Discord interaction (button, select menu, etc.)."""
    type: int  # 1 = Ping, 2 = ApplicationCommand, 3 = MessageComponent
    data: Dict[Any, Any]
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    member: Optional[Dict] = None
    user: Optional[Dict] = None


@router.get("/webhook")
async def verify_webhook(
    interactions_endpoint_url: str = "https://your-app.com/api/v1/discord/interactions",
):
    """
    Discord webhook verification endpoint.
    Setup: Configure this URL in Discord Developer Portal.
    """
    # Discord will send a GET request to verify the endpoint
    return {"status": "ok"}


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_signature_ed25519: Optional[str] = Header(None),
    x_signature_timestamp: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive interactions from Discord (slash commands, buttons, etc.).
    
    Discord sends POST requests with signed payload for verification.
    """
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # Verify signature if bot token is configured
    from app.core.config import get_settings
    settings = get_settings()
    discord_bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', None)
    
    if discord_bot_token and x_signature_ed25519 and x_signature_timestamp:
        # Verify the request is actually from Discord
        # Note: Requires storing the public key from Discord Developer Portal
        # For now, we'll just log it
        logger.info(f"Discord interaction: signature={x_signature_ed25519[:20]}...")
    
    try:
        import json
        payload = json.loads(body_str)
        
        # Determine interaction type
        interaction_type = payload.get("type", 1)
        
        if interaction_type == 1:
            # Ping - respond with Pong
            return {"type": 1}
        
        elif interaction_type == 2:
            # Application Command (slash command)
            await _handle_slash_command(db, payload)
        
        elif interaction_type == 3:
            # Message Component (button, select menu)
            await _handle_component_interaction(db, payload)
        
        elif interaction_type == 4:
            # Modal Submit
            await _handle_modal_submit(db, payload)
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"Error processing Discord webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_slash_command(db: AsyncSession, payload: Dict[Any, Any]):
    """Handle slash command interactions."""
    data = payload.get("data", {})
    command_name = data.get("name", "")
    options = data.get("options", [])
    
    user = payload.get("user", {})
    member = payload.get("member", {})
    
    logger.info(f"Discord slash command: /{command_name} from {user.get('username')}")
    
    # TODO: Process command and respond
    # For now, just log it


async def _handle_component_interaction(db: AsyncSession, payload: Dict[Any, Any]):
    """Handle button/select menu interactions."""
    data = payload.get("data", {})
    component_type = data.get("component_type", 0)
    custom_id = data.get("custom_id", "")
    
    user = payload.get("user", {})
    
    logger.info(f"Discord component interaction: {custom_id} from {user.get('username')}")
    
    # TODO: Process button click and respond


async def _handle_modal_submit(db: AsyncSession, payload: Dict[Any, Any]):
    """Handle modal submit interactions."""
    data = payload.get("data", {})
    custom_id = data.get("custom_id", "")
    components = data.get("components", [])
    
    user = payload.get("user", {})
    
    logger.info(f"Discord modal submit: {custom_id} from {user.get('username')}")
    
    # TODO: Process modal data and respond


@router.post("/send")
async def send_message(
    message: DiscordSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to a Discord channel via Bot API.
    """
    from app.core.config import get_settings
    settings = get_settings()
    
    discord_bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', None)
    
    if not discord_bot_token:
        raise HTTPException(
            status_code=503,
            detail="Discord not configured. Set DISCORD_BOT_TOKEN in .env"
        )
    
    # Send via Discord REST API
    import httpx
    
    url = f"https://discord.com/api/v10/channels/{message.channel_id}/messages"
    headers = {
        "Authorization": f"Bot {discord_bot_token}",
        "Content-Type": "application/json",
    }
    
    payload = {"content": message.content}
    if message.embeds:
        payload["embeds"] = message.embeds
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code in (200, 201):
                result = response.json()
                return {
                    "status": "success",
                    "message_id": result.get("id"),
                }
            else:
                logger.error(f"Discord API error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Discord API error: {response.text}"
                )
    except Exception as e:
        logger.error(f"Discord send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send_dm")
async def send_direct_message(
    user_id: str,
    content: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a direct message to a Discord user.
    """
    from app.core.config import get_settings
    settings = get_settings()
    
    discord_bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', None)
    
    if not discord_bot_token:
        raise HTTPException(
            status_code=503,
            detail="Discord not configured. Set DISCORD_BOT_TOKEN in .env"
        )
    
    import httpx
    
    # First, create a DM channel
    create_dm_url = "https://discord.com/api/v10/users/@me/channels"
    headers = {
        "Authorization": f"Bot {discord_bot_token}",
        "Content-Type": "application/json",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Create DM
            dm_response = await client.post(
                create_dm_url,
                json={"recipient_id": user_id},
                headers=headers,
            )
            
            if dm_response.status_code not in (200, 201):
                logger.error(f"Discord create DM error: {dm_response.text}")
                raise HTTPException(
                    status_code=dm_response.status_code,
                    detail="Failed to create DM"
                )
            
            dm_data = dm_response.json()
            channel_id = dm_data.get("id")
            
            # Send message to DM channel
            send_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            send_response = await client.post(
                send_url,
                json={"content": content},
                headers=headers,
            )
            
            if send_response.status_code in (200, 201):
                return {
                    "status": "success",
                    "message_id": send_response.json().get("id"),
                }
            else:
                raise HTTPException(
                    status_code=send_response.status_code,
                    detail="Failed to send DM"
                )
                
    except Exception as e:
        logger.error(f"Discord DM error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels/{guild_id}")
async def list_guild_channels(
    guild_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    List all channels in a Discord guild.
    """
    from app.core.config import get_settings
    settings = get_settings()
    
    discord_bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', None)
    
    if not discord_bot_token:
        raise HTTPException(
            status_code=503,
            detail="Discord not configured"
        )
    
    import httpx
    
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    headers = {
        "Authorization": f"Bot {discord_bot_token}",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                return {"channels": response.json()}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch channels"
                )
    except Exception as e:
        logger.error(f"Discord list channels error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def discord_health():
    """Discord service health check."""
    from app.core.config import get_settings
    settings = get_settings()
    
    configured = bool(getattr(settings, 'DISCORD_BOT_TOKEN', None))
    
    return {
        "status": "healthy" if configured else "not_configured",
        "platform": "discord",
        "configured": configured,
    }