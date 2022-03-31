// SPDX-License-Identifier: AGPL-3.0
// Feel free to change the license, but this is what we use

// Feel free to change this version of Solidity. We support >=0.6.0 <0.7.0;
pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;
import {IERC20} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

interface ILendingPool {
    function exchangeRate() external returns (uint256);

    function exchangeRateLast() external view returns (uint256);

    function collateral() external view returns (address);

    function mint(address minter) external returns (uint256);

    function redeem(address redeemer) external returns (uint256);
}

interface ILendingPoolToken is ILendingPool, IERC20 {}
