from .pow import ProofOfWork
from .pos import ProofOfStake

# Tạo các instance mặc định
pow_consensus = ProofOfWork(difficulty=4)
pos_consensus = ProofOfStake(min_stake=100)

# Cơ chế đồng thuận hiện tại (mặc định là PoW)
current_consensus = pow_consensus

def get_consensus():
    """Lấy cơ chế đồng thuận hiện tại"""
    return current_consensus

def set_consensus(consensus_type):
    """
    Thiết lập cơ chế đồng thuận
    
    Args:
        consensus_type: "pow" hoặc "pos"
    """
    global current_consensus
    
    if consensus_type.lower() == "pow":
        current_consensus = pow_consensus
    elif consensus_type.lower() == "pos":
        current_consensus = pos_consensus
    else:
        raise ValueError("Cơ chế đồng thuận không hợp lệ. Chỉ hỗ trợ 'pow' hoặc 'pos'")
    
    return current_consensus