// SPDX-License-Identifier: MIT
pragma solidity ^0.6.12;

interface LqdrFarm {
    function pendingLqdr(uint256 _pid, address _user)
        external
        view
        returns (uint256);

    function harvest(uint256 _pid, address _to) external;

    function deposit(
        uint256 _pid,
        uint256 _wantAmt,
        address _sponsor
    ) external;

    function withdraw(
        uint256 _pid,
        uint256 _amount,
        address _to
    ) external;

    function userInfo(uint256 _pid, address user)
        external
        view
        returns (uint256, int256);
}
