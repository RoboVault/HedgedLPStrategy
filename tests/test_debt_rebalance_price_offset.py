from _pytest.fixtures import fixture
import brownie
from brownie import Contract, interface, accounts
import pytest

COMPTROLLER = '0x260E596DAbE3AFc463e75B6CC05d8c46aCAcFB09'
cTokenLend = '0x5AA53f03197E08C4851CAD8C92c7922DA5857E5d' # WFTM
cTokenBorrow = '0xE45Ac34E528907d0A0239ab5Db507688070B20bf' # USDC

def farmWithdraw(lp_farm, pid, strategy, amount):
    auth = accounts.at(strategy, True)
    if (lp_farm.address == '0x6e2ad6527901c9664f016466b8DA1357a004db0f'):
        lp_farm.withdraw(pid, amount, strategy, {'from': auth}) 
    else:
        lp_farm.withdraw(pid, amount, {'from': auth})

@pytest.fixture
def short(strategy):
    assert Contract(strategy.short())

def run_debt_rebalance_price_offset(price_offset, accounts, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle):
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
    # assert Contract(comp.oracle()).getUnderlyingPrice(cTokenLend) == new_price

    # Change the debt ratio to ~95% and rebalance
    sendAmount = round(strategy.balanceLp() * (1/.95 - 1) / lp_price)
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatio = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    # collat will be off due to changing the price after the first harvest
    print('collatRatio: {0}'.format(collatRatio))
    assert pytest.approx(9500, rel=1e-3) == debtRatio

    # The first one should fail because of the priceOffsetTest
    with brownie.reverts():
        strategy.rebalanceDebt()

    # Rebalance Debt  and check it's back to the target
    strategy.setSlippageConfig(9900, 500, False)
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(10000, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-2) == strategy.calcCollateral()

    # Change the debt ratio to ~40% and rebalance
    # sendAmount = round(strategy.balanceLpInShort() * (1/.4 - 1))
    sendAmount = round(strategy.balanceLp() * (1/.4 - 1) / lp_price)
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatio = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatio))
    assert pytest.approx(4000, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatio

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(10000, rel=1e-3) == debtRatio 
    assert pytest.approx(6000, rel=1e-2) == strategy.calcCollateral()

    # Change the debt ratio to ~105% and rebalance - steal some lp from the strat
    sendAmount = round(strategy.balanceLp() * 0.05/1.05 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatio = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatio))
    assert pytest.approx(10500, rel=2e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatio

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(10000, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-2) == strategy.calcCollateral()

    # Change the debt ratio to ~150% and rebalance - steal some lp from the strat
    # sendAmount = round(strategy.balanceLpInShort()*(1 - 1/1.50))
    sendAmount = round(strategy.balanceLp() * 0.5/1.50 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatio = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatio))
    assert pytest.approx(15000, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatio

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(10000, rel=2e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-2) == strategy.calcCollateral()

    # return the price for other test
    comp._setPriceOracle(old_oracle, {'from': admin})

def run_debt_rebalance_partial_price_offset(price_offset, accounts, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle):
    # strategy = test_strategy
    strategy.setDebtThresholds(9800, 10200, 5000)

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

    # Change the debt ratio to ~95% and rebalance
    sendAmount = round(strategy.balanceLpInShort()*(1/.95 - 1))
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(strategy.calcCollateral()))
    assert pytest.approx(9500, rel=1e-3) == debtRatio

    # The first one should fail because of the priceOffsetTest
    with brownie.reverts():
        strategy.rebalanceDebt()

    # Rebalance Debt  and check it's back to the target
    strategy.setSlippageConfig(9900, 500, False)
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(9750, rel=4e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-2) == strategy.calcCollateral()

    # assert False
    # rebalance the whole way now
    strategy.setDebtThresholds(9800, 10200, 10000)
    strategy.rebalanceDebt()
    assert pytest.approx(10000, rel=1e-3) == strategy.calcDebtRatio()

    strategy.setDebtThresholds(9800, 10200, 5000)
    # Change the debt ratio to ~105% and rebalance - steal some lp from the strat
    sendAmount = round(strategy.balanceLp() * 0.05/1.05 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))
    debtRatio = strategy.calcDebtRatio()
    collatRatio = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('CollatRatio: {0}'.format(collatRatio))
    assert pytest.approx(10500, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatio

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    collatRatio = strategy.calcCollateral()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    print('CollatRatio: {0}'.format(collatRatio))
    assert pytest.approx(10250, rel=4e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-2) == collatRatio

    # return the price for other test
    comp._setPriceOracle(old_oracle, {'from': admin})

def test_debt_rebalance_price_offset_high(accounts, deployed_vault, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle):
    run_debt_rebalance_price_offset(1.1, accounts, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle)

def test_debt_rebalance_price_offset_low(accounts, deployed_vault, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle):
    run_debt_rebalance_price_offset(0.9, accounts, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle)

def test_debt_rebalance_partial_price_offset_high(accounts, deployed_vault, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle):
    run_debt_rebalance_partial_price_offset(1.1, accounts, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle)

def test_debt_rebalance_partial_price_offset_low(accounts, deployed_vault, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle):
    run_debt_rebalance_partial_price_offset(0.9, accounts, strategy, user, lp_token, lp_whale, lp_farm, lp_price, pid, MockPriceOracle)