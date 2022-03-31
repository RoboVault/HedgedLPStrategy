import brownie
from brownie import interface, Contract, accounts
import pytest
import time 

#this gets LP on other AMM so we can SIM a swap to offset debt Ratios 
def getWhaleAddress(strategy, routerAddress, Contract) : 
    spiritRouter = '0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52'
    spookyRouter = '0xF491e7B69E4244ad4002BC14e878a34207E38c29'
    if (routerAddress == spiritRouter):
        altRouter = spookyRouter
    else : altRouter = spiritRouter

    altRouterContract = Contract(altRouter)
    factory = Contract(altRouterContract.factory())
    token = strategy.want()
    short = strategy.short()

    whale = factory.getPair(token, short)

    return(whale)


def offSetDebtRatioLow(strategy, lp_token, token, Contract, swapPct, router):
    # use other AMM's LP to force some swaps 
    whale = getWhaleAddress(strategy, router.address, Contract)
    short = Contract(strategy.short())
    swapAmtMax = short.balanceOf(lp_token)*swapPct
    swapAmt = min(swapAmtMax, short.balanceOf(whale))
    print("Force Large Swap - to offset debt ratios")
    short.approve(router, 2**256-1, {"from": whale})
    router.swapExactTokensForTokens(swapAmt, 0, [short, token], whale, 2**256-1, {"from": whale})


def offSetDebtRatioHigh(strategy, lp_token, token, Contract, swapPct, router):
    # use other AMM's LP to force some swaps 
    whale = getWhaleAddress(strategy, router.address, Contract)
    short = Contract(strategy.short())
    swapAmtMax = token.balanceOf(lp_token)*swapPct
    swapAmt = min(swapAmtMax, token.balanceOf(whale))
    print("Force Large Swap - to offset debt ratios")
    token.approve(router, 2**256-1, {"from": whale})
    router.swapExactTokensForTokens(swapAmt, 0, [token, short], whale, 2**256-1, {"from": whale})


def steal(stealPercent, strategy, token, chain, gov, user):
    steal = round(strategy.estimatedTotalAssets() * stealPercent)
    strategy.liquidatePositionAuth(steal, {'from': gov})
    token.transfer(user, strategy.balanceOfWant(), {"from": accounts.at(strategy, True)})
    chain.sleep(1)
    chain.mine(1)


def strategySharePrice(strategy, vault):
    return strategy.estimatedTotalAssets() / vault.strategies(strategy)['totalDebt']


def test_operation(
    chain, accounts, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf, lp_token, router
):
    # Deposit to the vault
    user_balance_before = token.balanceOf(user)
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount
    
    # harvest
    chain.sleep(1)
    strategy.harvest()
    strat = strategy
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # make tiny swap to avoid issue where dif
    swapPct = 1 / 1000
    offSetDebtRatioHigh(strategy, lp_token, token, Contract, swapPct, router) 

    # check debt ratio
    debtRatio = strategy.calcDebtRatio()
    collatRatio = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatio))
    assert pytest.approx(10000, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-2) == collatRatio

    # withdrawal
    vault.withdraw(amount, user, 500, {'from' : user}) 
    assert (
        pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == user_balance_before
    )

def test_emergency_exit(
    chain, accounts, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # set emergency and exit
    strategy.setEmergencyExit()
    chain.sleep(1)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero
    assert pytest.approx(token.balanceOf(vault), rel=RELATIVE_APPROX) == amount


def test_profitable_harvest(
    chain, accounts, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    # Harvest 1: Send funds through the strategy
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount
    before_pps = vault.pricePerShare()

    # Use a whale of the harvest token to send
    harvest = interface.ERC20(conf['harvest_token'])
    harvestWhale = accounts.at(conf['harvest_token_whale'], True)
    sendAmount = round((vault.totalAssets() / conf['harvest_token_price']) * 0.05)
    print('Send amount: {0}'.format(sendAmount))
    print('harvestWhale balance: {0}'.format(harvest.balanceOf(harvestWhale)))
    harvest.transfer(strategy, sendAmount, {'from': harvestWhale})

    # Harvest 2: Realize profit
    chain.sleep(1)
    strategy.harvest()
    chain.sleep(3600 * 6)  # 6 hrs needed for profits to unlock
    chain.mine(1)
    profit = token.balanceOf(vault.address)  # Profits go to vault

    assert strategy.estimatedTotalAssets() + profit > amount
    assert vault.pricePerShare() > before_pps


def test_change_debt(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    half = int(amount / 2)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero


def test_change_debt_lossy(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Steal from the strategy
    steal = round(strategy.estimatedTotalAssets() * 0.01)
    strategy.liquidatePositionAuth(steal, {'from': gov})
    token.transfer(user, strategy.balanceOfWant(), {"from": accounts.at(strategy, True)})
    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=1e-2) == int(amount * 0.98 / 2) 

    vault.updateStrategyDebtRatio(strategy.address, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero

def test_sweep(gov, vault, strategy, token, user, amount, conf):
    # Strategy want token doesn't work
    token.transfer(strategy, amount, {"from": user})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})


def test_triggers(
    chain, gov, vault, strategy, token, amount, user, conf
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    chain.sleep(1)
    strategy.harvest()

    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)


def test_lossy_withdrawal(
    chain, gov, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Steal from the strategy
    stealPercent = 0.01
    steal(stealPercent, strategy, token, chain, gov, user)

    chain.mine(1)
    balBefore = token.balanceOf(user)
    vault.withdraw(amount, user, 150, {'from' : user}) 
    balAfter = token.balanceOf(user)
    assert pytest.approx(balAfter - balBefore, rel = 2e-3) == int(amount * .99)

def test_lossy_withdrawal_partial(
    chain, gov, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount


    # Steal from the strategy
    stealPercent = 0.005
    steal(stealPercent, strategy, token, chain, gov, user)

    balBefore = token.balanceOf(user)
    ssp_before = strategySharePrice(strategy, vault)

    #give RPC a little break to stop it spzzing out 
    time.sleep(5)

    half = int(amount / 2)
    vault.withdraw(half, user, 100, {'from' : user}) 
    balAfter = token.balanceOf(user)
    assert pytest.approx(balAfter - balBefore, rel = 2e-3) == (half * (1-stealPercent)) 

    # Check the strategy share price wasn't negatively effected
    ssp_after = strategySharePrice(strategy, vault)
    assert pytest.approx(ssp_before, rel = 2e-5) == ssp_after

def test_lossy_withdrawal_tiny(
    chain, gov, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})


    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount


    # Steal from the strategy
    stealPercent = 0.005
    steal(stealPercent, strategy, token, chain, gov, user)
    
    balBefore = token.balanceOf(user)
    ssp_before = strategySharePrice(strategy, vault)

    #give RPC a little break to stop it spzzing out 
    time.sleep(5)

    tiny = int(amount * 0.001)
    vault.withdraw(tiny, user, 100, {'from' : user}) 
    balAfter = token.balanceOf(user)
    assert pytest.approx(balAfter - balBefore, rel = 2e-3) == (tiny * (1-stealPercent)) 

    # Check the strategy share price wasn't negatively effected
    ssp_after = strategySharePrice(strategy, vault)
    assert pytest.approx(ssp_before, rel = 2e-5) == ssp_after

def test_lossy_withdrawal_99pc(
    chain, gov, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    # Steal from the strategy
    stealPercent = 0.005
    steal(stealPercent, strategy, token, chain, gov, user)

    balBefore = token.balanceOf(user)
    ssp_before = strategySharePrice(strategy, vault)

    #give RPC a little break to stop it spzzing out 
    time.sleep(5)

    tiny = int(amount * 0.99)
    vault.withdraw(tiny, user, 100, {'from' : user}) 
    balAfter = token.balanceOf(user)
    assert pytest.approx(balAfter - balBefore, rel = 2e-3) == (tiny * (1-stealPercent)) 

    # Check the strategy share price wasn't negatively effected
    ssp_after = strategySharePrice(strategy, vault)
    assert pytest.approx(ssp_before, rel = 2e-5) == ssp_after

def test_lossy_withdrawal_95pc(
    chain, gov, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount


    # Steal from the strategy
    stealPercent = 0.005
    steal(stealPercent, strategy, token, chain, gov, user)

    balBefore = token.balanceOf(user)
    ssp_before = strategySharePrice(strategy, vault)

    #give RPC a little break to stop it spzzing out 
    time.sleep(5)

    tiny = int(amount * 0.95)
    vault.withdraw(tiny, user, 100, {'from' : user}) 
    balAfter = token.balanceOf(user)
    assert pytest.approx(balAfter - balBefore, rel = 2e-3) == (tiny * (1-stealPercent)) 

    # Check the strategy share price wasn't negatively effected
    ssp_after = strategySharePrice(strategy, vault)
    assert pytest.approx(ssp_before, rel = 2e-5) == ssp_after

def test_reduce_debt_with_low_calcdebtratio(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf, lp_token, lp_whale, lp_farm, lp_price, pid, router
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    half = int(amount / 2)

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    swapPct = 0.015
    offSetDebtRatioLow(strategy, lp_token, token, Contract, swapPct, router)

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    #assert pytest.approx(9500, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=2e-3) == half

    vault.updateStrategyDebtRatio(strategy.address, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero



def test_reduce_debt_with_high_calcdebtratio(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf, lp_token, lp_whale, lp_farm, lp_price, pid, router
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    swapPct = 0.015
    offSetDebtRatioHigh(strategy, lp_token, token, Contract, swapPct, router)

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    #assert pytest.approx(10500, rel=2e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    chain.sleep(1)
    strategy.harvest()
    newAmount = strategy.estimatedTotalAssets() 

    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()

    assert pytest.approx(strategy.estimatedTotalAssets(), rel=2e-3) == int(newAmount / 2)

    vault.updateStrategyDebtRatio(strategy.address, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero


def test_increase_debt_with_low_calcdebtratio(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf, lp_token, lp_whale, lp_farm, lp_price, pid, router
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    half = int(amount / 2)

    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    # Change the debt ratio to ~95% and rebalance
    swapPct = 0.015
    offSetDebtRatioLow(strategy, lp_token, token, Contract, swapPct, router)


    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    #assert pytest.approx(9500, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=2e-3) == amount

    vault.updateStrategyDebtRatio(strategy.address, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero



def test_increase_debt_with_high_calcdebtratio(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf, lp_token, lp_whale, lp_farm, lp_price, pid, router
):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount / 2 

    swapPct = 0.015
    offSetDebtRatioHigh(strategy, lp_token, token, Contract, swapPct, router)

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    #assert pytest.approx(10500, rel=2e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    chain.sleep(1)
    strategy.harvest()
    newAmount = strategy.estimatedTotalAssets() 

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()

    loss = 0
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=2e-3) == int(amount - loss)

    
    vault.updateStrategyDebtRatio(strategy.address, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()

    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero
    
    # REMAINING AMOUNT BEING % of TVL 

    #remainingAmount = strategy.estimatedTotalAssets() / (amount - loss)
    #print('Remaining Amount:   {0}'.format(remainingAmount))

COMPTROLLER = '0x260E596DAbE3AFc463e75B6CC05d8c46aCAcFB09'
cTokenLend = '0x5AA53f03197E08C4851CAD8C92c7922DA5857E5d' # WFTM
cTokenBorrow = '0xE45Ac34E528907d0A0239ab5Db507688070B20bf' # USDC

def test_change_debt_with_price_offset_high(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf, MockPriceOracle
):
    price_offset = 1.03
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    # Edit the comp price oracle prices
    comp = interface.ComptrollerV5Storage(COMPTROLLER)
    old_oracle = Contract(comp.oracle())
    oracle = MockPriceOracle.deploy(old_oracle, {'from': accounts[0]})

    # Set the mock price oracle
    admin = accounts.at(comp.admin(), True)
    comp._setPriceOracle(oracle, {'from': admin})

    # Set the new one
    new_price = int(old_oracle.getUnderlyingPrice(cTokenLend) * price_offset)
    oracle.setUnderlyingPrice(cTokenLend, new_price)


    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    half = int(amount / 2)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero

    # return the price for other test
    comp._setPriceOracle(old_oracle, {'from': admin})


def test_change_debt_with_price_offset_low(
    chain, gov, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, conf, MockPriceOracle
):
    price_offset = 0.97
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})

    # Edit the comp price oracle prices
    comp = interface.ComptrollerV5Storage(COMPTROLLER)
    old_oracle = Contract(comp.oracle())
    oracle = MockPriceOracle.deploy(old_oracle, {'from': accounts[0]})

    # Set the mock price oracle
    admin = accounts.at(comp.admin(), True)
    comp._setPriceOracle(oracle, {'from': admin})

    # Set the new one
    new_price = int(old_oracle.getUnderlyingPrice(cTokenLend) * price_offset)
    oracle.setUnderlyingPrice(cTokenLend, new_price)


    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    half = int(amount / 2)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 100_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    vault.updateStrategyDebtRatio(strategy.address, 50_00, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == half

    vault.updateStrategyDebtRatio(strategy.address, 0, {"from": gov})
    chain.sleep(1)
    strategy.harvest()
    assert strategy.estimatedTotalAssets() < 10 ** (token.decimals() - 3) # near zero

    # return the price for other test
    comp._setPriceOracle(old_oracle, {'from': admin})


def farmWithdraw(lp_farm, pid, strategy, amount):
    auth = accounts.at(strategy, True)
    if (lp_farm.address == '0x6e2ad6527901c9664f016466b8DA1357a004db0f'):
        lp_farm.withdraw(pid, amount, strategy, {'from': auth}) 
    else:
        lp_farm.withdraw(pid, amount, {'from': auth})



