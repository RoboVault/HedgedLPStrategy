// SPDX-License-Identifier: MIT
pragma solidity ^0.6.12;

interface SpookyFarm {
    function pendingBOO(uint256 _pid, address _user)
        external
        view
        returns (uint256);
}
