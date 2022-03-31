import brownie
from brownie import Contract, interface, accounts
import pytest


def farmWithdraw(lp_farm, pid, strategy, amount):
    auth = accounts.at(strategy, True)
    if (lp_farm.address == '0x6e2ad6527901c9664f016466b8DA1357a004db0f'):
        lp_farm.withdraw(pid, amount, strategy, {'from': auth}) 
    else:
        lp_farm.withdraw(pid, amount, {'from': auth})


@pytest.fixture
def short(strategy):
    assert Contract(strategy.short())


def test_debt_rebalance(chain, accounts, token, deployed_vault, strategy, user, conf, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    ###################################################################
    # Test Debt Rebalance
    ###################################################################
    # Change the debt ratio to ~95% and rebalance
    sendAmount = round(strategy.balanceLp() * (1/.95 - 1) / lp_price)
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(9500, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(10000, rel=1e-3) == debtRatio
    assert pytest.approx(collatRatioBefore, rel=1e-2) == strategy.calcCollateral()

    # Change the debt ratio to ~40% and rebalance
    # sendAmount = round(strategy.balanceLpInShort() * (1/.4 - 1))
    sendAmount = round(strategy.balanceLp() * (1/.4 - 1) / lp_price)
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(4000, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(10000, rel=1e-3) == debtRatio 
    assert pytest.approx(collatRatioBefore, rel=1e-2) == strategy.calcCollateral()

    # Change the debt ratio to ~105% and rebalance - steal some lp from the strat
    sendAmount = round(strategy.balanceLp() * 0.05/1.05 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(10500, rel=2e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(10000, rel=2e-3) == debtRatio
    assert pytest.approx(collatRatioBefore, rel=1e-2) == strategy.calcCollateral()

    # Change the debt ratio to ~150% and rebalance - steal some lp from the strat
    # sendAmount = round(strategy.balanceLpInShort()*(1 - 1/1.50))
    sendAmount = round(strategy.balanceLp() * 0.5/1.50 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(15000, rel=2e-3) == debtRatio
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    assert pytest.approx(10000, rel=2e-3) == debtRatio
    assert pytest.approx(collatRatioBefore, rel=1e-2) == strategy.calcCollateral()


def test_debt_rebalance_partial(chain, accounts, token, deployed_vault, strategy, user, strategist, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    strategy.setDebtThresholds(9800, 10200, 5000)

    # Change the debt ratio to ~95% and rebalance
    sendAmount = round(strategy.balanceLpInShort()*(1/.95 - 1))
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(9500, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-3) == collatRatioBefore

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    collatRatio = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatio))
    assert pytest.approx(9750, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-3) == collatRatio

    # rebalance the whole way now
    strategy.setDebtThresholds(9800, 10200, 10000)
    strategy.rebalanceDebt()
    assert pytest.approx(10000, rel=1e-3) == strategy.calcDebtRatio()
    assert pytest.approx(6000, rel=1e-3) == strategy.calcCollateral()

    strategy.setDebtThresholds(9800, 10200, 5000)
    # Change the debt ratio to ~105% and rebalance - steal some lp from the strat
    sendAmount = round(strategy.balanceLp() * 0.05/1.05 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))
    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('CollatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(10500, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-3) == collatRatioBefore

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    collatRatio = strategy.calcCollateral()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    print('CollatRatio: {0}'.format(collatRatio))
    assert pytest.approx(10250, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-3) == collatRatio


def test_debt_rebalance_partial(chain, accounts, token, deployed_vault_large_deposit, strategy, user, strategist, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    strategy.setDebtThresholds(9800, 10200, 5000)

    # Change the debt ratio to ~95% and rebalance
    sendAmount = round(strategy.balanceLpInShort()*(1/.95 - 1))
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(9500, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-3) == collatRatioBefore

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    debtRatio = strategy.calcDebtRatio()
    collatRatio = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('collatRatio: {0}'.format(collatRatio))
    assert pytest.approx(9750, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-3) == collatRatio

    # rebalance the whole way now
    strategy.setDebtThresholds(9800, 10200, 10000)
    strategy.rebalanceDebt()
    assert pytest.approx(10000, rel=1e-3) == strategy.calcDebtRatio()
    assert pytest.approx(6000, rel=1e-3) == strategy.calcCollateral()

    strategy.setDebtThresholds(9800, 10200, 5000)
    # Change the debt ratio to ~105% and rebalance - steal some lp from the strat
    sendAmount = round(strategy.balanceLp() * 0.05/1.05 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))
    debtRatio = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatio))
    print('CollatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(10500, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-3) == collatRatioBefore

    # Rebalance Debt  and check it's back to the target
    strategy.rebalanceDebt()
    collatRatio = strategy.calcCollateral()
    debtRatio = strategy.calcDebtRatio()
    print('debtRatio:   {0}'.format(debtRatio))
    print('CollatRatio: {0}'.format(collatRatio))
    assert pytest.approx(10250, rel=1e-3) == debtRatio
    assert pytest.approx(6000, rel=1e-3) == collatRatio

    