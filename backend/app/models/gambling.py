from pydantic import BaseModel

class SlotMachineRequest(BaseModel):
    bet_amount: int

class SlotMachineResponse(BaseModel):
    result: str
    payout: int
    net_change: int
    new_balance: int
    message: str
