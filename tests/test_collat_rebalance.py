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


def test_collat_rebalance(chain, accounts, token, deployed_vault, strategy, user, conf, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    # set low collateral and rebalance
    target = 2000
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    debtBefore = strategy.calcDebtRatio()

    # rebalance
    strategy.rebalanceCollateral()
    debtAfter = strategy.calcDebtRatio()
    debtCollat = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtAfter))
    print('CollatRatio: {0}'.format(debtCollat))
    assert pytest.approx(10000, rel=1e-3) == debtAfter
    assert pytest.approx(target, rel=1e-2) == debtCollat

    # set high collateral and rebalance
    target = 6000
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    debtBefore = strategy.calcDebtRatio()

    # rebalance
    strategy.rebalanceCollateral()
    debtAfter = strategy.calcDebtRatio()
    debtCollat = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtAfter))
    print('CollatRatio: {0}'.format(debtCollat))
    assert pytest.approx(10000, rel=1e-3) == debtAfter
    assert pytest.approx(target, rel=1e-2) == debtCollat


def test_set_collat_thresholds(chain, accounts, token, deployed_vault, strategy, user, conf, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    # Vault share token doesn't work
    with brownie.reverts():
        strategy.setCollateralThresholds(5000, 4000, 6000, 7500)
    with brownie.reverts():
        strategy.setCollateralThresholds(7500, 8000, 8500, 7500)

    strategy.setCollateralThresholds(2000, 2500, 3000, 7500)


def test_large_collat_rebalance_with_low_debt(chain, accounts, token, deployed_vault, strategy, user, conf, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    # set low collateral and rebalance
    target = 2000
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    
    # Change the debt ratio to ~98%
    sendAmount = round(strategy.balanceLpInShort()*(1/.98 - 1))
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatioBefore = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatioBefore))
    print('collatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(9800, rel=1e-3) == debtRatioBefore
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    # now rebalance collat
    # We expect this to drag the debt ratio down, but only ~3%, this will differ
    strategy.rebalanceCollateral()
    debtAfter = strategy.calcDebtRatio()
    debtCollat = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtAfter))
    print('CollatRatio: {0}'.format(debtCollat))
    assert debtAfter > debtRatioBefore - 300 
    assert pytest.approx(target, rel=1e-2) == debtCollat

    # now rebalance debt for good measure
    # assert False
    target = 6000
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    debtRatioBefore = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatioBefore))
    print('collatRatio: {0}'.format(collatRatioBefore))

    # now rebalance collat
    # We expect this to drag the debt back up around where it was
    strategy.rebalanceCollateral()
    debtAfter = strategy.calcDebtRatio()
    debtCollat = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtAfter))
    print('CollatRatio: {0}'.format(debtCollat))
    assert pytest.approx(9800, rel=1e-3) == debtAfter
    assert pytest.approx(target, rel=1e-2) == debtCollat


def test_large_collat_rebalance_with_low_debt(chain, accounts, token, deployed_vault, strategy, user, conf, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    # set low collateral and rebalance
    target = 2000
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    
    # Change the debt ratio to ~102%
    sendAmount = round(strategy.balanceLp() * 0.02/1.02 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))
    debtRatioBefore = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatioBefore))
    print('CollatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(10200, rel=1e-3) == debtRatioBefore
    assert pytest.approx(6000, rel=2e-2) == collatRatioBefore

    # now rebalance collat
    # We expect this to drag the debt ratio down, but only ~3%, this will differ
    strategy.rebalanceCollateral()
    debtAfter = strategy.calcDebtRatio()
    debtCollat = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtAfter))
    print('CollatRatio: {0}'.format(debtCollat))
    assert debtAfter < debtRatioBefore + 300 
    assert pytest.approx(target, rel=1e-2) == debtCollat

    # now rebalance debt for good measure
    # assert False
    target = 6000
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    debtRatioBefore = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatioBefore))
    print('collatRatio: {0}'.format(collatRatioBefore))

    # now rebalance collat
    # We expect this to drag the debt back up around where it was
    strategy.rebalanceCollateral()
    debtAfter = strategy.calcDebtRatio()
    debtCollat = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtAfter))
    print('CollatRatio: {0}'.format(debtCollat))
    assert pytest.approx(10200, rel=1e-3) == debtAfter
    assert pytest.approx(target, rel=1e-2) == debtCollat


# this is a typical collat rebalance ~10% rebalance
def test_typical_rebalance_with_low_debt(chain, accounts, token, deployed_vault, strategy, user, conf, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    # set low collateral to 52%
    target = 5200
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    strategy.rebalanceCollateral()
    
    # Change the debt ratio to ~98%
    sendAmount = round(strategy.balanceLpInShort()*(1/.98 - 1))
    lp_token.transfer(strategy, sendAmount, {'from': lp_whale})
    print('Send amount: {0}'.format(sendAmount))
    print('debt Ratio:  {0}'.format(strategy.calcDebtRatio()))

    debtRatioBefore = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatioBefore))
    print('collatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(9800, rel=1e-3) == debtRatioBefore
    assert pytest.approx(target, rel=2e-2) == collatRatioBefore

    # now set collat back to 60%
    target = 6000
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    strategy.rebalanceCollateral()
    debtAfter = strategy.calcDebtRatio()
    debtCollat = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtAfter))
    print('CollatRatio: {0}'.format(debtCollat))
    assert pytest.approx(9800, rel=1e-3) == debtRatioBefore
    assert pytest.approx(target, rel=1e-2) == debtCollat


# this is a typical collat rebalance ~10% rebalance
def test_typical_collat_rebalance_with_high_debt(chain, accounts, token, deployed_vault, strategy, user, conf, gov, lp_token, lp_whale, lp_farm, lp_price, pid):
    # set low collateral and rebalance
    target = 6800
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    strategy.rebalanceCollateral()
    
    # Change the debt ratio to ~102%
    sendAmount = round(strategy.balanceLp() * 0.02/1.02 / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    print('Send amount: {0}'.format(sendAmount))
    debtRatioBefore = strategy.calcDebtRatio()
    collatRatioBefore = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtRatioBefore))
    print('CollatRatio: {0}'.format(collatRatioBefore))
    assert pytest.approx(10200, rel=1e-3) == debtRatioBefore
    assert pytest.approx(target, rel=2e-2) == collatRatioBefore

    # now set collat back to 60%
    target = 6000
    strategy.setCollateralThresholds(target-500, target, target+500, 7500)
    strategy.rebalanceCollateral()
    debtAfter = strategy.calcDebtRatio()
    debtCollat = strategy.calcCollateral()
    print('debtRatio:   {0}'.format(debtAfter))
    print('CollatRatio: {0}'.format(debtCollat))
    assert pytest.approx(10200, rel=1e-3) == debtRatioBefore
    assert pytest.approx(target, rel=1e-2) == debtCollat
