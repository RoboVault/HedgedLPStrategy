// SPDX-License-Identifier: MIT
pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

import "../CoreStrategy.sol";
import "../interfaces/lqdrfarm.sol";
import "../screampriceoracle.sol";

contract WBTCWFTMScreamLqdrSpooky is CoreStrategy {
    constructor(address _vault)
        public
        CoreStrategy(
            _vault,
            CoreStrategyConfig(
                0x04068DA6C83AFCFA0e13ba15A6696662335D5B75, // want
                0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83, // short
                0x2b4C76d0dc16BE1C31D4C1DC53bF9B45987Fc75c, // wantShortLP
                0x10b620b2dbAC4Faa7D7FFD71Da486f5D44cd86f9, // farmToken
                0x4Fe6f19031239F105F753D1DF8A0d24857D0cAA2, // farmTokenLp
                0x6e2ad6527901c9664f016466b8DA1357a004db0f, // farmMasterChef
                11, // farmPid
                0xE45Ac34E528907d0A0239ab5Db507688070B20bf, // cTokenLend
                0x5AA53f03197E08C4851CAD8C92c7922DA5857E5d, // cTokenBorrow
                0xe0654C8e6fd4D733349ac7E09f6f23DA256bF475, // compToken
                0x30872e4fc4edbFD7a352bFC2463eb4fAe9C09086, // compTokenLP
                0x260E596DAbE3AFc463e75B6CC05d8c46aCAcFB09, // comptroller
                0xF491e7B69E4244ad4002BC14e878a34207E38c29, // router
                1e4
            )
        )
    {
        // create a default oracle and set it
        oracle = new ScreamPriceOracle(
            address(comptroller),
            address(cTokenLend),
            address(cTokenBorrow)
        );
    }

    function _farmPendingRewards(uint256 _pid, address _user)
        internal
        view
        override
        returns (uint256)
    {
        return LqdrFarm(address(farm)).pendingLqdr(_pid, _user);
    }

    function _depoistLp() internal override {
        uint256 lpBalance = wantShortLP.balanceOf(address(this));
        LqdrFarm(address(farm)).deposit(farmPid, lpBalance, address(this));
    }

    function _withdrawFarm(uint256 _amount) internal override {
        LqdrFarm(address(farm)).withdraw(farmPid, _amount, address(this));
    }

    function claimHarvest() internal override {
        LqdrFarm(address(farm)).harvest(farmPid, address(this));
    }

    /**
     * Checks if collateral cap is reached or if deploying `_amount` will make it reach the cap
     * returns true if the cap is reached
     */
    function collateralCapReached(uint256 _amount)
        public
        view
        override
        returns (bool _capReached)
    {
        _capReached = false;
    }
}
