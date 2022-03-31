// SPDX-License-Identifier: AGPL-3.0

pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

import {
    SafeMath,
    Address
} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import {VaultAPI} from "@yearnvaults/contracts/BaseStrategy.sol";

/**
 * This interface is here for the keeper proxy to interact
 * with the strategy
 */
interface CoreStrategyAPI {
    function harvestTrigger(uint256 callCost) external view returns (bool);

    function harvest() external;

    function calcDebtRatio() external view returns (uint256);

    function calcCollateral() external view returns (uint256);

    function rebalanceDebt() external;

    function rebalanceCollateral() external;

    function strategist() external view returns (address);
}

/**
 * @title Robovault Keeper Proxy
 * @author robovault
 * @notice
 *  KeeperProxy implements a proxy for Robovaults CoreStrategy. The proxy provide
 *  More flexibility will roles, allowing for multiple addresses to be granted
 *  keeper permissions.
 *
 */
contract KeeperProxy {
    using Address for address;
    using SafeMath for uint256;

    CoreStrategyAPI public strategy;
    address public strategist;
    mapping(address => bool) public keepers;
    address[] public keepersList;

    constructor(address _strategy) public {
        setStrategyInternal(_strategy);
    }

    function _onlyStrategist() internal {
        require(msg.sender == address(strategist));
    }

    /**
     * @notice
     *  Only the strategist and approved keepers can call authorized
     *  functions
     */
    function _onlyKeepers() internal {
        require(
            keepers[msg.sender] == true || msg.sender == address(strategist),
            "!authorized"
        );
    }

    function setStrategy(address _strategy) external {
        _onlyStrategist();
        setStrategyInternal(_strategy);
    }

    function addKeeper(address _newKeeper) external {
        _onlyStrategist();
        keepers[_newKeeper] = true;
        keepersList.push(_newKeeper);
    }

    function removeKeeper(address _removeKeeper) external {
        _onlyStrategist();
        keepers[_removeKeeper] = false;
    }

    function harvestTrigger(uint256 _callCost) external view returns (bool) {
        return strategy.harvestTrigger(_callCost);
    }

    function harvest() external {
        _onlyKeepers();
        strategy.harvest();
    }

    function calcDebtRatio() external view returns (uint256) {
        return strategy.calcDebtRatio();
    }

    function rebalanceDebt() external {
        _onlyKeepers();
        strategy.rebalanceDebt();
    }

    function calcCollateral() external view returns (uint256) {
        return strategy.calcCollateral();
    }

    function rebalanceCollateral() external {
        _onlyKeepers();
        strategy.rebalanceCollateral();
    }

    function setStrategyInternal(address _strategy) internal {
        strategy = CoreStrategyAPI(_strategy);
        strategist = strategy.strategist();
    }
}
