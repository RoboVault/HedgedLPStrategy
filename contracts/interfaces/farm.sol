// SPDX-License-Identifier: MIT
pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

struct UserInfo {
    uint256 amount; // How many LP tokens the user has provided.
    uint256 rewardDebt; // Reward debt.
}

interface IFarmMasterChef {
    function deposit(uint256 _pid, uint256 _amount) external;

    function withdraw(uint256 _pid, uint256 _amount) external;

    function userInfo(uint256 _pid, address user)
        external
        view
        returns (UserInfo calldata);
}
