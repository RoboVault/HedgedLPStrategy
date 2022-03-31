
import pytest
from brownie import Contract, accounts

def farmWithdraw(lp_farm, pid, strategy, amount):
    auth = accounts.at(strategy, True)
    if (lp_farm.address == '0x6e2ad6527901c9664f016466b8DA1357a004db0f'):
        lp_farm.withdraw(pid, amount, strategy, {'from': auth}) 
    else:
        lp_farm.withdraw(pid, amount, {'from': auth})


def test_report_profit(
    chain,
    token,
    deployed_vault,
    strategy,
    interface,
    harvest_token,
    harvest_token_whale,
    conf
):
    # harvest to load deploy the funnds
    strategy.harvest()
    chain.sleep(1)
    
    # send some funds to force the profit
    harvest_token = interface.ERC20(conf['harvest_token'])

    # need a small amount to actually call insurance
    profit = int(strategy.estimatedTotalAssets() * 0.01)
    amount = round(profit / conf['harvest_token_price'])
    harvest_token.transfer(strategy, amount, {'from': harvest_token_whale})
    strategy.harvest()
    chain.sleep(3600 * 6)  # 6 hrs needed for profits to unlock
    chain.mine(1)

    # insurance payment should be 10% of profit
    assert pytest.approx(0.1, rel=1e-1) == token.balanceOf(strategy.insurance()) / profit 


def test_multiple_insurance_payouts(
    chain,
    token,
    deployed_vault,
    whale,
    strategy,
    interface,
    harvest_token,
    harvest_token_whale,
    conf,
    lp_price,
    lp_token,
    lp_farm,
    user,
    pid,
    StrategyInsurance
):
    vault = deployed_vault
    insurance = StrategyInsurance.at(strategy.insurance())

    # harvest to load deploy the funnds
    strategy.harvest()
    chain.sleep(1)

    # send some funds to insurance for the payment
    init_insurance_balance = int(vault.totalAssets() * 0.02)
    token.transfer(strategy.insurance(), init_insurance_balance, {'from': whale})

    # steal 0.2% from from the strat to force a loss
    stolen = strategy.estimatedTotalAssets() * 0.002
    sendAmount = round(stolen / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    # loop through payouts until the debt is erased
    loss = stolen
    print(loss)
    loops = 0
    payout = 0
    while (True):
        loops = loops + 1
        assert loops < 10
        print('***** {} *****'.format(loops))
        # The max debt payout is insurace.maximumCompenstionRate() bps of the total debt of the strategy
        max_payout = int(vault.strategies(strategy)[6] * insurance.maximumCompenstionRate() / 10000)
        target_payout = int(max(min(max_payout, loss - payout), 0))
        bal_before = token.balanceOf(insurance)

        # harvesting will trigger the payout
        print('Pre Balance:  {}'.format(strategy.estimatedTotalAssets()))
        print('Pre Debt:     {}'.format(int(vault.strategies(strategy)[6])))
        print('Pre Loss Sum: {}'.format(insurance.lossSum()))
        strategy.harvest()
        payout = int(bal_before - token.balanceOf(insurance))
        print('Target:   {}'.format(target_payout))
        print('Payout:   {}'.format(payout))
        print('Loss Sum: {}'.format(insurance.lossSum()))
        print('Loss:     {}'.format(loss))
        loss = int(loss - payout)

        if (insurance.lossSum() == 0):
            break

        chain.sleep(1)
    
    # there should now be no pending loss
    assert loops > 0
    assert insurance.lossSum() == 0
    assert init_insurance_balance - token.balanceOf(insurance) == pytest.approx(stolen, rel=1e-3)


def test_payout_then_profit(
    chain,
    token,
    deployed_vault,
    whale,
    strategy,
    interface,
    harvest_token,
    harvest_token_whale,
    conf,
    lp_price,
    lp_token,
    lp_farm,
    user,
    pid,
    StrategyInsurance
):
    vault = deployed_vault
    insurance = StrategyInsurance.at(strategy.insurance())

    # harvest to load deploy the funnds
    strategy.harvest()
    chain.sleep(1)
    initial_debt = vault.strategies(strategy)[6]

    # send some funds to insurance for the payment
    token.transfer(strategy.insurance(), int(vault.totalAssets() * 0.02), {'from': whale})

    # steal 0.2% from from the strat to force a loss
    stolen = strategy.estimatedTotalAssets() * 0.002
    sendAmount = int(stolen / lp_price)
    auth = accounts.at(strategy, True)
    farmWithdraw(lp_farm, pid, strategy, sendAmount)
    lp_token.transfer(user, sendAmount, {'from': auth})

    # *** 1 *** Test the insurance payout

    # The max debt payout is insurace.maximumCompenstionRate() bps of the total debt of the strategy
    max_payout = int(vault.strategies(strategy)[6] * insurance.maximumCompenstionRate() / 10000)
    target_payout = min(max_payout, stolen)
    bal_before = token.balanceOf(insurance)

    # harvesting will trigger the payout
    strategy.harvest()
    payout = bal_before - token.balanceOf(insurance)
    print('target: {}'.format(target_payout))
    print('payout: {}'.format(payout))

    assert pytest.approx(target_payout, rel=1e-1) == payout 
    chain.sleep(1)

    # *** 2 *** Now cover the losses with profit and check no payout is made
    token.transfer(strategy, stolen, {'from': whale})

    bal_before = token.balanceOf(insurance)
    strategy.harvest()
    payout = bal_before - token.balanceOf(insurance)

    assert payout == 0
    assert insurance.lossSum() == 0


def test_max_insurance_reached(
    chain,
):
    # todo - check once the insurance has been reached
    assert True

def test_small_payout(
    chain,
    token,
    deployed_vault,
    whale,
    strategy,
    interface,
    harvest_token,
    harvest_token_whale,
    conf,
    lp_price,
    lp_token,
    lp_farm,
    user,
    pid,
    StrategyInsurance
):
    # TODO - test that only takes a single payout to cover the loss.
    assert True

