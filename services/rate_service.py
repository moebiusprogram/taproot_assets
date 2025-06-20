"""Rate service for Taproot Assets."""
from typing import Optional
from loguru import logger
from datetime import datetime, timedelta, timezone

from ..tapd.taproot_factory import TaprootAssetsFactory
from ..tapd.taproot_invoices import TaprootInvoiceManager
from ....wallets.tapd_grpc_files.rfqrpc import rfq_pb2, rfq_pb2_grpc


class RateService:
    """Service for getting asset exchange rates."""
    
    # Simple in-memory cache
    _rate_cache = {}
    
    @classmethod
    async def get_current_rate(
        cls,
        asset_id: str,
        amount: int,
        wallet_info
    ) -> Optional[float]:
        """
        Get current exchange rate for an asset.
        Returns sats per asset unit.
        """
        # Check cache first (1 minute TTL)
        cache_key = f"{asset_id}:{amount}"
        cached = cls._rate_cache.get(cache_key)
        if cached:
            cached_at = cached.get("timestamp")
            if cached_at and datetime.now(timezone.utc) - cached_at < timedelta(seconds=60):
                return cached.get("rate")
        
        try:
            # Create wallet instance
            taproot_wallet = await TaprootAssetsFactory.create_wallet(
                user_id=wallet_info.wallet.user,
                wallet_id=wallet_info.wallet.id
            )
            
            # Get RFQ stub
            rfq_stub = rfq_pb2_grpc.RfqStub(taproot_wallet.node.channel)
            
            # Create buy order request to get rate
            buy_order_request = rfq_pb2.AddAssetBuyOrderRequest(
                asset_specifier=rfq_pb2.AssetSpecifier(asset_id=bytes.fromhex(asset_id)),
                asset_max_amt=amount,
                expiry=int((datetime.now(timezone.utc) + timedelta(minutes=1)).timestamp()),
                timeout_seconds=5
            )
            
            # Get quote
            buy_order_response = await rfq_stub.AddAssetBuyOrder(buy_order_request, timeout=5)
            
            if buy_order_response.accepted_quote:
                # Extract rate
                rate_info = buy_order_response.accepted_quote.ask_asset_rate
                total_millisats = float(rate_info.coefficient) / (10 ** rate_info.scale)
                rate_per_unit = (total_millisats / amount) / 1000  # Convert to sats
                
                # Cache the rate
                cls._rate_cache[cache_key] = {
                    "rate": rate_per_unit,
                    "timestamp": datetime.now(timezone.utc)
                }
                
                return rate_per_unit
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get rate for {asset_id}: {e}")
            return None