"""API endpoints for Taproot Assets extension."""
from http import HTTPStatus
from typing import Optional, Union, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from loguru import logger
from lnbits import bolt11

from lnbits.core.models import WalletTypeInfo
from lnbits.decorators import require_admin_key, require_invoice_key

from .models import (
    TaprootInvoiceRequest,
    TaprootPaymentRequest,
    InvoiceResponse,
    PaymentResponse,
    TaprootAsset,
    TaprootPayment,
    TaprootInvoice,
)
from .services.invoice_service import InvoiceService
from .services.payment_service import PaymentService
from .services.asset_service import AssetService
from .services.lnurl_service import LnurlService
from .services.rate_service import RateService
from .services.notification_service import NotificationService

taproot_assets_api_router = APIRouter(prefix="/api/v1/taproot", tags=["taproot"])


@taproot_assets_api_router.post(
    "/invoices",
    status_code=HTTPStatus.OK,
    response_model=InvoiceResponse,
    dependencies=[Depends(require_invoice_key)],
)
async def create_invoice(
    data: TaprootInvoiceRequest, wallet: WalletTypeInfo = Depends(require_invoice_key)
) -> InvoiceResponse:
    """Create an invoice for a Taproot Asset"""
    return await InvoiceService.create_invoice(
        data=data,
        user_id=wallet.wallet.user,
        wallet_id=wallet.wallet.id
    )


@taproot_assets_api_router.get(
    "/invoices",
    status_code=HTTPStatus.OK,
    response_model=List[TaprootInvoice],
    dependencies=[Depends(require_invoice_key)],
)
async def get_invoices(
    wallet: WalletTypeInfo = Depends(require_invoice_key)
) -> List[TaprootInvoice]:
    """Get all Taproot Asset invoices for a user"""
    return await InvoiceService.get_user_invoices(wallet.wallet.user)


@taproot_assets_api_router.get(
    "/invoices/{invoice_id}",
    status_code=HTTPStatus.OK,
    response_model=TaprootInvoice,
    dependencies=[Depends(require_invoice_key)],
)
async def get_invoice(
    invoice_id: str, wallet: WalletTypeInfo = Depends(require_invoice_key)
) -> TaprootInvoice:
    """Get a specific Taproot Asset invoice"""
    return await InvoiceService.get_invoice(invoice_id, wallet.wallet.user)


@taproot_assets_api_router.patch(
    "/invoices/{invoice_id}",
    status_code=HTTPStatus.OK,
    response_model=TaprootInvoice,
    dependencies=[Depends(require_admin_key)],
)
async def update_invoice_status(
    invoice_id: str,
    status: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> TaprootInvoice:
    """Update the status of a Taproot Asset invoice"""
    return await InvoiceService.update_invoice_status(
        invoice_id=invoice_id,
        status=status,
        user_id=wallet.wallet.user,
        wallet_id=wallet.wallet.id
    )


@taproot_assets_api_router.post(
    "/payments",
    status_code=HTTPStatus.OK,
    response_model=PaymentResponse,
    dependencies=[Depends(require_admin_key)],
)
async def pay_invoice(
    data: TaprootPaymentRequest, wallet: WalletTypeInfo = Depends(require_admin_key)
) -> PaymentResponse:
    """Pay a Taproot Asset invoice"""
    payment_response = await PaymentService.process_payment(data=data, wallet=wallet)
    
    if not payment_response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=payment_response.error or "Payment failed",
        )
    
    return payment_response


@taproot_assets_api_router.get(
    "/payments",
    status_code=HTTPStatus.OK,
    response_model=List[TaprootPayment],
    dependencies=[Depends(require_invoice_key)],
)
async def get_payments(
    wallet: WalletTypeInfo = Depends(require_invoice_key)
) -> List[TaprootPayment]:
    """Get all Taproot Asset payments for a user"""
    return await PaymentService.get_user_payments(wallet.wallet.user)


@taproot_assets_api_router.get(
    "/payments/{payment_id}",
    status_code=HTTPStatus.OK,
    response_model=TaprootPayment,
    dependencies=[Depends(require_invoice_key)],
)
async def get_payment(
    payment_id: str, wallet: WalletTypeInfo = Depends(require_invoice_key)
) -> TaprootPayment:
    """Get a specific Taproot Asset payment"""
    return await PaymentService.get_payment(payment_id, wallet.wallet.user)


@taproot_assets_api_router.get(
    "/assets",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(require_invoice_key)],
)
async def get_assets(wallet: WalletTypeInfo = Depends(require_invoice_key)) -> list:
    """Get all Taproot Assets for a user"""
    return await AssetService.list_assets(wallet)


@taproot_assets_api_router.get(
    "/asset-balances",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(require_invoice_key)],
)
async def get_asset_balances(wallet: WalletTypeInfo = Depends(require_invoice_key)) -> list:
    """Get all Taproot Asset balances for a user"""
    return await AssetService.get_asset_balances(wallet)


@taproot_assets_api_router.post(
    "/pay-lnurl",
    status_code=HTTPStatus.OK,
    response_model=PaymentResponse,
    dependencies=[Depends(require_admin_key)],
)
async def pay_lnurl(
    lnurl: str,
    amount_msat: int,
    wallet: WalletTypeInfo = Depends(require_admin_key),
    comment: Optional[str] = None,
    asset_id: Optional[str] = None,
) -> PaymentResponse:
    """
    Pay an LNURL with Taproot Assets.
    
    Args:
        lnurl: The LNURL string to pay
        amount_msat: Amount to pay in millisatoshis (will be ignored if paying with assets)
        comment: Optional comment
        asset_id: Optional asset ID to pay with
    """
    payment_response = await LnurlService.pay_lnurl(
        lnurl_string=lnurl,
        amount_msat=amount_msat,
        wallet_info=wallet,
        comment=comment,
        asset_id=asset_id
    )
    
    if not payment_response.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=payment_response.error or "LNURL payment failed",
        )
    
    return payment_response


@taproot_assets_api_router.get(
    "/check-lnurl",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(require_invoice_key)],
)
async def check_lnurl(
    lnurl: str,
    wallet: WalletTypeInfo = Depends(require_invoice_key)
) -> Dict[str, Any]:
    """
    Check if an LNURL supports Taproot Assets.
    
    Args:
        lnurl: The LNURL string to check
    """
    return await LnurlService.check_lnurl_asset_support(lnurl)


@taproot_assets_api_router.get(
    "/parse-invoice",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(require_invoice_key)],
)
async def parse_invoice(
    payment_request: str = Query(..., description="Payment request to parse"),
    wallet: WalletTypeInfo = Depends(require_invoice_key)
) -> Dict[str, Any]:
    """
    Parse a payment request to extract invoice details.
    
    Args:
        payment_request: The bolt11 payment request or LNURL to parse
    """
    try:
        # Check if this is an LNURL
        if payment_request.upper().startswith("LNURL"):
            # For LNURL, return a special response
            return {
                "is_lnurl": True,
                "payment_request": payment_request,
                "description": "LNURL Pay Request",
                "amount": 0,  # Amount will be determined by LNURL params
            }
        
        # Otherwise parse as bolt11
        parsed = await PaymentService.parse_invoice(payment_request)
        return {
            "is_lnurl": False,
            "payment_hash": parsed.payment_hash,
            "amount": parsed.amount,
            "asset_id": parsed.asset_id,
            "description": parsed.description,
            "destination": parsed.destination,
            "timestamp": parsed.timestamp,
            "expiry": parsed.expiry,
            "min_final_cltv_expiry": parsed.min_final_cltv_expiry,
            "route_hints": parsed.route_hints
        }
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Failed to parse invoice: {str(e)}"
        )


@taproot_assets_api_router.get(
    "/rates/{asset_id}",
    status_code=HTTPStatus.OK,
    dependencies=[Depends(require_admin_key)]
)
async def get_asset_rate(
    asset_id: str,
    amount: int = Query(1, description="Amount of assets to quote"),
    wallet: WalletTypeInfo = Depends(require_admin_key)
) -> dict:
    """
    Get current RFQ rate for an asset.
    
    Returns the rate in sats per asset unit.
    """
    try:
        rate = await RateService.get_current_rate(
            asset_id=asset_id,
            amount=amount,
            wallet_info=wallet
        )
        
        if rate is None:
            return {
                "error": "Could not fetch rate",
                "asset_id": asset_id,
                "rate_per_unit": None
            }
        
        return {
            "asset_id": asset_id,
            "amount": amount,
            "rate_per_unit": rate,
            "total_sats": int(amount * rate)
        }
        
    except Exception as e:
        logger.error(f"Error getting rate for {asset_id}: {e}")
        return {
            "error": str(e),
            "asset_id": asset_id,
            "rate_per_unit": None
        }