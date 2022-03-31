// SPDX-License-Identifier: MIT
pragma solidity ^0.6.12;

interface inSpirit {
    function create_lock(uint256 _value, uint256 _unlock_time) external;

    function epoch() external view returns (uint256);

    function increase_amount(uint256 _value) external;

    function withdraw() external;

    function locked__end(address _addr) external view returns (uint256);

    function balanceOf(address _addr) external view returns (uint256);

    function locked(address _addr) external view returns (int128, uint256);
}

interface gauge {
    function vote(address[] calldata _tokenVote, uint256[] calldata _weights)
        external;
}

interface inSpiritRewards {
    function claim() external;
}
