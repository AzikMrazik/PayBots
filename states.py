from aiogram.fsm.state import State, StatesGroup


class RefillStates(StatesGroup):
    waiting_amount = State()


class BuyEnergyStates(StatesGroup):
    choosing_wallet = State()
    entering_amount = State()
    confirming = State()


class BuyBandwidthStates(StatesGroup):
    choosing_wallet = State()
    entering_amount = State()
    confirming = State()


class AddWalletStates(StatesGroup):
    entering_address = State()
    entering_label = State()


class CalculateStates(StatesGroup):
    choosing_type = State()  # energy or bandwidth or transfer
    entering_params = State()
    showing_result = State()

