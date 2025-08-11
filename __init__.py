import asyncio
import sys
import os

from fastapi import APIRouter
from loguru import logger
from .db import db
from .views import taproot_assets_router
from .views_api import taproot_assets_api_router


sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lnbits'))

# Create router with prefix for the extension
taproot_assets_ext = APIRouter(prefix="/taproot_assets", tags=["taproot_assets"])

# Include the routers
taproot_assets_ext.include_router(taproot_assets_router)
taproot_assets_ext.include_router(taproot_assets_api_router)

# Define static files with the correct naming pattern
taproot_assets_static_files = [
    {
        "path": "/taproot_assets/static",
        "name": "taproot_assets_static",
        "mount_point": "/taproot_assets/static",  # Added mount_point
    }
]

# List for scheduled tasks
scheduled_tasks: list[asyncio.Task] = []

def taproot_assets_start():
    """Start any scheduled tasks."""
    # Add your scheduled tasks here if needed
    # For example:
    # from lnbits.tasks import create_permanent_unique_task
    # task = create_permanent_unique_task("taproot_assets_task", some_periodic_function)
    # scheduled_tasks.append(task)
    logger.info("Taproot Assets extension started")

def taproot_assets_stop():
    """Stop any scheduled tasks and close connections."""
    # Cancel scheduled tasks
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)
    
    # Close the parser client connection if it exists
    async def close_parser_client():
        try:
            from .tapd.taproot_parser import TaprootParserClient
            parser_client = TaprootParserClient.get_instance()
            if parser_client._initialized:
                logger.info("Closing TaprootParserClient connection")
                await parser_client.close()
                logger.info("TaprootParserClient connection closed")
        except Exception as ex:
            logger.warning(f"Error closing TaprootParserClient: {ex}")
    
    # Run the async close function in a new event loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(close_parser_client())
        else:
            asyncio.run(close_parser_client())
    except Exception as ex:
        logger.warning(f"Error in shutdown hook: {ex}")

# Make sure db is properly exposed
def taproot_assets_createdb():
    """Initialize the database schema."""
    from . import migrations
    return (db, [migrations])

# Items to export - fixed syntax
__all__ = [
    "db",
    "taproot_assets_ext",
    "taproot_assets_static_files",
    "taproot_assets_start",
    "taproot_assets_stop",
    "taproot_assets_createdb",
]
