// SPDX-License-Identifier: AGPL-3.0
pragma solidity >=0.6.0 <0.7.0;
pragma experimental ABIEncoderV2;

interface IPriceOracle {
    function getPrice() external view returns (uint256);
}
