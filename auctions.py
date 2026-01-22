"""
Auction mechanisms for proposer selection.
"""

from typing import Dict, Tuple
from enum import Enum


class AuctionType(Enum):
    """Types of auctions supported."""
    SEALED_BID = "sealed_bid"
    VICKREY = "vickrey"
    ALL_PAY = "all_pay"


def sealed_bid_auction(bids: Dict[str, float]) -> Tuple[str, float]:
    """
    Sealed-bid (first-price) auction.
    
    Args:
        bids: Dict of agent_id -> bid amount
    
    Returns:
        (winner_id, amount_paid)
    """
    if not bids:
        raise ValueError("No bids received")
    
    winner_id = max(bids, key=bids.get)
    amount_paid = bids[winner_id]
    
    return winner_id, amount_paid


def vickrey_auction(bids: Dict[str, float]) -> Tuple[str, float]:
    """
    Vickrey (second-price sealed-bid) auction.
    Winner pays the second-highest bid.
    
    Args:
        bids: Dict of agent_id -> bid amount
    
    Returns:
        (winner_id, amount_paid)
    """
    if not bids:
        raise ValueError("No bids received")
    
    if len(bids) < 2:
        # Only one bidder: pays their own bid (or 0 if we're generous)
        winner_id = list(bids.keys())[0]
        return winner_id, 0.0
    
    sorted_bids = sorted(bids.items(), key=lambda x: x[1], reverse=True)
    winner_id, _ = sorted_bids[0]
    second_price = sorted_bids[1][1]
    
    return winner_id, second_price


def all_pay_auction(bids: Dict[str, float]) -> Tuple[str, float]:
    """
    All-pay auction.
    Everyone pays their bid; highest bid wins proposer role.
    
    Args:
        bids: Dict of agent_id -> bid amount
    
    Returns:
        (winner_id, amount_paid_by_winner) 
        Note: Others also pay, but we return winner's cost
    """
    if not bids:
        raise ValueError("No bids received")
    
    winner_id = max(bids, key=bids.get)
    amount_paid = bids[winner_id]
    
    return winner_id, amount_paid


def run_auction(
    bids: Dict[str, float],
    auction_type: str,
    budgets: Dict[str, float]
) -> Tuple[str, float]:
    """
    Run an auction given bids and type.
    
    Args:
        bids: Dict of agent_id -> bid amount
        auction_type: "sealed_bid", "vickrey", or "all_pay"
        budgets: Dict of agent_id -> remaining_budget (for validation)
    
    Returns:
        (proposer_id, amount_to_deduct_from_budget)
    
    Raises:
        ValueError: If bid exceeds budget
    """
    # Validate bids against budgets
    for agent_id, bid in bids.items():
        if bid > budgets.get(agent_id, 0):
            raise ValueError(
                f"Agent {agent_id} bid {bid} but only has budget {budgets[agent_id]}"
            )
    
    if auction_type == "sealed_bid" or auction_type == AuctionType.SEALED_BID.value:
        return sealed_bid_auction(bids)
    elif auction_type == "vickrey" or auction_type == AuctionType.VICKREY.value:
        return vickrey_auction(bids)
    elif auction_type == "all_pay" or auction_type == AuctionType.ALL_PAY.value:
        return all_pay_auction(bids)
    else:
        raise ValueError(f"Unknown auction type: {auction_type}")
